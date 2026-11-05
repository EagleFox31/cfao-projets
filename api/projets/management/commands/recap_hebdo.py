"""Envoie a chaque chef de projet le recapitulatif de la semaine ecoulee.

    python manage.py recap_hebdo                 # semaine ISO precedente
    python manage.py recap_hebdo --semaine 2026-W44

Idempotent : le courrier porte `recap:<semaine>:<personne>` ; relancer la
commande n'envoie rien de plus.
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from projets import courrier, github
from projets.models import Membre, Personne


def semaine_precedente():
    annee, numero, _ = (date.today() - timedelta(days=7)).isocalendar()
    return f"{annee}-W{numero:02d}"


class Command(BaseCommand):
    help = "Recapitulatif hebdomadaire par courriel aux chefs de projet."

    def add_arguments(self, parser):
        parser.add_argument("--semaine", default=None, help="AAAA-Www (defaut : semaine precedente)")

    def handle(self, *args, **options):
        semaine = options["semaine"] or semaine_precedente()
        github.bornes_semaine(semaine)
        envoyes = 0
        for personne in Personne.objects.filter(participations__role_membre="chef").distinct():
            lignes = []
            for m in Membre.objects.filter(personne=personne, role_membre="chef").select_related("projet"):
                projet = m.projet
                if projet.statut in ("termine", "archive"):
                    continue
                a = github.activite([projet], semaine)
                lignes.append({"projet": projet.nom, "commits": a["total"]["commits"],
                               "additions": a["total"]["additions"], "deletions": a["total"]["deletions"],
                               "contributeurs": len(a["personnes"]), "avancement": projet.avancement()})
            if courrier.recap_hebdo(personne, semaine, lignes):
                envoyes += 1
        self.stdout.write(f"{semaine} : {envoyes} récapitulatif(s) envoyé(s)")
