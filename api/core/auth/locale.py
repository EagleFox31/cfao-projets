"""Modes autonome (developpement) et local : identite sans Keycloak.

Deux sources, comme le kit `template-service` :
- l'en-tete `X-User-ID` (tests, curl), en mode autonome seulement ;
- le cookie de session (`COOKIE_SESSION`, `cfao_session` par defaut), signe par le service a la connexion
  (`/pj-donnees/connexion`), pour que le portail fonctionne tel quel.

Le mode autonome ne verifie aucun mot de passe : il n'est autorise
qu'avec DEBUG (voir `config/settings/base.py`). Le mode local verifie le
mot de passe a la connexion (`comptes.py`) et ne reconnait que les
profils de `PROFILS_LOCAUX`.
"""
from django.conf import settings
from django.core import signing
from rest_framework import authentication

from .identity import get_identity_provider, profil_par_id
from .principal import construire_principal

COOKIE = settings.COOKIE_SESSION   # nom configurable (COOKIE_SESSION)
DUREE_PERSISTANTE = 30 * 24 * 3600
DUREE_NAVIGATEUR = 12 * 3600
# Un sel par duree : la duree de vie fait partie de la signature.
_SELS = {"p": ("cr-session-persistante", DUREE_PERSISTANTE),
         "n": ("cr-session-navigateur", DUREE_NAVIGATEUR)}


def signer_session(user_id: str, persistante: bool) -> tuple[str, int]:
    """La valeur du cookie de session et sa duree de vie."""
    genre = "p" if persistante else "n"
    sel, duree = _SELS[genre]
    return f"{genre}:{signing.TimestampSigner(salt=sel).sign(user_id)}", duree


def lire_session(valeur: str | None) -> str | None:
    """L'identifiant porte par un cookie de session valide, ou None."""
    genre, _, signe = (valeur or "").partition(":")
    if genre not in _SELS or not signe:
        return None
    sel, duree = _SELS[genre]
    try:
        return signing.TimestampSigner(salt=sel).unsign(signe, max_age=duree)
    except signing.BadSignature:
        return None


class LocaleAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        autonome = settings.DEPLOYMENT_MODE == "standalone"
        user_id = (autonome and request.headers.get("X-User-ID")) or lire_session(request.COOKIES.get(COOKIE))
        if not user_id:
            return None
        # Un compte retire des profils perd l'acces, meme avec un cookie encore valide.
        if not autonome and not profil_par_id(user_id):
            return None
        resolu = get_identity_provider().resolve_user(user_id=user_id)
        return construire_principal({**resolu, "id": user_id}), None

    def authenticate_header(self, request):
        # Un en-tete WWW-Authenticate fait renvoyer 401 (et non 403) par DRF.
        return "Session"
