"""Declare une personne avant sa premiere connexion, pour lui rattacher ses commits.

Idempotent : relancer avec les memes valeurs n'ecrit rien. La fiche porte un
sujet provisoire derive de l'e-mail ; a la premiere connexion par la plateforme
(meme e-mail), elle prend le vrai sujet et garde login GitHub et adresses.
"""
from django.core.management.base import BaseCommand, CommandError

from projets import formulaires, github
from projets.models import Personne


class Command(BaseCommand):
    help = "Declare (ou complete) une personne : e-mail, nom, login GitHub, autres adresses de commit."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--prenom", default="")
        parser.add_argument("--nom", default="")
        parser.add_argument("--github", default="", dest="login", help="login GitHub")
        parser.add_argument("--adresse-git", action="append", default=[], dest="adresses",
                            help="autre adresse d'auteur de commit (repetable)")

    def handle(self, *args, email, prenom, nom, login, adresses, **_):
        email = email.strip().lower()
        if "@" not in email:
            raise CommandError("--email : adresse invalide")
        propres, erreur = formulaires.adresses_git(adresses)
        if erreur:
            raise CommandError(erreur)
        login = login.strip().lstrip("@")

        personne = (Personne.objects.filter(email__iexact=email).first()
                    or Personne.objects.filter(sujet=Personne.sujet_pre_enregistre(email)).first())
        cree = personne is None
        if cree:
            personne = Personne(sujet=Personne.sujet_pre_enregistre(email), email=email)

        voulu = {"prenom": prenom or personne.prenom, "nom": nom or personne.nom,
                 "github_login": login or personne.github_login,
                 "adresses_git": sorted(set(personne.adresses_git or []) | set(propres))}
        modifs = [k for k, v in voulu.items() if getattr(personne, k) != v]
        for k in modifs:
            setattr(personne, k, voulu[k])
        if cree or modifs:
            personne.save()
        relies = github.rattacher_personnes()
        etat = "creee" if cree else ("mise a jour (" + ", ".join(modifs) + ")" if modifs else "inchangee")
        self.stdout.write(f"{personne.nom_complet} <{email}> : {etat} ; {relies} commit(s) rattache(s)")
