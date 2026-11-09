"""Envoi des courriels du module.

Quatre modes (`MAIL_MODE`) : `hub` (file d'attente cfao-academy-mail,
`POST /api/v1/mail/messages/enqueue`), `smtp` (envoi direct), `console`
(journal du serveur, pour le developpement) et `aucun`.

Chaque envoi porte un `correlation_id` deterministe : le journal `Courrier`
en garde une ligne unique, donc rejouer un evenement (synchronisation
relancee, double clic) n'envoie jamais deux fois le meme courriel.
"""
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction

from .models import Courrier

journal = logging.getLogger(__name__)
SOURCE = "cfao-projets"
DELAI = 10


def envoyer(kind, destinataires, sujet, texte, correlation_id, contexte=None):
    """Envoie un courriel une seule fois par `correlation_id`. Ne leve jamais."""
    destinataires = sorted({d for d in destinataires if d})
    if not destinataires or settings.MAIL_MODE == "aucun":
        return False
    try:
        with transaction.atomic():
            ligne = Courrier.objects.create(correlation_id=correlation_id[:160], kind=kind,
                                            destinataires=destinataires, sujet=sujet[:300],
                                            statut="en_cours")
    except IntegrityError:
        return False   # deja envoye
    sujet_complet = f"{settings.MAIL_PREFIX} {sujet}".strip()
    try:
        if settings.MAIL_MODE == "hub":
            _hub(kind, destinataires, sujet_complet, texte, correlation_id, contexte or {})
        elif settings.MAIL_MODE == "smtp":
            send_mail(sujet_complet, texte, settings.MAIL_FROM, destinataires, fail_silently=False)
        else:
            journal.info("courriel (%s) à %s : %s\n%s", kind, ", ".join(destinataires),
                         sujet_complet, texte)
        ligne.statut = "envoye"
    except Exception as exc:  # noqa: BLE001 — un courriel ne doit pas casser l'action
        journal.warning("courriel %s non envoyé : %s", correlation_id, exc)
        ligne.statut, ligne.detail = "echec", str(exc)[:500]
    ligne.save(update_fields=["statut", "detail"])
    return ligne.statut == "envoye"


def _hub(kind, destinataires, sujet, texte, correlation_id, contexte):
    reponse = requests.post(
        f"{settings.MAIL_HUB_URL}/api/v1/mail/messages/enqueue",
        headers={"X-Mail-Service-Key": settings.MAIL_HUB_KEY},
        json={"kind": kind, "source_app": SOURCE, "source_ref": correlation_id,
              "correlation_id": correlation_id, "to": destinataires, "locale": "fr",
              "module_url": settings.PJ_URL_PUBLIQUE,
              "context": {"subject": sujet, "body": texte, **contexte}},
        timeout=DELAI)
    if reponse.status_code >= 300:
        raise RuntimeError(f"hub {reponse.status_code}")


def _lien(chemin):
    return f"{settings.PJ_URL_PUBLIQUE}{chemin}"


# ── Evenements ────────────────────────────────────────────────────────

def membre_ajoute(membre, par):
    projet = membre.projet
    return envoyer(
        "projets.membre_ajoute", [membre.personne.email],
        f"Vous rejoignez le projet « {projet.nom} »",
        f"Bonjour {membre.personne.prenom or membre.personne.nom_complet},\n\n"
        f"{par.nom_complet} vous a ajouté au projet « {projet.nom} » "
        f"en tant que {membre.get_role_membre_display().lower()}.\n\n"
        f"Ouvrir le projet : {_lien(f'/projets/{projet.id}')}\n",
        f"membre:{membre.id}:{membre.role_membre}",
        {"projet": projet.nom, "role": membre.role_membre})


def tache_assignee(tache, par):
    if not tache.assigne or tache.assigne_id == getattr(par, "id", None):
        return False
    projet = tache.projet
    return envoyer(
        "projets.tache_assignee", [tache.assigne.email],
        f"Tâche assignée : {tache.titre}",
        f"Bonjour {tache.assigne.prenom or tache.assigne.nom_complet},\n\n"
        f"{par.nom_complet} vous a assigné la tâche « {tache.titre} » "
        f"du projet « {projet.nom} »"
        + (f", à rendre pour le {tache.echeance:%d/%m/%Y}" if tache.echeance else "") + ".\n\n"
        f"Ouvrir le projet : {_lien(f'/projets/{projet.id}')}\n",
        f"tache:{tache.id}:assigne:{tache.assigne_id}",
        {"projet": projet.nom, "tache": tache.titre})


def proposition_soumise(proposition, decideurs):
    projet = proposition.projet
    return envoyer(
        "projets.proposition_soumise", [p.email for p in decideurs],
        f"Proposition à examiner sur « {projet.nom} »",
        f"Bonjour,\n\n{proposition.auteur.nom_complet} propose : "
        f"{proposition.get_type_display().lower()} sur le projet « {projet.nom} ».\n"
        + (f"Motif : {proposition.motif}\n" if proposition.motif else "")
        + f"\nExaminer : {_lien(f'/projets/{projet.id}?onglet=propositions')}\n",
        f"proposition:{proposition.id}:soumise",
        {"projet": projet.nom, "type": proposition.type})


def proposition_decidee(proposition):
    if not proposition.auteur:
        return None   # issue GitHub sans auteur rattache : personne a prevenir
    projet = proposition.projet
    verdict = "acceptée" if proposition.statut == "acceptee" else "refusée"
    decideur = proposition.decideur.nom_complet if proposition.decideur else "le pilote du projet"
    return envoyer(
        "projets.proposition_decidee", [proposition.auteur.email],
        f"Votre proposition sur « {projet.nom} » a été {verdict}",
        f"Bonjour {proposition.auteur.prenom or proposition.auteur.nom_complet},\n\n"
        f"Votre proposition ({proposition.get_type_display().lower()}) a été {verdict} "
        f"par {decideur}.\n"
        + (f"Commentaire : {proposition.commentaire}\n" if proposition.commentaire else "")
        + f"\nOuvrir le projet : {_lien(f'/projets/{projet.id}')}\n",
        f"proposition:{proposition.id}:{proposition.statut}",
        {"projet": projet.nom, "statut": proposition.statut})


def recap_hebdo(personne, semaine, lignes):
    """Recapitulatif d'une semaine ISO pour une personne (pilote du projet)."""
    if not lignes:
        return False
    corps = [f"Bonjour {personne.prenom or personne.nom_complet},\n",
             f"Activité de la semaine {semaine} sur vos projets :\n"]
    for ligne in lignes:
        corps.append(f"- {ligne['projet']} : {ligne['commits']} commit(s), "
                     f"+{ligne['additions']} / -{ligne['deletions']} lignes, "
                     f"{ligne['contributeurs']} contributeur(s), avancement {ligne['avancement']} %")
    corps.append(f"\nTableau de bord : {_lien('/')}\n")
    return envoyer("projets.recap_hebdo", [personne.email], f"Récapitulatif {semaine}",
                   "\n".join(corps), f"recap:{semaine}:{personne.id}", {"semaine": semaine})
