"""Lecture GitHub : synchronisation, webhook signe, activite hebdomadaire."""
import hashlib
import hmac
import json

from django.test import override_settings

from projets import github
from projets.models import Commit, Depot, Membre, Personne

P = "/pj-donnees/projets"


def _brut(sha, login, date, additions=10, deletions=2, message="feat: x"):
    return {"sha": sha, "html_url": f"https://github.com/cfao/portail/commit/{sha}",
            "commit": {"message": message, "author": {"name": login.title(), "email": f"{login}@example.test",
                                                      "date": date}},
            "author": {"login": login},
            "stats": {"additions": additions, "deletions": deletions},
            "files": [{"filename": "a.py", "additions": additions, "deletions": deletions}]}


def _depot(client, projet, faux_github, toutes_branches=False):
    r = client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/portail", "toutes_branches": toutes_branches},
                      format="json")
    assert r.status_code == 201, r.content
    faux_github.reponses["/repos/cfao/portail/commits"] = [
        _brut("a" * 40, "formateur-demo", "2026-11-03T10:00:00Z"),
        _brut("b" * 40, "formateur-demo", "2026-11-04T09:00:00Z", 5, 5),
        _brut("c" * 40, "inconnu", "2026-11-05T08:00:00Z", 1, 0),
    ]
    faux_github.reponses["/repos/cfao/portail"] = {"default_branch": "main"}
    faux_github.reponses["/repos/cfao/portail/issues"] = []
    return r.json()


def test_synchroniser_lit_les_commits_et_les_rattache(client, pdp, projet, faux_github):
    depot = _depot(client, projet, faux_github)
    assert client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/portail"}, format="json").status_code == 200
    client().patch("/pj-donnees/personnes/moi", {"github_login": "formateur-demo"}, format="json")
    r = client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    assert r.status_code == 200, r.content
    assert r.json()["nouveaux"] == 3 and r.json()["depot"]["branche_par_defaut"] == "main"
    assert pdp.demandes[-1]["action"] == "sync"
    # Les parametres GitHub : branche par defaut et fenetre « since ».
    chemins = [c for c, _ in faux_github.appels]
    assert "/repos/cfao/portail/commits" in chemins
    params = [p for c, p in faux_github.appels if c.endswith("/commits")][0]
    assert params["sha"] == "main" and "since" in params
    # Rejouer : zero nouveau commit, aucun doublon.
    assert client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser").json()["nouveaux"] == 0
    assert Commit.objects.count() == 3
    moi = Personne.objects.get(sujet="f-demo")
    assert Commit.objects.filter(personne=moi).count() == 2


def test_une_erreur_github_est_notee_sans_casser(client, projet, faux_github):
    depot = _depot(client, projet, faux_github)
    faux_github.reponses["/repos/cfao/portail"] = lambda: (_ for _ in ()).throw(github.ErreurGitHub("GitHub 404"))
    r = client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    assert r.status_code == 502 and r.json()["erreur"] == "GitHub 404"
    assert Depot.objects.get(id=depot["id"]).derniere_erreur == "GitHub 404"
    assert client("s-demo").get("/pj-donnees/erreurs").json()["erreurs"][0]["origine"] == "synchro"


def test_un_jeton_sans_droit_sur_les_issues_n_empeche_pas_les_commits(client, projet, faux_github):
    depot = _depot(client, projet, faux_github)
    faux_github.reponses["/repos/cfao/portail/issues"] = lambda: (_ for _ in ()).throw(
        github.ErreurGitHub("GitHub refuse l'accès à cfao/portail (403)"))
    r = client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    assert r.status_code == 200, r.content
    assert r.json()["nouveaux"] == 3 and Commit.objects.count() == 3
    enregistre = Depot.objects.get(id=depot["id"])
    assert enregistre.derniere_synchro is not None
    assert enregistre.derniere_erreur.startswith("Issues non importees")


def test_l_activite_hebdo_par_personne_et_les_diffs(client, projet, faux_github):
    depot = _depot(client, projet, faux_github)
    client().patch("/pj-donnees/personnes/moi", {"github_login": "formateur-demo"}, format="json")
    client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    r = client().get(f"{P}/{projet['id']}/activite?semaine=2026-W45")
    assert r.status_code == 200, r.content
    corps = r.json()
    assert corps["total"] == {"commits": 3, "additions": 16, "deletions": 7, "fichiers": 3}
    moi = next(p for p in corps["personnes"] if p["personne"])
    assert moi["login"] == "formateur-demo" and moi["commits"] == 2 and moi["additions"] == 15
    assert moi["depots"][0]["diff"] == ("https://github.com/cfao/portail/compare/" + "a" * 40 + "%5E..." + "b" * 40)
    assert sum(moi["jours"]) == 2 and len(corps["jours"]) == 7
    inconnu = next(p for p in corps["personnes"] if not p["personne"])
    assert inconnu["login"] == "inconnu" and inconnu["commits"] == 1
    assert client().get(f"{P}/{projet['id']}/activite?semaine=2026-W44").json()["total"]["commits"] == 0
    assert client().get(f"{P}/{projet['id']}/activite?semaine=nimporte").status_code == 400
    tableau = client().get("/pj-donnees/activite/semaine?semaine=2026-W45").json()
    assert tableau["total"]["commits"] == 3 and tableau["projets"][0]["id"] == projet["id"]


def _signature(secret, corps):
    return "sha256=" + hmac.new(secret.encode(), corps, hashlib.sha256).hexdigest()


@override_settings(GITHUB_WEBHOOK_SECRET="tres-secret")
def test_le_webhook_push_exige_une_signature_valide(client, anonyme, projet, faux_github):
    _depot(client, projet, faux_github)
    charge = json.dumps({"ref": "refs/heads/main", "repository": {"full_name": "cfao/portail", "default_branch": "main"},
                         "commits": [{"id": "d" * 40}]}).encode()
    faux_github.reponses["/repos/cfao/portail/commits/" + "d" * 40] = _brut("d" * 40, "formateur-demo",
                                                                           "2026-11-05T12:00:00Z")
    from rest_framework.test import APIClient
    hook = APIClient()
    r = hook.post("/pj-donnees/webhooks/github", charge, content_type="application/json",
                  HTTP_X_GITHUB_EVENT="push", HTTP_X_HUB_SIGNATURE_256="sha256=faux")
    assert r.status_code == 403 and Commit.objects.count() == 0
    r = hook.post("/pj-donnees/webhooks/github", charge, content_type="application/json",
                  HTTP_X_GITHUB_EVENT="push", HTTP_X_HUB_SIGNATURE_256=_signature("tres-secret", charge))
    assert r.status_code == 200 and r.json()["nouveaux"] == 1
    # Rejoue (GitHub relivre parfois) : rien de plus.
    r = hook.post("/pj-donnees/webhooks/github", charge, content_type="application/json",
                  HTTP_X_GITHUB_EVENT="push", HTTP_X_HUB_SIGNATURE_256=_signature("tres-secret", charge))
    assert r.json()["nouveaux"] == 0 and Commit.objects.count() == 1


@override_settings(GITHUB_WEBHOOK_SECRET="")
def test_sans_secret_configure_le_webhook_est_ferme(db):
    from rest_framework.test import APIClient
    r = APIClient().post("/pj-donnees/webhooks/github", b"{}", content_type="application/json",
                         HTTP_X_GITHUB_EVENT="push")
    assert r.status_code == 403


def test_un_depot_mal_forme_est_refuse(client, projet):
    for depot in ("cfao", "cfao/portail/x", "cfao/por tail", "../x"):
        assert client().post(f"{P}/{projet['id']}/depots", {"depot": depot}, format="json").status_code == 400
    r = client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/portail", "jeton_variable": "pas valide"},
                      format="json")
    assert r.status_code == 400


def test_un_sous_dossier_filtre_les_commits_et_leurs_stats(client, projet, faux_github):
    """Monorepo : seuls les fichiers sous `chemin` comptent ; un commit hors dossier est ignore."""
    r = client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/mono", "chemin": "/apps/mail/"}, format="json")
    assert r.status_code == 201, r.content
    depot = r.json()
    assert depot["chemin"] == "apps/mail" and depot["libelle"] == "cfao/mono/apps/mail"
    # Le meme depot sans filtre reste un autre suivi du meme projet.
    assert client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/mono"}, format="json").status_code == 201
    dedans = _brut("a" * 40, "formateur-demo", "2026-11-03T10:00:00Z", 30, 3)
    dedans["files"] = [{"filename": "apps/mail/x.py", "additions": 20, "deletions": 1},
                       {"filename": "apps/web/y.py", "additions": 10, "deletions": 2}]
    dehors = _brut("b" * 40, "formateur-demo", "2026-11-04T09:00:00Z")
    dehors["files"] = [{"filename": "apps/web/z.py", "additions": 10, "deletions": 2}]
    faux_github.reponses["/repos/cfao/mono/commits"] = [dedans, dehors]
    faux_github.reponses["/repos/cfao/mono"] = {"default_branch": "main"}
    r = client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    assert r.status_code == 200, r.content
    assert r.json()["nouveaux"] == 1
    params = [p for c, p in faux_github.appels if c.endswith("/commits")][0]
    assert params["path"] == "apps/mail"
    commit = Commit.objects.get(sha="a" * 40)
    assert (commit.additions, commit.deletions, commit.fichiers) == (20, 1, 1)
    for chemin in ("a/../b", "a b"):
        assert client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/mono", "chemin": chemin},
                             format="json").status_code == 400


@override_settings(SYNCHRO_RECOUVREMENT_HEURES=72)
def test_la_synchro_relit_assez_loin_pour_un_commit_pousse_en_retard(client, projet, faux_github):
    """Un commit date de plusieurs heures avant la derniere passe, pousse ensuite, reste rattrape."""
    from datetime import timedelta
    from django.utils import timezone
    depot = _depot(client, projet, faux_github)
    url = f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser"
    client().post(url)
    derniere = timezone.now()
    Depot.objects.filter(pk=depot["id"]).update(derniere_synchro=derniere)
    faux_github.appels.clear()
    client().post(url)
    since = [p for c, p in faux_github.appels if c.endswith("/commits")][0]["since"]
    attendu = (derniere - timedelta(hours=72)).astimezone(github.tz.utc).strftime("%Y-%m-%dT%H:%M")
    assert since.startswith(attendu)


def _issue(numero, titre, login="formateur-demo", pr=False, labels=()):
    brut = {"number": numero, "title": titre, "body": "Detail", "html_url": f"https://github.com/cfao/portail/issues/{numero}",
            "user": {"login": login}, "labels": [{"name": n} for n in labels]}
    if pr:
        brut["pull_request"] = {"url": "x"}
    return brut


def test_les_issues_ouvertes_deviennent_des_propositions_une_seule_fois(client, projet, faux_github):
    from projets.models import Proposition
    depot = _depot(client, projet, faux_github)
    client().patch("/pj-donnees/personnes/moi", {"github_login": "formateur-demo"}, format="json")
    faux_github.reponses["/repos/cfao/portail/issues"] = [_issue(1, "Ajouter l'export"), _issue(2, "PR", pr=True),
                                                         _issue(3, "Bug", login="inconnu")]
    url = f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser"
    client().post(url)
    client().post(url)   # rejouer : aucun doublon
    props = {p.reference: p for p in Proposition.objects.all()}
    assert set(props) == {"cfao/portail#1", "cfao/portail#3"}
    p1 = props["cfao/portail#1"]
    assert p1.source == "github" and p1.type == "ajouter_tache" and p1.contenu["titre"] == "Ajouter l'export"
    assert p1.auteur.sujet == "f-demo" and props["cfao/portail#3"].auteur is None
    # Visible et decidable par le chef ; l'acceptation cree la tache.
    r = client().get("/pj-donnees/propositions").json()
    assert {p["reference"] for p in r["a_decider"]} == {"cfao/portail#1", "cfao/portail#3"}
    sans_auteur = props["cfao/portail#3"]
    r = client().post(f"/pj-donnees/propositions/{sans_auteur.id}/decision", {"decision": "acceptee"}, format="json")
    assert r.status_code == 200, r.content
    assert r.json()["source"] == "github" and r.json()["auteur"] is None
    assert projet_taches(projet) == ["Bug"]


def projet_taches(projet):
    from projets.models import Tache
    return list(Tache.objects.filter(projet_id=projet["id"]).values_list("titre", flat=True))


def test_un_sous_dossier_de_monorepo_n_importe_que_son_etiquette(client, projet, faux_github):
    from projets.models import Proposition
    r = client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/portail", "chemin": "apps/mail"}, format="json")
    depot = r.json()
    assert depot["importe_issues"] is False
    faux_github.reponses["/repos/cfao/portail"] = {"default_branch": "main"}
    faux_github.reponses["/repos/cfao/portail/commits"] = []
    faux_github.reponses["/repos/cfao/portail/issues"] = [_issue(7, "Mail")]
    client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    assert Proposition.objects.count() == 0
    # Etiquette posee (meme depot reposte : mise a jour, pas de doublon) : filtre transmis a GitHub.
    r = client().post(f"{P}/{projet['id']}/depots", {"depot": "cfao/portail", "chemin": "apps/mail",
                                                    "issues_etiquette": "mail"}, format="json")
    assert r.status_code == 200 and r.json()["importe_issues"] is True
    client().post(f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser")
    params = [p for c, p in faux_github.appels if c.endswith("/issues")][-1]
    assert params["labels"] == "mail" and Proposition.objects.count() == 1

def test_les_auteurs_reconnus_deviennent_contributeurs_une_seule_fois(client, projet, faux_github):
    depot = _depot(client, projet, faux_github)
    dev = Personne.objects.create(sujet="dev-demo", nom="Dev", github_login="formateur-demo")
    chef = Membre.objects.get(projet_id=projet["id"]).personne
    url = f"{P}/{projet['id']}/depots/{depot['id']}/synchroniser"
    assert client().post(url).status_code == 200
    roles = dict(Membre.objects.filter(projet_id=projet["id"]).values_list("personne__sujet", "role_membre"))
    assert roles == {chef.sujet: "chef", "dev-demo": "contributeur"}   # « inconnu » n'est pas ajoute
    # Un role fixe a la main survit aux synchros suivantes, sans doublon.
    Membre.objects.filter(projet_id=projet["id"], personne=dev).update(role_membre="observateur")
    assert client().post(url).status_code == 200
    assert Membre.objects.get(projet_id=projet["id"], personne=dev).role_membre == "observateur"
    assert Membre.objects.filter(projet_id=projet["id"]).count() == 2
