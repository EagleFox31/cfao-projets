"""Mots de passe des formateurs (mode `local`).

Le mode `local` sert le portail sur le reseau interne, sans Keycloak :
chaque compte a un mot de passe dont seule l'empreinte est gardee, dans
une base SQLite hors depot (`COMPTES_LOCAUX`, table `comptes`). Le profil
affiche reste celui de `PROFILS_LOCAUX`, retrouve par l'identifiant.

L'empreinte suit le format de Werkzeug (`scrypt:n:r:p$sel$hex`) : les
comptes du service precedent gardent leur mot de passe.

Apres cinq echecs, un identifiant attend une minute avant de reessayer.
"""
import hashlib
import hmac
import secrets
import sqlite3
import string
import threading
import time
from contextlib import closing

from django.conf import settings

ECHECS_MAX, ATTENTE = 5, 60
LONGUEUR_MIN = 4
_N, _R, _P = 32768, 8, 1
# Une empreinte de reference : un identifiant inconnu coute le meme calcul
# qu'un mauvais mot de passe, sa reponse ne le trahit pas.
_FACTICE = "scrypt:32768:8:1$facticefactice00$" + "0" * 128

_verrou = threading.Lock()
_echecs = {}


class TropDEssais(Exception):
    """L'identifiant a ete refuse trop souvent : il attend."""


def _base():
    cx = sqlite3.connect(settings.COMPTES_LOCAUX)
    cx.execute("CREATE TABLE IF NOT EXISTS comptes ("
               " identifiant TEXT PRIMARY KEY, empreinte TEXT NOT NULL, profil TEXT NOT NULL)")
    return cx


def _scrypt(mot_de_passe, sel, n, r, p):
    return hashlib.scrypt(mot_de_passe.encode(), salt=sel.encode(), n=n, r=r, p=p,
                          maxmem=132 * n * r * p).hex()


def empreinter(mot_de_passe):
    sel = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    return f"scrypt:{_N}:{_R}:{_P}${sel}${_scrypt(mot_de_passe, sel, _N, _R, _P)}"


def correspond(empreinte, mot_de_passe):
    try:
        methode, sel, attendu = empreinte.split("$", 2)
        nom, n, r, p = methode.split(":")
        if nom != "scrypt":
            return False
        calcule = _scrypt(mot_de_passe, sel, int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calcule, attendu)


def verifier(identifiant, mot_de_passe):
    """True si le mot de passe est celui du compte.

    Leve TropDEssais tant qu'un identifiant trop souvent refuse attend.
    """
    identifiant = (identifiant or "").strip().lower()
    maintenant = time.time()
    with _verrou:
        # Un identifiant sans essai depuis une minute repart de zero : la
        # table ne grossit pas avec les identifiants essayes.
        for ancien in [k for k, (_, le) in _echecs.items() if maintenant - le >= ATTENTE]:
            del _echecs[ancien]
        n, _ = _echecs.get(identifiant, (0, 0))
        if n >= ECHECS_MAX:
            raise TropDEssais(identifiant)
        # L'essai compte des maintenant : des envois simultanes ne passent
        # pas tous sous la limite pendant le calcul de l'empreinte.
        _echecs[identifiant] = n + 1, maintenant
    with closing(_base()) as cx:
        ligne = cx.execute("SELECT empreinte FROM comptes WHERE identifiant = ?",
                           (identifiant,)).fetchone()
    bon = correspond(ligne[0] if ligne else _FACTICE, mot_de_passe or "") and ligne is not None
    if bon:
        with _verrou:
            _echecs.pop(identifiant, None)
    return bon


def changer_mot_de_passe(identifiant, mot_de_passe):
    """Cree le mot de passe du compte, ou le remplace."""
    if len(mot_de_passe) < LONGUEUR_MIN:
        raise ValueError(f"mot de passe de {LONGUEUR_MIN} caracteres au moins")
    identifiant = identifiant.strip().lower()
    with closing(_base()) as cx, cx:
        cx.execute("INSERT INTO comptes (identifiant, empreinte, profil) VALUES (?, ?, '{}') "
                   "ON CONFLICT (identifiant) DO UPDATE SET empreinte = excluded.empreinte",
                   (identifiant, empreinter(mot_de_passe)))


def existe(identifiant):
    """True si le compte a deja un mot de passe."""
    with closing(_base()) as cx:
        return cx.execute("SELECT 1 FROM comptes WHERE identifiant = ?",
                          ((identifiant or "").strip().lower(),)).fetchone() is not None
