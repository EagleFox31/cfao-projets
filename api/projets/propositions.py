"""Application d'une proposition acceptee.

Le contenu a ete valide a la soumission (`formulaires.proposition`) ; il
l'est a nouveau ici, car l'etat du projet a pu changer entre-temps. Chaque
application est idempotente : rejouer une proposition acceptee ne cree
pas de doublon (membre unique, tache retrouvee par la proposition).
"""
from django.db import transaction

from . import courrier, formulaires
from .models import Membre, Tache


class Inapplicable(Exception):
    """La proposition ne peut plus s'appliquer (cible disparue, contenu invalide)."""


@transaction.atomic
def appliquer(proposition, decideur):
    projet = proposition.projet
    contenu = proposition.contenu or {}
    try:
        if proposition.type == "modifier_projet":
            champs = formulaires.projet(contenu, partiel=True)
            for k, v in champs.items():
                setattr(projet, k, v)
            projet.save()
        elif proposition.type == "ajouter_tache":
            champs = formulaires.tache(contenu)
            if not Tache.objects.filter(projet=projet, titre=champs["titre"],
                                        cree_par=proposition.auteur).exists():
                tache = Tache.objects.create(projet=projet, cree_par=proposition.auteur, **champs)
                courrier.tache_assignee(tache, decideur)
        elif proposition.type == "modifier_tache":
            tache = Tache.objects.filter(projet=projet, id=proposition.cible_id).first()
            if tache is None:
                raise Inapplicable("la tâche visée n'existe plus")
            champs = formulaires.tache(contenu, partiel=True)
            ancien = tache.assigne_id
            for k, v in champs.items():
                setattr(tache, k, v)
            tache.save()
            if tache.assigne_id != ancien:
                courrier.tache_assignee(tache, decideur)
        elif proposition.type == "ajouter_membre":
            champs = formulaires.membre(contenu)
            membre, cree = Membre.objects.get_or_create(
                projet=projet, personne=champs["personne"],
                defaults={"role_membre": champs["role_membre"]})
            if cree:
                courrier.membre_ajoute(membre, decideur)
    except formulaires.Invalide as exc:
        raise Inapplicable(str(exc)) from exc
