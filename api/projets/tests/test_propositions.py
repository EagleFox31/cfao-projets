"""Propositions de modification : un autre profil propose, le chef tranche."""
from projets.models import Courrier, Membre, Personne, Proposition, Tache

P = "/pj-donnees/projets"


def _membre_demandeur(client, projet):
    Personne.objects.get_or_create(sujet="a-demo", defaults={"prenom": "Apprenant", "nom": "Demo",
                                                             "email": "a@example.test"})
    r = client().post(f"{P}/{projet['id']}/membres", {"personne": "a-demo", "role_membre": "demandeur"},
                      format="json")
    assert r.status_code == 201


def test_soumettre_puis_accepter_une_proposition_de_tache(client, pdp, projet):
    _membre_demandeur(client, projet)
    url = f"{P}/{projet['id']}/propositions"
    corps = {"type": "ajouter_tache", "contenu": {"titre": "Former les KI", "poids": 2, "inconnu": "ignore"},
             "motif": "Le besoin remonte du terrain"}
    r = client("a-demo").post(url, corps, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["contenu"] == {"titre": "Former les KI", "poids": 2}
    demande = pdp.demandes[-1]
    assert (demande["kind"], demande["action"]) == ("proposition", "create")
    assert demande["attr"]["roleMembre"] == "demandeur" and demande["attr"]["auteurId"] == "a-demo"
    # Idempotent : la meme proposition en attente n'est pas dupliquee.
    assert client("a-demo").post(url, corps, format="json").status_code == 200
    assert Proposition.objects.count() == 1
    assert Courrier.objects.filter(kind="projets.proposition_soumise").count() == 1

    # Le demandeur ne voit que les siennes, le chef les voit toutes dans « a_decider ».
    pdp.reponse = lambda principal, resource, action: not (
        action == "decide" and resource["attr"]["roleMembre"] != "chef")
    assert len(client("a-demo").get(url).json()["propositions"]) == 1
    boite = client().get("/pj-donnees/propositions").json()
    assert len(boite["a_decider"]) == 1 and boite["miennes"] == []
    assert client("a-demo").get("/pj-donnees/propositions").json()["a_decider"] == []

    pid = r.json()["id"]
    assert client("a-demo").post(f"/pj-donnees/propositions/{pid}/decision", {"decision": "acceptee"},
                                 format="json").status_code == 403
    r = client().post(f"/pj-donnees/propositions/{pid}/decision", {"decision": "acceptee", "commentaire": "ok"},
                      format="json")
    assert r.status_code == 200 and r.json()["statut"] == "acceptee" and r.json()["decideur"]["sujet"] == "f-demo"
    assert Tache.objects.filter(projet_id=projet["id"], titre="Former les KI", poids=2).exists()
    assert Courrier.objects.filter(kind="projets.proposition_decidee").count() == 1
    # Rejouer la meme decision : no-op ; une decision contraire : conflit.
    assert client().post(f"/pj-donnees/propositions/{pid}/decision", {"decision": "acceptee"},
                         format="json").status_code == 200
    assert client().post(f"/pj-donnees/propositions/{pid}/decision", {"decision": "refusee"},
                         format="json").status_code == 409
    assert Tache.objects.count() == 1


def test_refuser_n_applique_rien(client, projet):
    _membre_demandeur(client, projet)
    r = client("a-demo").post(f"{P}/{projet['id']}/propositions",
                              {"type": "modifier_projet", "contenu": {"statut": "termine"}}, format="json")
    pid = r.json()["id"]
    r = client().post(f"/pj-donnees/propositions/{pid}/decision", {"decision": "refusee", "commentaire": "trop tot"},
                      format="json")
    assert r.status_code == 200 and r.json()["statut"] == "refusee"
    assert client().get(f"{P}/{projet['id']}").json()["statut"] == "en_cours"


def test_une_proposition_sur_une_tache_disparue_est_inapplicable(client, projet):
    _membre_demandeur(client, projet)
    t = client().post(f"{P}/{projet['id']}/taches", {"titre": "A revoir"}, format="json").json()
    r = client("a-demo").post(f"{P}/{projet['id']}/propositions",
                              {"type": "modifier_tache", "cible_id": t["id"], "contenu": {"statut": "bloque"}},
                              format="json")
    assert r.status_code == 201, r.content
    client().delete(f"{P}/{projet['id']}/taches/{t['id']}")
    r = client().post(f"/pj-donnees/propositions/{r.json()['id']}/decision", {"decision": "acceptee"}, format="json")
    assert r.status_code == 409 and "inapplicable" in r.json()["erreur"]
    assert Proposition.objects.get().statut == "soumise"


def test_ajouter_un_membre_par_proposition(client, projet):
    _membre_demandeur(client, projet)
    r = client("a-demo").post(f"{P}/{projet['id']}/propositions",
                              {"type": "ajouter_membre", "contenu": {"personne": "ki-demo", "role_membre": "chef"}},
                              format="json")
    assert r.status_code == 400   # ki-demo n'existe pas encore comme personne
    client("ki-demo").get("/pj-donnees/personnes/moi")
    r = client("a-demo").post(f"{P}/{projet['id']}/propositions",
                              {"type": "ajouter_membre", "contenu": {"personne": "ki-demo", "role_membre": "contributeur"}},
                              format="json")
    assert r.status_code == 201, r.content
    client().post(f"/pj-donnees/propositions/{r.json()['id']}/decision", {"decision": "acceptee"}, format="json")
    assert Membre.objects.get(projet_id=projet["id"], personne__sujet="ki-demo").role_membre == "contributeur"


def test_contenu_invalide_refuse(client, projet):
    _membre_demandeur(client, projet)
    for corps in ({"type": "inconnu", "contenu": {}}, {"type": "ajouter_tache", "contenu": {}},
                  {"type": "modifier_tache", "contenu": {"statut": "fait"}},
                  {"type": "modifier_projet", "contenu": {"avancement_manuel": 150}}):
        assert client("a-demo").post(f"{P}/{projet['id']}/propositions", corps, format="json").status_code == 400
