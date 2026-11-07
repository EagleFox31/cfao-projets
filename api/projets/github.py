"""Lecture des depots GitHub : commits, statistiques, activite par semaine.

Lecture seule, par l'API REST publique (`GITHUB_API_URL`), avec le jeton
`GITHUB_TOKEN` ou celui que nomme `Depot.jeton_variable`. La branche par
defaut est decouverte, jamais supposee. Chaque commit est enregistre une
fois (`Commit` unique par depot et sha) : relancer une synchronisation,
ou recevoir un webhook pour un commit deja vu, ne change rien.
"""
import hashlib
import hmac
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone as tz

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import Commit, Depot, Personne

journal = logging.getLogger(__name__)
DELAI = 20
PAR_PAGE = 100
PAGES_MAX = 10              # par branche et par synchronisation
FICHIERS_MAX = 50           # detail garde par commit
FENETRE_INITIALE = timedelta(days=90)
MAX_BRANCHES = 30


class ErreurGitHub(Exception):
    """L'API a refuse ou n'a pas repondu ; le message est affichable."""


def _jeton(depot):
    if depot.jeton_variable:
        return os.environ.get(depot.jeton_variable, "")
    return settings.GITHUB_TOKEN


def _entetes(depot):
    entetes = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "cfao-projets"}
    jeton = _jeton(depot)
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    return entetes


def _get(depot, chemin, params=None):
    url = chemin if chemin.startswith("http") else f"{settings.GITHUB_API_URL}{chemin}"
    try:
        reponse = requests.get(url, headers=_entetes(depot), params=params, timeout=DELAI)
    except requests.RequestException as exc:
        raise ErreurGitHub(f"GitHub injoignable : {exc.__class__.__name__}") from exc
    if reponse.status_code == 404:
        raise ErreurGitHub(f"dépôt {depot.plein_nom} introuvable ou jeton sans accès")
    if reponse.status_code in (401, 403):
        raise ErreurGitHub(f"GitHub refuse l'accès à {depot.plein_nom} ({reponse.status_code})")
    if reponse.status_code >= 400:
        raise ErreurGitHub(f"GitHub a répondu {reponse.status_code}")
    return reponse


def _pages(depot, chemin, params):
    """Suit l'en-tete `Link` (rel=next), au plus PAGES_MAX pages."""
    url, pages = chemin, 0
    while url and pages < PAGES_MAX:
        reponse = _get(depot, url, params if pages == 0 else None)
        yield from reponse.json()
        url = reponse.links.get("next", {}).get("url")
        pages += 1


def infos_depot(depot):
    return _get(depot, f"/repos/{depot.proprietaire}/{depot.nom}").json()


def branches(depot):
    return [b["name"] for b in _pages(depot, f"/repos/{depot.proprietaire}/{depot.nom}/branches",
                                      {"per_page": PAR_PAGE})][:MAX_BRANCHES]


def commits_depuis(depot, branche, depuis):
    params = {"sha": branche, "per_page": PAR_PAGE}
    if depot.chemin:
        params["path"] = depot.chemin
    if depuis:
        params["since"] = depuis.astimezone(tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _pages(depot, f"/repos/{depot.proprietaire}/{depot.nom}/commits", params)


def detail_commit(depot, sha):
    return _get(depot, f"/repos/{depot.proprietaire}/{depot.nom}/commits/{sha}").json()


def _personne_pour(login, email):
    if login:
        personne = Personne.objects.filter(github_login__iexact=login).first()
        if personne:
            return personne
    if email:
        email = email.strip().lower()
        # Recherche dans les adresses secondaires faite en Python : portable
        # (SQLite, PostgreSQL) et la table des personnes reste petite.
        return (Personne.objects.filter(email__iexact=email).first()
                or next((p for p in Personne.objects.exclude(adresses_git=[]) if email in p.adresses_git), None))
    return None


def enregistrer_commit(depot, brut, branche=""):
    """Cree la ligne du commit si elle n'existe pas. Renvoie True si nouvelle."""
    sha = brut["sha"]
    if Commit.objects.filter(depot=depot, sha=sha).exists():
        return False
    detail = brut if "stats" in brut else detail_commit(depot, sha)
    auteur = detail.get("author") or {}
    git = (detail.get("commit") or {}).get("author") or {}
    login = auteur.get("login") or ""
    email = git.get("email") or ""
    fichiers = [f for f in detail.get("files") or [] if depot.fichier_suivi(f.get("filename", ""))]
    if depot.chemin:
        if not fichiers:
            return False   # commit hors du sous-dossier suivi (webhook ou liste non filtree)
        stats = {"additions": sum(f.get("additions", 0) or 0 for f in fichiers),
                 "deletions": sum(f.get("deletions", 0) or 0 for f in fichiers)}
    else:
        stats = detail.get("stats") or {}
    quand = git.get("date")
    try:
        date_commit = datetime.fromisoformat(quand.replace("Z", "+00:00")) if quand else timezone.now()
    except ValueError:
        date_commit = timezone.now()
    try:
        with transaction.atomic():
            Commit.objects.create(
                depot=depot, sha=sha, auteur_login=login[:80], auteur_nom=(git.get("name") or "")[:200],
                auteur_email=email[:254], personne=_personne_pour(login, email), date=date_commit,
                message=((detail.get("commit") or {}).get("message") or "").split("\n", 1)[0][:500],
                branche=branche[:120], additions=stats.get("additions", 0) or 0,
                deletions=stats.get("deletions", 0) or 0, fichiers=len(fichiers),
                fichiers_detail=[{"chemin": f.get("filename", ""), "additions": f.get("additions", 0),
                                  "deletions": f.get("deletions", 0), "statut": f.get("status", "")}
                                 for f in fichiers[:FICHIERS_MAX]],
                url=detail.get("html_url") or "")
    except IntegrityError:
        return False   # arrive en meme temps par un autre chemin (webhook + synchro)
    return True


def synchroniser(depot):
    """Lit les nouveaux commits du depot. Renvoie le nombre de lignes ajoutees."""
    try:
        infos = infos_depot(depot)
        branche_defaut = infos.get("default_branch") or depot.branche_par_defaut
        depuis = depot.derniere_synchro - timedelta(hours=1) if depot.derniere_synchro \
            else timezone.now() - FENETRE_INITIALE
        cibles = branches(depot) if depot.toutes_branches else [branche_defaut]
        if branche_defaut in cibles:
            cibles.remove(branche_defaut)
            cibles.insert(0, branche_defaut)   # ses commits portent la branche principale
        nouveaux = 0
        for branche in cibles:
            for brut in commits_depuis(depot, branche, depuis):
                if enregistrer_commit(depot, brut, branche):
                    nouveaux += 1
    except ErreurGitHub as exc:
        depot.derniere_erreur = str(exc)[:500]
        depot.save(update_fields=["derniere_erreur"])
        raise
    depot.branche_par_defaut = branche_defaut[:120]
    depot.derniere_synchro = timezone.now()
    depot.derniere_erreur = ""
    depot.save(update_fields=["branche_par_defaut", "derniere_synchro", "derniere_erreur"])
    return nouveaux


def rattacher_personnes():
    """Relie les commits orphelins aux personnes dont le login ou l'e-mail correspond."""
    total = 0
    for personne in Personne.objects.all():
        filtre = Q(pk__in=[])
        if personne.github_login:
            filtre |= Q(auteur_login__iexact=personne.github_login)
        if personne.email:
            filtre |= Q(auteur_email__iexact=personne.email)
        for adresse in personne.adresses_git or []:
            filtre |= Q(auteur_email__iexact=adresse)
        total += Commit.objects.filter(filtre, personne__isnull=True).update(personne=personne)
    return total


# ── Webhook ───────────────────────────────────────────────────────────

def signature_valide(secret, corps, entete):
    if not secret or not entete or not entete.startswith("sha256="):
        return False
    attendu = hmac.new(secret.encode(), corps, hashlib.sha256).hexdigest()
    return hmac.compare_digest(attendu, entete[len("sha256="):])


def traiter_push(charge):
    """Enregistre les commits d'un evenement `push` pour chaque depot suivi."""
    plein = ((charge.get("repository") or {}).get("full_name") or "")
    if "/" not in plein:
        return 0
    proprietaire, nom = plein.split("/", 1)
    ref = charge.get("ref") or ""
    branche = ref.rsplit("/", 1)[-1] if ref.startswith("refs/heads/") else ""
    nouveaux = 0
    for depot in Depot.objects.filter(proprietaire__iexact=proprietaire, nom__iexact=nom):
        if not depot.toutes_branches and depot.branche_par_defaut and branche != depot.branche_par_defaut:
            continue
        for brut in charge.get("commits") or []:
            try:
                if enregistrer_commit(depot, {"sha": brut.get("id") or brut.get("sha")}, branche):
                    nouveaux += 1
            except ErreurGitHub as exc:
                journal.warning("webhook %s : %s", depot.plein_nom, exc)
    return nouveaux


# ── Activite hebdomadaire ─────────────────────────────────────────────

def semaine_courante():
    annee, numero, _ = date.today().isocalendar()
    return f"{annee}-W{numero:02d}"


def bornes_semaine(semaine):
    """`AAAA-Www` → (lundi 00:00 UTC, lundi suivant 00:00 UTC)."""
    try:
        annee, numero = semaine.upper().split("-W")
        lundi = date.fromisocalendar(int(annee), int(numero), 1)
    except (ValueError, AttributeError):
        raise ValueError("semaine : forme AAAA-Www attendue") from None
    debut = datetime(lundi.year, lundi.month, lundi.day, tzinfo=tz.utc)
    return debut, debut + timedelta(days=7)


def _compare(depot, premier, dernier):
    return f"https://github.com/{depot.plein_nom}/compare/{premier}%5E...{dernier}"


def activite(projets, semaine):
    """Travail de la semaine par personne, tous depots des projets confondus.

    Renvoie `{semaine, debut, fin, total, personnes: [...], jours: [...]}` ;
    chaque personne porte ses commits, lignes ajoutees et supprimees,
    fichiers touches, et par depot le lien de comparaison du premier au
    dernier commit de la semaine (le « diff de la personne »).
    """
    debut, fin = bornes_semaine(semaine)
    commits = (Commit.objects.filter(depot__projet__in=projets, date__gte=debut, date__lt=fin)
               .select_related("depot", "depot__projet", "personne").order_by("date"))
    personnes = {}
    jours = [0] * 7
    total = {"commits": 0, "additions": 0, "deletions": 0, "fichiers": 0}
    for c in commits:
        cle = f"p{c.personne_id}" if c.personne_id else (c.auteur_login or c.auteur_email or c.auteur_nom or "?")
        p = personnes.setdefault(cle, {
            "personne": {"id": c.personne.id, "nom": c.personne.nom_complet} if c.personne else None,
            "login": c.auteur_login or (c.personne.github_login if c.personne else ""),
            "nom": c.personne.nom_complet if c.personne else (c.auteur_nom or c.auteur_login),
            "commits": 0, "additions": 0, "deletions": 0, "fichiers": 0,
            "depots": {}, "derniers": [], "jours": [0] * 7})
        for d in (p, total):
            d["commits"] += 1
            d["additions"] += c.additions
            d["deletions"] += c.deletions
            d["fichiers"] += c.fichiers
        jour = (c.date - debut).days
        if 0 <= jour < 7:
            jours[jour] += 1
            p["jours"][jour] += 1
        dep = p["depots"].setdefault(c.depot_id, {
            "depot": c.depot.plein_nom, "projet": c.depot.projet.nom, "projet_id": c.depot.projet_id,
            "commits": 0, "additions": 0, "deletions": 0, "premier": c.sha, "dernier": c.sha})
        dep["commits"] += 1
        dep["additions"] += c.additions
        dep["deletions"] += c.deletions
        dep["dernier"] = c.sha
        dep["diff"] = _compare(c.depot, dep["premier"], dep["dernier"])
        if len(p["derniers"]) < 8:
            p["derniers"].append({"sha": c.sha[:7], "message": c.message, "date": c.date.isoformat(),
                                  "url": c.url, "depot": c.depot.plein_nom,
                                  "additions": c.additions, "deletions": c.deletions})
    liste = sorted(personnes.values(), key=lambda p: (-p["commits"], p["nom"] or ""))
    for p in liste:
        p["depots"] = list(p["depots"].values())
    return {"semaine": semaine, "debut": debut.date().isoformat(),
            "fin": (fin - timedelta(days=1)).date().isoformat(), "total": total,
            "personnes": liste, "jours": jours}
