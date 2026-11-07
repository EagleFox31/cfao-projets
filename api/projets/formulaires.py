"""Validation des corps de requete, partagee par les vues et les propositions.

Une proposition acceptee applique exactement le meme controle qu'une
modification directe : les deux chemins passent ici.
"""
from datetime import date

from .models import (ROLES_MEMBRE, STATUTS_PROJET, STATUTS_TACHE, TYPES_PROPOSITION,
                     Personne)


class Invalide(Exception):
    """Corps refuse ; le message est affichable tel quel."""


def _texte(valeur, champ, maximum, obligatoire=False):
    if valeur is None:
        if obligatoire:
            raise Invalide(f"{champ} obligatoire")
        return None
    if not isinstance(valeur, str):
        raise Invalide(f"{champ} : texte attendu")
    valeur = valeur.strip()
    if obligatoire and not valeur:
        raise Invalide(f"{champ} obligatoire")
    if len(valeur) > maximum:
        raise Invalide(f"{champ} : {maximum} caractères au plus")
    return valeur


def _date(valeur, champ):
    if valeur in (None, ""):
        return None
    try:
        return date.fromisoformat(str(valeur))
    except ValueError:
        raise Invalide(f"{champ} : date AAAA-MM-JJ attendue") from None


def _choix(valeur, champ, choix):
    if valeur is None:
        return None
    codes = [c for c, _ in choix]
    if valeur not in codes:
        raise Invalide(f"{champ} : valeurs possibles {', '.join(codes)}")
    return valeur


def _entier(valeur, champ, minimum, maximum):
    if valeur in (None, ""):
        return None
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        raise Invalide(f"{champ} : entier attendu")
    if not minimum <= valeur <= maximum:
        raise Invalide(f"{champ} : entre {minimum} et {maximum}")
    return valeur


def _personne(valeur, champ):
    """Accepte l'identifiant interne ou le `sujet` d'une personne connue."""
    if valeur in (None, ""):
        return None
    if isinstance(valeur, int) and not isinstance(valeur, bool):
        personne = Personne.objects.filter(id=valeur).first()
    else:
        personne = Personne.objects.filter(sujet=str(valeur)).first()
    if personne is None:
        raise Invalide(f"{champ} : personne inconnue")
    return personne


def projet(corps, partiel=False):
    """Champs d'un projet ; `partiel` pour un PATCH (seuls les champs presents)."""
    if not isinstance(corps, dict):
        raise Invalide("corps JSON attendu")
    champs = {}
    if "nom" in corps or not partiel:
        champs["nom"] = _texte(corps.get("nom"), "nom", 200, obligatoire=True)
    if "description" in corps:
        champs["description"] = _texte(corps.get("description"), "description", 20_000) or ""
    if "statut" in corps:
        champs["statut"] = _choix(corps["statut"], "statut", STATUTS_PROJET)
    for cle in ("date_debut", "date_fin"):
        if cle in corps:
            champs[cle] = _date(corps[cle], cle)
    if "avancement_manuel" in corps:
        champs["avancement_manuel"] = _entier(corps["avancement_manuel"], "avancement_manuel", 0, 100)
    if "scope_node" in corps:
        champs["scope_node"] = _texte(corps.get("scope_node"), "scope_node", 64) or ""
    if "brand" in corps:
        champs["brand"] = _texte(corps.get("brand"), "brand", 64) or ""
    debut, fin = champs.get("date_debut"), champs.get("date_fin")
    if debut and fin and fin < debut:
        raise Invalide("date_fin : antérieure à date_debut")
    return champs


def tache(corps, partiel=False):
    if not isinstance(corps, dict):
        raise Invalide("corps JSON attendu")
    champs = {}
    if "titre" in corps or not partiel:
        champs["titre"] = _texte(corps.get("titre"), "titre", 200, obligatoire=True)
    if "description" in corps:
        champs["description"] = _texte(corps.get("description"), "description", 20_000) or ""
    if "statut" in corps:
        champs["statut"] = _choix(corps["statut"], "statut", STATUTS_TACHE)
    if "echeance" in corps:
        champs["echeance"] = _date(corps["echeance"], "echeance")
    if "poids" in corps:
        champs["poids"] = _entier(corps["poids"], "poids", 1, 100) or 1
    if "assigne" in corps:
        champs["assigne"] = _personne(corps["assigne"], "assigne")
    return champs


def membre(corps):
    if not isinstance(corps, dict):
        raise Invalide("corps JSON attendu")
    personne = _personne(corps.get("personne"), "personne")
    if personne is None:
        raise Invalide("personne obligatoire")
    role = _choix(corps.get("role_membre", "contributeur"), "role_membre", ROLES_MEMBRE)
    return {"personne": personne, "role_membre": role}


def depot(corps):
    if not isinstance(corps, dict):
        raise Invalide("corps JSON attendu")
    plein = _texte(corps.get("depot"), "depot", 201, obligatoire=True)
    if plein.count("/") != 1:
        raise Invalide("depot : forme attendue proprietaire/nom")
    proprietaire, nom = plein.split("/")
    for partie, champ in ((proprietaire, "proprietaire"), (nom, "nom")):
        if (not partie or not any(c.isalnum() for c in partie)
                or not all(c.isalnum() or c in "-._" for c in partie)):
            raise Invalide(f"depot : {champ} invalide")
    jeton_variable = _texte(corps.get("jeton_variable"), "jeton_variable", 80) or ""
    if jeton_variable and not all(c.isalnum() or c == "_" for c in jeton_variable):
        raise Invalide("jeton_variable : nom de variable d'environnement attendu")
    chemin = (_texte(corps.get("chemin"), "chemin", 200) or "").strip("/")
    if chemin and (".." in chemin.split("/") or any(c.isspace() or c == "\\" for c in chemin)):
        raise Invalide("chemin : sous-dossier du dépôt attendu (ex. apps/mail)")
    return {"proprietaire": proprietaire, "nom": nom, "jeton_variable": jeton_variable,
            "toutes_branches": bool(corps.get("toutes_branches", False)), "chemin": chemin}


def proposition(corps):
    """Valide une proposition : son type, sa cible et le contenu qu'elle appliquera."""
    if not isinstance(corps, dict):
        raise Invalide("corps JSON attendu")
    type_ = _choix(corps.get("type"), "type", TYPES_PROPOSITION)
    if type_ is None:
        raise Invalide("type obligatoire")
    contenu = corps.get("contenu")
    if not isinstance(contenu, dict) or not contenu:
        raise Invalide("contenu obligatoire")
    cible = corps.get("cible_id")
    if type_ == "modifier_tache":
        if not isinstance(cible, int) or isinstance(cible, bool):
            raise Invalide("cible_id obligatoire pour modifier une tâche")
    else:
        cible = None
    # Le contenu est valide maintenant, pour refuser tot une proposition inapplicable.
    valide = {"modifier_projet": lambda c: projet(c, partiel=True),
              "ajouter_tache": lambda c: tache(c),
              "modifier_tache": lambda c: tache(c, partiel=True),
              "ajouter_membre": membre}[type_](contenu)
    if not valide:
        raise Invalide("contenu : aucun champ modifiable")
    return {"type": type_, "cible_id": cible, "contenu": _serialisable(contenu, valide),
            "motif": _texte(corps.get("motif"), "motif", 5000) or ""}


def _serialisable(brut, valide):
    """Garde du contenu brut les seules cles retenues, en JSON (dates en texte)."""
    return {k: brut[k] for k in valide if k in brut}


MAX_ADRESSES_GIT = 20


def adresses_git(valeur):
    """Liste d'adresses d'auteur de commit : minuscules, sans doublon. Renvoie (liste, erreur)."""
    if valeur in (None, ""):
        return [], None
    if isinstance(valeur, str):
        valeur = valeur.replace(",", "\n").splitlines()
    if not isinstance(valeur, list) or not all(isinstance(a, str) for a in valeur):
        return None, "adresses_git : liste d'adresses attendue"
    propres = []
    for adresse in (a.strip().lower() for a in valeur):
        if not adresse:
            continue
        if "@" not in adresse or len(adresse) > 254 or any(c.isspace() for c in adresse):
            return None, f"adresses_git : adresse invalide « {adresse[:60]} »"
        if adresse not in propres:
            propres.append(adresse)
    if len(propres) > MAX_ADRESSES_GIT:
        return None, f"adresses_git : {MAX_ADRESSES_GIT} adresses au plus"
    return propres, None
