"""Controle d'origine des requetes qui ecrivent (cookie de session, CSRF)."""
from rest_framework.test import APIClient

from core.auth import locale

ETRANGERE = "http://evil.example"
CONNEXION = "/pj-donnees/connexion"
CORPS = {"identifiant": "formateur.demo"}


def _navigateur(**defauts):
    return APIClient(**defauts)


def test_une_origine_autorisee_passe(db):
    r = _navigateur(HTTP_ORIGIN="http://localhost:8094").post(CONNEXION, CORPS, format="json")
    assert r.status_code == 200


def test_l_origine_du_serveur_de_dev_passe(db):
    r = _navigateur(HTTP_ORIGIN="http://localhost:5178").post(CONNEXION, CORPS, format="json")
    assert r.status_code == 200


def test_le_portail_garde_sa_connexion_par_compte(db):
    # Le portail (5173 en dev, 5174 servi) appelle /pj-donnees par son proxy :
    # l'Origin reste la sienne.
    for origine in ("http://localhost:5173", "http://127.0.0.1:5174"):
        c = _navigateur(HTTP_ORIGIN=origine)
        assert c.post(CONNEXION, CORPS, format="json").status_code == 200
        assert c.post("/pj-donnees/deconnexion").status_code != 403


def test_une_origine_etrangere_est_refusee_meme_sans_cookie(db):
    r = _navigateur(HTTP_ORIGIN=ETRANGERE).post(CONNEXION, CORPS, format="json")
    assert r.status_code == 403
    assert locale.COOKIE not in r.cookies


def test_une_origine_etrangere_ne_deconnecte_pas_ni_n_ecrit(db):
    c = _navigateur(HTTP_ORIGIN="http://localhost:8094")
    assert c.post(CONNEXION, CORPS, format="json").status_code == 200
    c.credentials(HTTP_ORIGIN=ETRANGERE)
    assert c.post("/pj-donnees/deconnexion").status_code == 403
    assert c.put("/pj-donnees/projets/abc", {}, format="json").status_code == 403
    assert c.delete("/pj-donnees/projets/abc").status_code == 403
    c.credentials(HTTP_ORIGIN="http://localhost:8094")
    assert c.get("/pj-donnees/session").status_code == 200


def test_une_photo_text_plain_d_une_origine_etrangere_est_refusee(db):
    c = _navigateur(HTTP_ORIGIN="http://localhost:8094")
    c.post(CONNEXION, CORPS, format="json")
    c.credentials(HTTP_ORIGIN=ETRANGERE)
    r = c.generic("POST", "/apercu/photo", b"\xff\xd8photo", content_type="text/plain")
    assert r.status_code == 403


def test_le_referer_remplace_l_origine_absente(db):
    c = _navigateur(HTTP_REFERER="http://localhost:8094/formateur/x")
    assert c.post(CONNEXION, CORPS, format="json").status_code == 200
    c = _navigateur(HTTP_REFERER="http://evil.example/page")
    assert c.post(CONNEXION, CORPS, format="json").status_code == 403


def test_sans_origine_ni_referer_le_cookie_est_refuse(db):
    c = _navigateur()
    c.cookies[locale.COOKIE] = locale.signer_session("f-demo", False)[0]
    assert c.post("/pj-donnees/deconnexion").status_code == 403


def test_un_navigateur_sans_origine_est_refuse(db):
    assert _navigateur(HTTP_SEC_FETCH_SITE="cross-site").post(CONNEXION, CORPS, format="json").status_code == 403


def test_sans_cookie_l_en_tete_x_user_id_passe_sans_origine(client, pdp):
    """Pas de credential envoyee d'office : curl et tests ne sont pas concernes."""
    assert client("f-demo").get("/pj-donnees/projets").status_code == 200
    assert client("f-demo").put("/pj-donnees/projets/abc", {}, format="json").status_code != 403


def test_le_cookie_porte_le_nom_configure_et_l_option_secure(db, settings):
    assert locale.COOKIE == settings.COOKIE_SESSION
    r = _navigateur(HTTP_ORIGIN="http://localhost:8094").post(CONNEXION, CORPS, format="json")
    assert not r.cookies[locale.COOKIE]["secure"]
    settings.COOKIE_SECURE = True
    r = _navigateur(HTTP_ORIGIN="http://localhost:8094").post(CONNEXION, CORPS, format="json")
    assert r.cookies[locale.COOKIE]["secure"]
