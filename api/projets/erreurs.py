"""Le journal des erreurs, consultable depuis le portail (`/portail/journal-erreurs`).

Le journal du serveur reste la reference technique ; celui-ci garde, en
base, ce qu'il faut pour retrouver une erreur signalee par un formateur :
qui, quand, quelle action, le message et la pile. Noter une erreur ne doit
jamais en provoquer une autre : tout echec ici est avale.
"""
import json
import logging
import traceback
from datetime import timedelta

from django.utils import timezone

from core.auth.identity import profil_par_id

from .models import Erreur

journal = logging.getLogger(__name__)

CONSERVATION = timedelta(days=90)
MAXIMUM = 2000            # lignes gardees au plus
TAILLE_TEXTE = 20_000     # caracteres gardes par message ou pile
TAILLE_CONTEXTE = 10_000  # octets JSON gardes pour le contexte


def _nom(user, owner):
    profil = getattr(user, "profil", None) or (profil_par_id(owner) if owner else None) or {}
    return " ".join(p for p in (profil.get("firstName"), profil.get("lastName")) if p)[:160]


def _contexte(contexte):
    if not isinstance(contexte, dict):
        return {}
    try:
        brut = json.dumps(contexte, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return {}
    # Rechargé depuis le texte : ce qui n'est pas JSON devient sa représentation.
    return json.loads(brut) if len(brut) <= TAILLE_CONTEXTE else {"tronque": brut[:TAILLE_CONTEXTE]}


def noter(origine, action, message="", detail=None, user=None, owner="", contexte=None):
    """Enregistre une erreur ; sans `detail`, la pile de l'exception en cours."""
    try:
        if detail is None:
            detail = traceback.format_exc()
            detail = "" if detail.startswith("NoneType: None") else detail
        owner = str(getattr(user, "id", "") or owner or "")[:128]
        Erreur.objects.create(
            origine=origine, action=str(action)[:120], owner=owner, nom=_nom(user, owner),
            message=str(message or "")[:TAILLE_TEXTE], detail=str(detail or "")[-TAILLE_TEXTE:],
            contexte=_contexte(contexte))
        _menage()
    except Exception:  # noqa: BLE001 — le journal ne doit jamais casser une requete
        journal.warning("erreur non notee", exc_info=True)


def _menage():
    Erreur.objects.filter(le__lt=timezone.now() - CONSERVATION).delete()
    trop = Erreur.objects.order_by("-le").values_list("id", flat=True)[MAXIMUM:MAXIMUM + 1]
    if trop:
        Erreur.objects.filter(id__lte=trop[0]).delete()


class Intercepteur:
    """Note toute exception non rattrapee par une route (reponse 500)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        user = getattr(request, "user", None)
        noter("service", f"{request.method} {request.path}", repr(exception),
              user=user if getattr(user, "id", None) else None)
        return None
