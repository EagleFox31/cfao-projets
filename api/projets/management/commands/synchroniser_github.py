"""Synchronise les depots GitHub suivis (consommateur declare, service `synchro`).

    python manage.py synchroniser_github            # un passage
    python manage.py synchroniser_github --boucle   # toutes les INTERVALLE secondes

Chaque depot est lu independamment : une erreur sur l'un n'arrete pas les
autres, elle est notee dans le journal des erreurs et sur le depot.
"""
import logging
import time

from django.core.management.base import BaseCommand

from projets import erreurs, github
from projets.models import Depot

journal = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Lit les nouveaux commits des depots GitHub suivis."

    def add_arguments(self, parser):
        parser.add_argument("--boucle", action="store_true", help="tourne en continu")
        parser.add_argument("--intervalle", type=int, default=900, help="secondes entre deux passages")
        parser.add_argument("--projet", type=int, help="ne traiter que ce projet")

    def handle(self, *args, **options):
        while True:
            self._passage(options.get("projet"))
            if not options["boucle"]:
                return
            time.sleep(max(options["intervalle"], 60))

    def _passage(self, projet_id):
        depots = Depot.objects.select_related("projet")
        if projet_id:
            depots = depots.filter(projet_id=projet_id)
        total = 0
        for depot in depots:
            try:
                nouveaux = github.synchroniser(depot)
                total += nouveaux
                self.stdout.write(f"{depot.plein_nom} : {nouveaux} nouveau(x) commit(s)")
            except github.ErreurGitHub as exc:
                erreurs.noter("synchro", f"synchroniser {depot.plein_nom}", str(exc), detail="")
                self.stderr.write(f"{depot.plein_nom} : {exc}")
            except Exception as exc:  # noqa: BLE001 — un depot ne bloque pas les autres
                erreurs.noter("synchro", f"synchroniser {depot.plein_nom}", repr(exc))
                journal.exception("synchronisation %s", depot.plein_nom)
        if total:
            github.rattacher_personnes()
