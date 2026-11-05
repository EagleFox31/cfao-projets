"""Mode local : mot de passe obligatoire, plus d'en-tete X-User-ID."""
import pytest
from django.core.management import call_command

from core.auth import comptes, locale

# Empreinte Werkzeug (`generate_password_hash("secret1")`) : les comptes du
# service precedent gardent leur mot de passe.
WERKZEUG = ("scrypt:32768:8:1$zK5jrbr4fyCsyIZ2$d2a0ea8f9cc9e0951963f02be4e8355d0281a0fada1a9f0dde556a95"
            "df88c7f021bee386fa6c74f6f17cd4bc0904675c848608060291490b2bb1e3059104dfdf")


@pytest.fixture
def local(settings, tmp_path, monkeypatch):
    settings.DEPLOYMENT_MODE = "local"
    settings.COMPTES_LOCAUX = str(tmp_path / "comptes.sqlite")
    monkeypatch.setattr(comptes, "_echecs", {})
    comptes.changer_mot_de_passe("formateur.demo", "secret1")
    return settings


def connecter(client, mot_de_passe, identifiant="formateur.demo"):
    return client.post("/pj-donnees/connexion",
                       {"identifiant": identifiant, "motDePasse": mot_de_passe}, format="json")


def test_le_bon_mot_de_passe_ouvre_la_session(local, anonyme):
    r = connecter(anonyme, "secret1")
    assert r.status_code == 200 and r.json()["id"] == "f-demo"
    assert anonyme.get("/pj-donnees/session").json()["id"] == "f-demo"


@pytest.mark.parametrize("mot_de_passe", ["", "secret2", None])
def test_un_mauvais_mot_de_passe_est_refuse(local, anonyme, mot_de_passe):
    r = connecter(anonyme, mot_de_passe)
    assert r.status_code == 401
    assert r.json() == {"erreur": "identifiant ou mot de passe incorrect"}
    assert locale.COOKIE not in r.cookies


@pytest.mark.parametrize("mot_de_passe", ["", "secret1"])
def test_un_profil_sans_mot_de_passe_est_refuse(local, anonyme, mot_de_passe):
    # Profil present dans PROFILS_LOCAUX, mais aucun mot de passe defini.
    assert connecter(anonyme, mot_de_passe, identifiant="ki.demo").status_code == 401


def test_cinq_echecs_font_attendre(local, anonyme):
    for _ in range(comptes.ECHECS_MAX):
        assert connecter(anonyme, "faux").status_code == 401
    r = connecter(anonyme, "secret1")
    assert r.status_code == 429


def test_des_essais_simultanes_ne_depassent_pas_la_limite(local, monkeypatch):
    import threading
    # Le calcul de l'empreinte attend que tous les essais soient partis.
    depart = threading.Barrier(comptes.ECHECS_MAX + 1, timeout=5)
    vrai = comptes.correspond

    def lent(empreinte, mot_de_passe):
        depart.wait()
        return vrai(empreinte, mot_de_passe)
    monkeypatch.setattr(comptes, "correspond", lent)
    refus = []

    def essayer():
        try:
            comptes.verifier("formateur.demo", "faux")
        except comptes.TropDEssais:
            refus.append(1)
    fils = [threading.Thread(target=essayer) for _ in range(comptes.ECHECS_MAX + 3)]
    for f in fils:
        f.start()
    depart.wait()
    for f in fils:
        f.join(5)
    assert len(refus) == 3


def test_la_table_des_echecs_oublie_les_identifiants_anciens(local, monkeypatch):
    comptes.verifier("inconnu.1", "x")
    horloge = comptes.time.time() + comptes.ATTENTE
    monkeypatch.setattr(comptes.time, "time", lambda: horloge)
    comptes.verifier("inconnu.2", "x")
    assert list(comptes._echecs) == ["inconnu.2"]


def test_apres_l_attente_le_bon_mot_de_passe_repasse(local, monkeypatch):
    for _ in range(comptes.ECHECS_MAX):
        comptes.verifier("formateur.demo", "faux")
    with pytest.raises(comptes.TropDEssais):
        comptes.verifier("formateur.demo", "secret1")
    horloge = comptes.time.time() + comptes.ATTENTE
    monkeypatch.setattr(comptes.time, "time", lambda: horloge)
    assert comptes.verifier("formateur.demo", "secret1")


def test_l_en_tete_x_user_id_n_identifie_plus(local, client):
    assert client("f-demo").get("/pj-donnees/session").status_code == 401
    assert client("f-demo").get("/pj-donnees/projets").status_code == 401


def test_un_cookie_d_un_profil_retire_n_ouvre_pas_de_session(local, anonyme):
    anonyme.cookies[locale.COOKIE] = locale.signer_session("retire", False)[0]
    assert anonyme.get("/pj-donnees/session").status_code == 401


def test_une_empreinte_werkzeug_est_reconnue():
    assert comptes.correspond(WERKZEUG, "secret1")
    assert not comptes.correspond(WERKZEUG, "secret2")
    assert comptes.correspond(comptes.empreinter("secret1"), "secret1")
    assert not comptes.correspond("pbkdf2:sha256:1$a$b", "secret1")
    assert not comptes.correspond("n'importe quoi", "secret1")


def test_la_commande_change_le_mot_de_passe(local, anonyme, capsys):
    call_command("mot_de_passe", "Formateur.Demo", "nouveau1")
    assert connecter(anonyme, "secret1").status_code == 401
    assert connecter(anonyme, "nouveau1").status_code == 200
