"""Chaque test tourne sans PDP reel, sans GitHub et sans courrier sortant.

Le PDP Cerbos est remplace par la fixture `pdp` : elle autorise par
defaut et note chaque demande (kind, action, attributs), pour verifier
que chaque route passe bien par le PEP. Les regles elles-memes sont
testees par `cerbos compile --tests` (voir `cerbos/tests/`).
"""
from types import SimpleNamespace

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from core.authz import cerbos
from projets import github


class FauxPDP:
    def __init__(self):
        self.demandes = []
        self.reponse = True

    def __call__(self, principal, resource, action):
        self.demandes.append({"principal": principal, "kind": resource["kind"],
                              "id": resource.get("id"), "action": action,
                              "attr": resource.get("attr", {})})
        return self.reponse(principal, resource, action) if callable(self.reponse) else self.reponse

    def refuser(self, *actions):
        """Refuse ces actions (kind:action ou action seule), autorise le reste."""
        def regle(principal, resource, action):
            return action not in actions and f"{resource['kind']}:{action}" not in actions
        self.reponse = regle


@pytest.fixture(autouse=True)
def pdp(monkeypatch):
    faux = FauxPDP()
    monkeypatch.setattr(cerbos, "check_permission", faux)
    return faux


@pytest.fixture(autouse=True)
def courrier_console():
    with override_settings(MAIL_MODE="console"):
        yield


class FauxGitHub:
    """Remplace les appels HTTP a l'API GitHub par des reponses preparees."""

    def __init__(self):
        self.reponses = {}
        self.appels = []

    def __call__(self, depot, chemin, params=None):
        """Imite `requests.Response` : `.json()`, `.links`, `.status_code`."""
        self.appels.append((chemin, dict(params or {})))
        for prefixe, reponse in sorted(self.reponses.items(), key=lambda kv: -len(kv[0])):
            if chemin.startswith(prefixe):
                corps = reponse() if callable(reponse) else reponse
                return SimpleNamespace(json=lambda: corps, links={}, status_code=200)
        raise github.ErreurGitHub(f"non prepare : {chemin}")


@pytest.fixture
def faux_github(monkeypatch):
    faux = FauxGitHub()
    monkeypatch.setattr(github, "_get", faux)
    monkeypatch.setattr(github, "_pages", lambda depot, chemin, params=None: list(faux(depot, chemin, params).json()))
    return faux


@pytest.fixture
def client(db):
    """Un client identifie par l'en-tete `X-User-ID` (mode autonome)."""
    def ouvrir(user_id="f-demo"):
        c = APIClient()
        c.credentials(HTTP_X_USER_ID=user_id)
        return c
    return ouvrir


ORIGINE_PORTAIL = "http://localhost:8094"


@pytest.fixture
def anonyme(db):
    """Un navigateur sans session : il envoie l'origine de la passerelle, comme un vrai."""
    return APIClient(HTTP_ORIGIN=ORIGINE_PORTAIL)


@pytest.fixture
def projet(client):
    """Un projet cree par le formateur de demonstration (chef de projet)."""
    r = client().post("/pj-donnees/projets", {"nom": "Portail apprenants", "description": "Refonte"},
                      format="json")
    assert r.status_code == 201, r.content
    return r.json()
