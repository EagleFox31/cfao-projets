"""Personnes declarees avant connexion et adresses secondaires d'auteur de commit."""
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from projets import github
from projets.models import Commit, Depot, Personne, Projet


def _declarer(*args):
    sortie = StringIO()
    call_command("declarer_personne", *args, stdout=sortie)
    return sortie.getvalue()


@pytest.fixture
def depot(db):
    createur = Personne.objects.create(sujet="createur")
    projet = Projet.objects.create(nom="P", cree_par=createur)
    return Depot.objects.create(projet=projet, proprietaire="o", nom="r")


def _commit(depot, sha, login="", email=""):
    return Commit.objects.create(depot=depot, sha=sha, auteur_login=login, auteur_email=email,
                                 date=timezone.now())


def test_declarer_rattache_commits_par_login_et_adresses_secondaires(depot):
    _commit(depot, "a1", login="Dev1")
    _commit(depot, "a2", email="Dev@Bureau.local")
    _commit(depot, "a3", email="autre@x.io")
    sortie = _declarer("--email", "Dev1@Exemple.com", "--prenom", "Dev", "--github", "@dev1",
                       "--adresse-git", "dev@bureau.local")
    personne = Personne.objects.get(email="dev1@exemple.com")
    assert personne.sujet == "pre:dev1@exemple.com"
    assert personne.github_login == "dev1" and personne.adresses_git == ["dev@bureau.local"]
    assert set(Commit.objects.filter(personne=personne).values_list("sha", flat=True)) == {"a1", "a2"}
    assert "creee" in sortie and "2 commit(s)" in sortie


def test_declarer_est_idempotent(depot):
    args = ("--email", "d@x.io", "--github", "d", "--adresse-git", "b@y.io")
    _declarer(*args)
    assert "inchangee" in _declarer(*args)
    assert Personne.objects.filter(email="d@x.io").count() == 1


def test_premiere_connexion_adopte_la_fiche_pre_enregistree(depot, client):
    _commit(depot, "c1", login="dev1")
    _declarer("--email", "formateur.demo@example.invalid", "--github", "dev1")
    r = client("f-demo").get("/pj-donnees/personnes/moi")
    assert r.status_code == 200
    personne = Personne.objects.get(sujet="f-demo")
    assert personne.github_login == "dev1"
    assert not Personne.objects.filter(sujet__startswith="pre:").exists()
    assert Commit.objects.get(sha="c1").personne == personne


def test_nouveau_commit_attribue_par_adresse_secondaire(db):
    personne = Personne.objects.create(sujet="s", adresses_git=["poste@bureau.local"])
    assert github._personne_pour("", "Poste@Bureau.local ") == personne


def test_modifier_moi_accepte_et_valide_les_adresses(client):
    c = client("f-demo")
    r = c.patch("/pj-donnees/personnes/moi", {"adresses_git": ["A@b.io", "a@b.io", " "]}, format="json")
    assert r.status_code == 200 and r.json()["adresses_git"] == ["a@b.io"]
    r = c.patch("/pj-donnees/personnes/moi", {"adresses_git": ["pas-une-adresse"]}, format="json")
    assert r.status_code == 400 and "adresse invalide" in r.json()["erreur"]
