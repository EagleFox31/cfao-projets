"""Mode autonome : connexion par profil fictif, cookie signe, routes libres."""
from django.test import override_settings

from core.auth import locale


def test_connexion_ouvre_une_session_que_la_deconnexion_ferme(anonyme):
    r = anonyme.post("/pj-donnees/connexion", {"identifiant": "Formateur.Demo"}, format="json")
    assert r.status_code == 200
    assert r.json()["id"] == "f-demo" and r.json()["compte"] is True
    assert "identifiant" not in r.json()
    session = anonyme.get("/pj-donnees/session").json()
    assert session["id"] == "f-demo" and session["roles"] == ["trainer"]
    assert session["firstName"] == "Formateur"
    assert anonyme.post("/pj-donnees/deconnexion").json() == {"deconnecte": True}
    assert anonyme.get("/pj-donnees/session").status_code == 401


def test_un_identifiant_inconnu_est_refuse(anonyme):
    r = anonyme.post("/pj-donnees/connexion", {"identifiant": "inconnu"}, format="json")
    assert r.status_code == 401
    assert r.json() == {"erreur": "identifiant ou mot de passe incorrect"}


def test_se_souvenir_de_moi_donne_un_cookie_durable(anonyme):
    court = anonyme.post("/pj-donnees/connexion", {"identifiant": "formateur.demo"}, format="json")
    long_ = anonyme.post("/pj-donnees/connexion", {"identifiant": "formateur.demo", "seSouvenir": True},
                         format="json")
    assert "Max-Age" not in str(court.cookies[locale.COOKIE])
    assert "Max-Age=2592000" in str(long_.cookies[locale.COOKIE])
    assert "HttpOnly" in str(long_.cookies[locale.COOKIE])


def test_un_cookie_falsifie_n_ouvre_pas_de_session(anonyme):
    anonyme.cookies[locale.COOKIE] = "n:f-demo:faux"
    assert anonyme.get("/pj-donnees/session").status_code == 401
    anonyme.cookies[locale.COOKIE] = "p:" + locale.signer_session("f-demo", False)[0][2:]
    assert anonyme.get("/pj-donnees/session").status_code == 401


def test_le_rendu_demande_une_session(anonyme):
    assert anonyme.post("/pj-donnees/projets", {"nom": "x"}, format="json").status_code == 401
    assert anonyme.get("/apercu/sante").status_code == 200


@override_settings(DEPLOYMENT_MODE="integrated")
def test_en_mode_integre_la_connexion_renvoie_vers_la_plateforme(anonyme):
    r = anonyme.post("/pj-donnees/connexion", {"identifiant": "formateur.demo"}, format="json")
    assert r.status_code == 401 and r.json()["redirection"].startswith("/oauth2/start")
    assert anonyme.post("/pj-donnees/deconnexion").json()["redirection"].startswith("/oauth2/sign_out")
