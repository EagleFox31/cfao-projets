"""Client Cerbos pour validation des autorisations (PEP).

API HTTP stable du PDP (`POST /api/check/resources`), comme `cfao-core`.
Toute erreur vaut refus (default-deny).
"""
import uuid

import requests
from django.conf import settings
from rest_framework.exceptions import PermissionDenied


def check_permission(principal: dict, resource: dict, action: str) -> bool:
    """Interroge le PDP Cerbos en HTTP."""
    payload = {
        "requestId": str(uuid.uuid4()),
        "principal": {
            "id": principal.get("id", "anonymous"),
            "roles": principal.get("roles") or ["_anon"],
            "attr": principal.get("attr", {}),
        },
        "resources": [
            {
                "resource": {
                    "kind": resource["kind"],
                    "id": str(resource.get("id") or "_new"),
                    "attr": resource.get("attr", {}),
                },
                "actions": [action],
            }
        ],
    }

    url = f"{settings.CERBOS_HTTP.rstrip('/')}/api/check/resources"
    try:
        resp = requests.post(url, json=payload, timeout=3)
        resp.raise_for_status()
        results = resp.json().get("results") or [{}]
        return results[0].get("actions", {}).get(action) == "EFFECT_ALLOW"
    except Exception:
        # Default-deny en cas d'erreur
        return False


def enforce_permission(principal: dict, resource: dict, action: str):
    """Leve une exception 403 si l'action est refusee."""
    if not check_permission(principal, resource, action):
        raise PermissionDenied(f"Action '{action}' non autorisee sur cette ressource.")
