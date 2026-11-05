"""Interface d'identite et de perimetre (Pattern Adapter).

Modes geres par DEPLOYMENT_MODE :
- 'standalone' / 'local' : lit un profil local (fichier `PROFILS_LOCAUX`), sans dependances.
- 'integrated' : interroge l'API centrale de CFAO Academy (GET /api/v1/core/me) avec cache.

L'identifiant passe a `resolve_user` est toujours celui d'une identite
verifiee (`sub` d'un jeton valide, ou cookie signe par le service) : le
cache ne doit jamais etre indexe par une valeur choisie par le navigateur.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

import requests
from django.conf import settings
from django.core.cache import cache

DUREE_CACHE = 60


class IdentityProvider(Protocol):
    def resolve_user(self, user_id: str, raw_token: str = "") -> Dict[str, Any]:
        """Retourne le dictionnaire des roles et attributs du perimetre utilisateur."""
        ...


def _profils_locaux() -> list:
    try:
        return json.loads(Path(settings.PROFILS_LOCAUX).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def profil_local(identifiant: str) -> Optional[Dict[str, Any]]:
    """Le profil local qui porte cet identifiant de connexion, ou None."""
    identifiant = (identifiant or "").strip().lower()
    return next((p for p in _profils_locaux()
                 if str(p.get("identifiant", "")).lower() == identifiant), None)


def profil_par_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Le profil local de cet id (sans l'identifiant de connexion), ou None."""
    for profil in _profils_locaux():
        if profil.get("id") == user_id:
            return {k: v for k, v in profil.items() if k != "identifiant"}
    return None


class LocalMockIdentityProvider:
    """Modes autonome et local : profils du fichier `PROFILS_LOCAUX`."""

    def resolve_user(self, user_id: str, raw_token: str = "") -> Dict[str, Any]:
        profil = profil_par_id(user_id)
        if profil:
            return profil
        return {
            "id": user_id or "demo-user",
            "roles": ["workshop_manager"],
            "scopeNodes": ["CMR", "CMR-DLA"],
            "brands": ["TOYOTA", "PEUGEOT"],
            "email": "chef.atelier@cfao.com",
            "locale": "fr",
        }


class PlatformIdentityProvider:
    """Mode integre : appel securise vers CFAO Core."""

    def resolve_user(self, user_id: str, raw_token: str = "") -> Dict[str, Any]:
        cache_key = f"user:scope:{user_id}"
        resolved = cache.get(cache_key)
        if resolved is not None:
            return resolved

        url = f"{settings.PLATFORM_CORE_URL.rstrip('/')}/api/v1/core/me"
        try:
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {raw_token}"},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            if str(data.get("id")) != str(user_id):
                raise ValueError("identite differente de celle du jeton")
            cache.set(cache_key, data, timeout=DUREE_CACHE)
            return data
        except Exception:
            # Comportement fail-closed : retourne un dictionnaire minimal sans droits
            return {"id": user_id, "roles": [], "scopeNodes": [], "brands": []}


def get_identity_provider() -> IdentityProvider:
    if getattr(settings, "DEPLOYMENT_MODE", "standalone") == "integrated":
        return PlatformIdentityProvider()
    return LocalMockIdentityProvider()
