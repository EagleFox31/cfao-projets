"""Projets, membres, taches : chaque route passe par le PEP avec les bons attributs."""
import pytest

from projets.models import Courrier, Membre, Personne, Projet

P = "/pj-donnees/projets"


def test_creer_un_projet_en_fait_le_chef_et_passe_par_le_pdp(client, pdp):
    r = client().post(P, {"nom": "Portail", "date_debut": "2026-01-05"}, format="json")
    assert r.status_code == 201, r.content
    corps = r.json()
    assert corps["mon_role"] == "chef" and corps["nb_membres"] == 1 and corps["avancement"] == 0
    assert corps["cree_par"]["sujet"] == "f-demo" and corps["scope_node"] == "CMR"
    demande = pdp.demandes[-1]
    assert (demande["kind"], demande["action"]) == ("projet", "create")
    assert demande["attr"]["ownerId"] == "f-demo" and demande["attr"]["scopeNode"] == "CMR"


def test_un_projet_invalide_est_refuse_avant_le_pdp(client, pdp):
    r = client().post(P, {"nom": "", "date_debut": "2026-02-01", "date_fin": "2026-01-01"}, format="json")
    assert r.status_code == 400 and "erreur" in r.json()
    assert pdp.demandes == []


def test_le_pdp_peut_refuser_la_creation(client, pdp):
    pdp.refuser("projet:create")
    assert client("a-demo").post(P, {"nom": "Interdit"}, format="json").status_code == 403
    assert Projet.objects.count() == 0


def test_la_liste_ne_montre_que_les_projets_lisibles(client, pdp, projet):
    client("c-demo").post(P, {"nom": "Meme perimetre, pas membre"}, format="json")
    pdp.reponse = lambda principal, resource, action: (
        action != "read" or resource["attr"]["roleMembre"] == "chef")
    noms = [p["nom"] for p in client().get(P).json()["projets"]]
    assert noms == ["Portail apprenants"]
    # Le role dans le projet est transmis au PDP.
    lectures = [d for d in pdp.demandes if d["action"] == "read"]
    assert {d["attr"]["roleMembre"] for d in lectures} == {"chef", ""}


def test_le_detail_expose_les_droits_calcules(client, pdp, projet):
    pdp.refuser("projet:delete", "proposition:decide")
    corps = client().get(f"{P}/{projet['id']}").json()
    assert corps["droits"] == {"update": True, "delete": False, "manage_members": True, "sync": True,
                               "creer_tache": True, "proposer": True, "decider": False}
    assert corps["membres"][0]["personne"]["sujet"] == "f-demo"


def test_modifier_et_supprimer_un_projet(client, pdp, projet):
    r = client().patch(f"{P}/{projet['id']}", {"statut": "en_pause", "avancement_manuel": 40}, format="json")
    assert r.status_code == 200 and r.json()["statut"] == "en_pause" and r.json()["avancement"] == 40
    assert pdp.demandes[-1]["action"] == "update"
    assert client().patch(f"{P}/{projet['id']}", {"statut": "inconnu"}, format="json").status_code == 400
    assert client().delete(f"{P}/{projet['id']}").status_code == 204
    assert client().get(f"{P}/{projet['id']}").status_code == 404
    assert client().delete(f"{P}/{projet['id']}").status_code == 204   # idempotent


def test_ajouter_un_membre_envoie_un_courrier_une_seule_fois(client, pdp, projet):
    url = f"{P}/{projet['id']}/membres"
    client("a-demo").get("/pj-donnees/personnes/moi")   # la personne existe des sa premiere visite
    r = client().post(url, {"personne": "a-demo", "role_membre": "contributeur"}, format="json")
    assert r.status_code == 201 and r.json()["role_membre"] == "contributeur"
    assert pdp.demandes[-1]["action"] == "manage_members"
    # Rejouer la meme demande ne duplique ni le membre ni le courrier.
    assert client().post(url, {"personne": "a-demo", "role_membre": "contributeur"}, format="json").status_code == 200
    assert Membre.objects.filter(projet_id=projet["id"]).count() == 2
    assert Courrier.objects.filter(kind="projets.membre_ajoute").count() == 1
    # Le dernier chef ne peut pas etre retrograde ni retire.
    chef = Membre.objects.get(projet_id=projet["id"], role_membre="chef")
    assert client().patch(f"{url}/{chef.id}", {"role_membre": "observateur"}, format="json").status_code == 400
    assert client().delete(f"{url}/{chef.id}").status_code == 400
    assert client().delete(f"{url}/{r.json()['id']}").status_code == 204


def test_un_membre_inconnu_est_refuse(client, projet):
    r = client().post(f"{P}/{projet['id']}/membres", {"personne": "nul", "role_membre": "chef"}, format="json")
    assert r.status_code == 400


def test_les_taches_portent_l_avancement_et_l_assigne(client, pdp, projet):
    Personne.objects.create(sujet="a-demo", prenom="Apprenant", nom="Demo", email="a@example.test")
    url = f"{P}/{projet['id']}/taches"
    t1 = client().post(url, {"titre": "Maquette", "poids": 3, "assigne": "a-demo"}, format="json")
    assert t1.status_code == 201 and t1.json()["assigne"]["sujet"] == "a-demo"
    assert pdp.demandes[-1]["kind"] == "tache" and pdp.demandes[-1]["attr"]["assigneId"] == "a-demo"
    assert Courrier.objects.filter(kind="projets.tache_assignee").count() == 1
    t2 = client().post(url, {"titre": "Recette", "poids": 1}, format="json")
    assert t2.status_code == 201
    r = client().patch(f"{url}/{t1.json()['id']}", {"statut": "fait"}, format="json")
    assert r.status_code == 200 and r.json()["statut"] == "fait"
    assert client().get(f"{P}/{projet['id']}").json()["avancement"] == 75
    assert client().post(url, {"titre": "x", "poids": 0}, format="json").status_code == 400
    assert client().delete(f"{url}/{t2.json()['id']}").status_code == 204
    assert pdp.demandes[-1]["action"] == "delete"


def test_personnes_moi_et_github_login(client, pdp):
    moi = client().get("/pj-donnees/personnes/moi").json()
    assert moi["sujet"] == "f-demo" and moi["prenom"] == "Formateur"
    r = client().patch("/pj-donnees/personnes/moi", {"github_login": "@Formateur-Demo"}, format="json")
    assert r.status_code == 200 and r.json()["github_login"] == "Formateur-Demo"
    assert pdp.demandes[-1] ["kind"] == "personne" and pdp.demandes[-1]["attr"]["ownerId"] == "f-demo"
    assert client().patch("/pj-donnees/personnes/moi", {"github_login": "pas valide!"}, format="json").status_code == 400
    liste = client().get("/pj-donnees/personnes?q=form").json()["personnes"]
    assert [p["sujet"] for p in liste] == ["f-demo"]


def test_le_referentiel_et_la_sante(client, anonyme):
    assert anonyme.get("/apercu/sante").json()["pret"] is True
    ref = client().get("/pj-donnees/referentiel").json()
    assert {s["code"] for s in ref["statuts_projet"]} >= {"en_cours", "termine"}
    assert ref["peut_creer_projet"] is True and ref["semaine_courante"].count("-W") == 1


@pytest.mark.parametrize("route", ["/pj-donnees/projets", "/pj-donnees/propositions", "/pj-donnees/personnes"])
def test_sans_session_rien_ne_passe(anonyme, route):
    assert anonyme.get(route).status_code == 401
