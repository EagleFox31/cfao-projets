"""Controle d'origine des requetes qui ecrivent (POST/PUT/PATCH/DELETE).

Le cookie de session part tout seul avec chaque requete du navigateur : sans
controle, une page d'un autre site pourrait ecrire au nom du formateur
connecte (meme hote, ports differents = meme site pour `SameSite`). Une
requete qui ecrit doit donc venir d'une origine de `ORIGINES_AUTORISEES`.

Regles :
- `Origin` present : il doit etre autorise, avec ou sans cookie ;
- sinon `Referer` present : son origine doit etre autorisee ;
- ni l'un ni l'autre : refus si la requete porte le cookie de session ou
  vient d'un navigateur (`Sec-Fetch-Site`) ; sinon (curl, tests, en-tete
  `X-User-ID`) aucune credential n'est envoyee d'office, la requete passe
  et l'authentification decide.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.http import JsonResponse

METHODES_SURES = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _origine(url: str) -> str | None:
    u = urlsplit(url)
    if not u.scheme or not u.netloc:
        return None
    return f"{u.scheme}://{u.netloc}".lower()


class ControleOrigine:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in METHODES_SURES and not self._autorisee(request):
            return JsonResponse({"erreur": "origine non autorisee"}, status=403)
        return self.get_response(request)

    @staticmethod
    def _autorisee(request) -> bool:
        autorisees = {o.lower() for o in settings.ORIGINES_AUTORISEES}
        origine = request.headers.get("Origin")
        if origine is not None:
            return origine.rstrip("/").lower() in autorisees
        referent = request.headers.get("Referer")
        if referent:
            return _origine(referent) in autorisees
        from core.auth import locale   # meme nom de cookie que l'authentification
        return not (locale.COOKIE in request.COOKIES
                    or request.headers.get("Sec-Fetch-Site"))
