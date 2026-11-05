"""Mode integre : jeton Keycloak verifie par JWKS, perimetre lu sur la plateforme.

Aucun Keycloak ni CFAO Core reel : une cle RSA generee ici signe les
jetons, et `GET /api/v1/core/me` est simule.
"""
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.views import APIView

from core.auth import identity, oidc

EMETTEUR = "http://keycloak.invalid/realms/cfao"
CLE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
AUTRE_CLE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PERIMETRE = {"id": "u-42", "roles": ["trainer"], "scopeNodes": ["CMR"], "brands": ["TOYOTA"]}


AUDIENCE = "cfao-projets"


def _jeton(cle=CLE, **claims):
    contenu = {"sub": "u-42", "iss": EMETTEUR, "aud": AUDIENCE, "exp": int(time.time()) + 300, **claims}
    return jwt.encode(contenu, cle, algorithm="RS256", headers={"kid": "k1"})


class FauxCoreMe:
    """`GET /api/v1/core/me` : compte les appels, repond `donnees` ou echoue."""

    def __init__(self):
        self.appels = []
        self.donnees = PERIMETRE

    def __call__(self, url, headers=None, timeout=None):
        self.appels.append({"url": url, "headers": headers})
        if self.donnees is None:
            raise ConnectionError("plateforme injoignable")
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: self.donnees)


@pytest.fixture
def integre(settings, monkeypatch):
    settings.DEPLOYMENT_MODE = "integrated"
    settings.OIDC_ISSUER = EMETTEUR
    settings.OIDC_AUDIENCE = AUDIENCE
    settings.OIDC_JWKS_URL = "http://keycloak.invalid/certs"
    monkeypatch.setattr(oidc, "_jwk_client", SimpleNamespace(
        get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=CLE.public_key())))
    # Les vues prennent l'authentification du mode integre.
    monkeypatch.setattr(APIView, "authentication_classes", [oidc.KeycloakJWTAuthentication])
    core_me = FauxCoreMe()
    monkeypatch.setattr(identity.requests, "get", core_me)
    cache.clear()
    yield core_me
    cache.clear()


def _porteur(jeton):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
    return c


def test_un_jeton_valide_ouvre_l_api(integre, db, pdp):
    r = _porteur(_jeton()).get("/pj-donnees/personnes")
    assert r.status_code == 200
    principal = pdp.demandes[-1]["principal"]
    assert principal["id"] == "u-42" and principal["roles"] == ["trainer"]
    assert principal["attr"]["scopeNodes"] == ["CMR"]
    assert integre.appels[0]["url"] == "http://core.invalid/api/v1/core/me"
    assert integre.appels[0]["headers"]["Authorization"].startswith("Bearer ")


@pytest.mark.parametrize("jeton", [
    _jeton(exp=int(time.time()) - 10),
    _jeton(iss="http://ailleurs.invalid/realms/x"),
    _jeton(cle=AUTRE_CLE),
    "pas-un-jeton",
], ids=["expire", "mauvais-emetteur", "mauvaise-signature", "illisible"])
def test_un_jeton_refuse_ne_passe_pas(integre, db, jeton):
    reponse = _porteur(jeton).get("/pj-donnees/personnes")
    assert reponse.status_code == 401
    assert reponse.json() == {"erreur": "Jeton invalide."}
    assert integre.appels == []


def test_un_jeton_sans_expiration_est_refuse(integre, db):
    jeton = jwt.encode({"sub": "u-42", "iss": EMETTEUR}, CLE, algorithm="RS256")
    assert _porteur(jeton).get("/pj-donnees/personnes").status_code == 401


def test_l_audience_est_toujours_verifiee(integre, db, settings):
    assert _porteur(_jeton(aud="autre")).get("/pj-donnees/personnes").status_code == 401
    sans = jwt.encode({"sub": "u-42", "iss": EMETTEUR, "exp": int(time.time()) + 300}, CLE,
                      algorithm="RS256")
    assert _porteur(sans).get("/pj-donnees/personnes").status_code == 401
    settings.OIDC_AUDIENCE = ""
    assert _porteur(_jeton()).get("/pj-donnees/personnes").status_code == 401


def test_l_en_tete_x_user_id_est_ignore_en_mode_integre(integre, db):
    c = APIClient()
    c.credentials(HTTP_X_USER_ID="u-42")
    assert c.get("/pj-donnees/personnes").status_code == 401


def test_plateforme_injoignable_donne_un_principal_sans_droit(integre, db, pdp):
    """Fail-closed : sans perimetre, aucun role, et le PDP refuse."""
    integre.donnees = None
    pdp.reponse = lambda principal, _r, _a: principal["roles"] != ["_anon"]
    r = _porteur(_jeton()).get("/pj-donnees/personnes")
    assert r.status_code == 403
    assert pdp.demandes[-1]["principal"]["roles"] == ["_anon"]


def test_une_reponse_pour_un_autre_utilisateur_est_ignoree(integre, db, pdp):
    integre.donnees = {**PERIMETRE, "id": "quelqu-un-d-autre"}
    _porteur(_jeton()).get("/pj-donnees/personnes")
    assert pdp.demandes[-1]["principal"]["id"] == "u-42"
    assert pdp.demandes[-1]["principal"]["roles"] == ["_anon"]


def test_le_perimetre_est_garde_60_secondes(integre, db, monkeypatch):
    client = _porteur(_jeton())
    client.get("/pj-donnees/personnes")
    client.get("/pj-donnees/personnes")
    assert len(integre.appels) == 1
    poses = {}
    monkeypatch.setattr(identity.cache, "set",
                        lambda cle, valeur, timeout: poses.update({cle: timeout}))
    cache.clear()
    client.get("/pj-donnees/personnes")
    assert poses == {"user:scope:u-42": 60}


def test_un_echec_n_est_pas_garde_en_cache(integre, db):
    integre.donnees = None
    client = _porteur(_jeton())
    client.get("/pj-donnees/personnes")
    integre.donnees = PERIMETRE
    assert client.get("/pj-donnees/personnes").status_code == 200
    assert len(integre.appels) == 2
