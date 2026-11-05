"""Mode integre : validation du JWT Keycloak via JWKS (architecture.md §6).

Le jeton arrive en `Authorization: Bearer`, injecte par la passerelle
(oauth2-proxy) ; aucun mot de passe ne transite par ce service.
"""
from __future__ import annotations

import logging

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from .identity import get_identity_provider
from .principal import construire_principal

journal = logging.getLogger(__name__)

_jwk_client: jwt.PyJWKClient | None = None


def _client() -> jwt.PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        if not settings.OIDC_JWKS_URL:
            raise exceptions.AuthenticationFailed("OIDC_JWKS_URL non configure.")
        _jwk_client = jwt.PyJWKClient(settings.OIDC_JWKS_URL)
    return _jwk_client


def verifier_jeton(token: str) -> dict:
    """Les claims d'un jeton valide ; leve AuthenticationFailed sinon."""
    # L'audience est toujours verifiee : sans elle, un jeton emis par le
    # meme royaume pour une autre application serait accepte.
    if not settings.OIDC_AUDIENCE:
        raise exceptions.AuthenticationFailed("OIDC_AUDIENCE non configuree.")
    options = {"require": ["exp", "sub", "aud"]}
    audience = settings.OIDC_AUDIENCE
    try:
        signing_key = _client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=settings.OIDC_ISSUER or None,
            options=options,
        )
    except jwt.PyJWTError as exc:  # signature, expiration, audience, emetteur...
        journal.info("jeton refuse : %s", exc)
        raise exceptions.AuthenticationFailed("Jeton invalide.") from exc


class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    """Authentifie via `Authorization: Bearer <JWT>` ; le perimetre vient de l'adaptateur."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header.startswith(self.keyword + " "):
            return None
        token = header[len(self.keyword) + 1:].strip()
        claims = verifier_jeton(token)
        resolu = get_identity_provider().resolve_user(user_id=claims["sub"], raw_token=token)
        return construire_principal({**resolu, "id": claims["sub"]}, claims), token

    def authenticate_header(self, request):
        return self.keyword
