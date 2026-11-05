"""Cree le compte de l'equipe technique (mode local), lance a chaque deploiement.

    python manage.py compte_technique

Le compte (profil `superadmin`, seul lecteur du journal d'erreurs) est ajoute
a `PROFILS_LOCAUX` s'il n'y est pas, avec le mot de passe initial s'il n'en
a pas encore : un mot de passe change ensuite n'est jamais ecrase.
Identifiants : PJ_COMPTE_TECHNIQUE et PJ_COMPTE_TECHNIQUE_MDP, sans valeur par
defaut : si l'un manque, aucun compte n'est cree (refus par defaut).
"""
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.auth import comptes
from core.auth.identity import _profils_locaux, profil_local

PROFIL = {"id": "equipe.technique", "roles": ["superadmin"],
          "firstName": "Equipe", "lastName": "TECHNIQUE", "scopeNodes": [], "brands": []}


class Command(BaseCommand):
    help = "Cree le compte de l'equipe technique s'il manque (mode local)."

    def handle(self, **options):
        if settings.DEPLOYMENT_MODE != "local":
            self.stdout.write("compte technique : inutile hors du mode local")
            return
        identifiant = os.environ.get("PJ_COMPTE_TECHNIQUE", "").strip().lower()
        mot_de_passe = os.environ.get("PJ_COMPTE_TECHNIQUE_MDP", "")
        if not identifiant or not mot_de_passe:
            self.stdout.write("compte technique : PJ_COMPTE_TECHNIQUE ou "
                              "PJ_COMPTE_TECHNIQUE_MDP absent, aucun compte cree")
            return
        if not profil_local(identifiant):
            profils = _profils_locaux() + [{"identifiant": identifiant, **PROFIL}]
            Path(settings.PROFILS_LOCAUX).write_text(
                json.dumps(profils, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.stdout.write(f"compte technique : profil {identifiant} ajoute")
        if comptes.existe(identifiant):
            self.stdout.write(f"compte technique : {identifiant} a deja un mot de passe")
            return
        comptes.changer_mot_de_passe(identifiant, mot_de_passe)
        self.stdout.write(f"compte technique : mot de passe initial de {identifiant} cree")
