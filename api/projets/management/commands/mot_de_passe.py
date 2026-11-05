"""Cree ou remplace le mot de passe d'un compte du mode local.

    python manage.py mot_de_passe <identifiant> [mot de passe]

Sans mot de passe, en genere un et l'affiche une seule fois.
"""
import secrets

from django.core.management.base import BaseCommand, CommandError

from core.auth import comptes
from core.auth.identity import profil_local


class Command(BaseCommand):
    help = "Cree ou remplace le mot de passe d'un compte (mode local)."

    def add_arguments(self, parser):
        parser.add_argument("identifiant")
        parser.add_argument("mot_de_passe", nargs="?")

    def handle(self, identifiant, mot_de_passe=None, **options):
        identifiant = identifiant.strip().lower()
        if not profil_local(identifiant):
            raise CommandError(f"aucun profil local pour {identifiant}")
        mot_de_passe = mot_de_passe or secrets.token_urlsafe(9)
        try:
            comptes.changer_mot_de_passe(identifiant, mot_de_passe)
        except ValueError as e:
            raise CommandError(str(e)) from e
        self.stdout.write(f"nouveau mot de passe de {identifiant} : {mot_de_passe}")
