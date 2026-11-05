"""Erreurs au format du portail : `{"erreur": "..."}` (contrat du service precedent)."""
from rest_framework import exceptions
from rest_framework.views import exception_handler


def erreur_en_francais(exc, context):
    reponse = exception_handler(exc, context)
    if reponse is None:
        return None
    if isinstance(exc, exceptions.NotAuthenticated):
        message = "connexion requise"
    elif isinstance(exc, exceptions.APIException) and isinstance(exc.detail, str):
        message = str(exc.detail)
    else:
        message = "requete invalide"
    reponse.data = {"erreur": message}
    return reponse
