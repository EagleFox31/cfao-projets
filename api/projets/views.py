"""Routes du gestionnaire de projets.

Chaque route est un PEP : la decision revient au PDP Cerbos (default-deny)
avec les attributs de la ressource (proprietaire, perimetre, role du
demandeur dans le projet, assigne, auteur). Les reponses sont en JSON,
les erreurs au format `{"erreur": "..."}`.
"""
import json
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth import comptes, locale
from core.auth.identity import profil_local
from core.authz import cerbos

from . import courrier, erreurs, formulaires, github, propositions
from .models import (ROLES_MEMBRE, STATUTS_PROJET, STATUTS_TACHE, TYPES_PROPOSITION, Depot,
                     Erreur, Membre, Personne, Projet, Proposition, Tache)

journal = logging.getLogger(__name__)

# Ressources Cerbos (cerbos/policies/*.yaml).
PROJET, TACHE, PROPOSITION, PERSONNE, JOURNAL = "projet", "tache", "proposition", "personne", "journal"
ORIGINES = ("service", "portail", "synchro")
LIMITE_LISTE = 500


def _erreur(message, code):
    return Response({"erreur": message}, status=code)


def _corps(request):
    return request.data if isinstance(request.data, dict) else {}


def _moi(request):
    return Personne.depuis_principal(request.user)


def _role_dans(projet, personne):
    m = Membre.objects.filter(projet=projet, personne=personne).only("role_membre").first()
    return m.role_membre if m else ""


def _attributs(projet, request, **extra):
    """Attributs Cerbos d'une ressource rattachee a un projet."""
    return {"ownerId": projet.cree_par.sujet, "scopeNode": projet.scope_node,
            "brand": projet.brand, "statut": projet.statut,
            "roleMembre": _role_dans(projet, _moi(request)), **extra}


def _autoriser(request, kind, ident, action, attr):
    cerbos.enforce_permission(request.user.to_cerbos(), {"kind": kind, "id": str(ident), "attr": attr}, action)


def _permis(request, kind, ident, action, attr):
    return cerbos.check_permission(request.user.to_cerbos(), {"kind": kind, "id": str(ident), "attr": attr}, action)


def _projet_ou_404(ident):
    return Projet.objects.select_related("cree_par").filter(id=ident).first()


def _projets_visibles(request):
    """Les projets que le PDP laisse lire : membre, createur ou meme perimetre.

    Les candidats sont bornes par la base (sinon tout pour l'equipe
    technique), puis chaque projet passe par Cerbos : les regles de
    visibilite ne vivent qu'a un endroit.
    """
    moi = _moi(request)
    principal = request.user
    candidats = Projet.objects.select_related("cree_par")
    if not {"superadmin", "build_team"} & set(principal.roles):
        perimetre = [n for n in principal.attr.get("scopeNodes", []) if n]
        filtre = Q(membres__personne=moi) | Q(cree_par=moi)
        if perimetre:
            filtre |= Q(scope_node__in=perimetre)
        candidats = candidats.filter(filtre).distinct()
    roles = dict(Membre.objects.filter(personne=moi).values_list("projet_id", "role_membre"))
    visibles = []
    for p in candidats[:LIMITE_LISTE]:
        attr = {"ownerId": p.cree_par.sujet, "scopeNode": p.scope_node, "brand": p.brand,
                "statut": p.statut, "roleMembre": roles.get(p.id, "")}
        if _permis(request, PROJET, p.id, "read", attr):
            visibles.append((p, roles.get(p.id, "")))
    return visibles


# ── Serialisation ─────────────────────────────────────────────────────

def ser_personne(p):
    return {"id": p.id, "sujet": p.sujet, "prenom": p.prenom, "nom": p.nom,
            "nom_complet": p.nom_complet, "email": p.email, "github_login": p.github_login}


def ser_membre(m):
    return {"id": m.id, "role_membre": m.role_membre, "personne": ser_personne(m.personne),
            "ajoute_le": m.ajoute_le.isoformat()}


def ser_tache(t):
    return {"id": t.id, "titre": t.titre, "description": t.description, "statut": t.statut,
            "assigne": ser_personne(t.assigne) if t.assigne else None,
            "echeance": t.echeance.isoformat() if t.echeance else None, "poids": t.poids,
            "cree_le": t.cree_le.isoformat(), "modifie_le": t.modifie_le.isoformat()}


def ser_depot(d):
    return {"id": d.id, "depot": d.plein_nom, "chemin": d.chemin, "libelle": d.libelle,
            "branche_par_defaut": d.branche_par_defaut,
            "toutes_branches": d.toutes_branches, "jeton_variable": d.jeton_variable,
            "derniere_synchro": d.derniere_synchro.isoformat() if d.derniere_synchro else None,
            "derniere_erreur": d.derniere_erreur, "commits": d.commits.count(),
            "url": f"https://github.com/{d.plein_nom}" + (f"/tree/{d.branche_par_defaut or 'HEAD'}/{d.chemin}" if d.chemin else "")}


def ser_proposition(p):
    return {"id": p.id, "projet": {"id": p.projet_id, "nom": p.projet.nom}, "type": p.type,
            "cible_id": p.cible_id, "contenu": p.contenu, "motif": p.motif, "statut": p.statut,
            "auteur": ser_personne(p.auteur),
            "decideur": ser_personne(p.decideur) if p.decideur else None,
            "decidee_le": p.decidee_le.isoformat() if p.decidee_le else None,
            "commentaire": p.commentaire, "soumise_le": p.soumise_le.isoformat()}


def ser_projet(p, role="", detail=False, droits=None):
    taches = list(p.taches.all())
    base = {"id": p.id, "nom": p.nom, "description": p.description, "statut": p.statut,
            "date_debut": p.date_debut.isoformat() if p.date_debut else None,
            "date_fin": p.date_fin.isoformat() if p.date_fin else None,
            "avancement": p.avancement(), "avancement_manuel": p.avancement_manuel,
            "scope_node": p.scope_node, "brand": p.brand, "cree_par": ser_personne(p.cree_par),
            "cree_le": p.cree_le.isoformat(), "modifie_le": p.modifie_le.isoformat(),
            "mon_role": role, "nb_membres": p.membres.count(),
            "taches_par_statut": {code: sum(1 for t in taches if t.statut == code)
                                  for code, _ in STATUTS_TACHE},
            "propositions_en_attente": p.propositions.filter(statut="soumise").count()}
    if detail:
        base["membres"] = [ser_membre(m) for m in p.membres.select_related("personne")]
        base["taches"] = [ser_tache(t) for t in p.taches.select_related("assigne")]
        base["depots"] = [ser_depot(d) for d in p.depots.all()]
        base["droits"] = droits or {}
    return base


# ── Sante et connexion ────────────────────────────────────────────────

class Sante(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"pret": True, "service": "cfao-projets", "mode": settings.DEPLOYMENT_MODE,
                         "courrier": settings.MAIL_MODE})


class Connexion(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if settings.DEPLOYMENT_MODE == "integrated":
            return Response({"erreur": "connexion par la plateforme",
                             "redirection": settings.OIDC_CONNEXION}, status=401)
        corps = _corps(request)
        identifiant = str(corps.get("identifiant") or "")
        if settings.DEPLOYMENT_MODE == "local":
            try:
                if not comptes.verifier(identifiant, str(corps.get("motDePasse") or "")):
                    return _erreur("identifiant ou mot de passe incorrect", 401)
            except comptes.TropDEssais:
                return _erreur("trop de tentatives, reessayez dans une minute", 429)
        profil = profil_local(identifiant)
        if not profil:
            return _erreur("identifiant ou mot de passe incorrect", 401)
        persistante = bool(corps.get("seSouvenir"))
        valeur, duree = locale.signer_session(profil["id"], persistante)
        r = Response({k: v for k, v in profil.items() if k != "identifiant"} | {"compte": True})
        r.set_cookie(locale.COOKIE, valeur, max_age=duree if persistante else None,
                     httponly=True, samesite="Lax", path="/", secure=settings.COOKIE_SECURE)
        return r


class Session(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user:
            return _erreur("aucune session", 401)
        moi = _moi(request)
        return Response(request.user.profil_portail() | {"personne": ser_personne(moi)})


class Deconnexion(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        corps = {"deconnecte": True}
        if settings.DEPLOYMENT_MODE == "integrated":
            corps["redirection"] = settings.OIDC_DECONNEXION
        r = Response(corps)
        r.delete_cookie(locale.COOKIE, path="/", samesite="Lax")
        return r


class Referentiel(APIView):
    def get(self, request):
        return Response({
            "statuts_projet": [{"code": c, "libelle": l} for c, l in STATUTS_PROJET],
            "statuts_tache": [{"code": c, "libelle": l} for c, l in STATUTS_TACHE],
            "roles_membre": [{"code": c, "libelle": l} for c, l in ROLES_MEMBRE],
            "types_proposition": [{"code": c, "libelle": l} for c, l in TYPES_PROPOSITION],
            "semaine_courante": github.semaine_courante(),
            "peut_creer_projet": _permis(request, PROJET, "_new", "create", {
                "ownerId": request.user.id, "scopeNode": request.user.attr.get("scopeNode", ""),
                "brand": "", "statut": "", "roleMembre": ""}),
        })


# ── Personnes ─────────────────────────────────────────────────────────

class Personnes(APIView):
    def get(self, request):
        _moi(request)
        _autoriser(request, PERSONNE, "*", "list", {"ownerId": request.user.id})
        q = (request.query_params.get("q") or "").strip()
        lignes = Personne.objects.filter(actif=True)
        if q:
            lignes = lignes.filter(Q(nom__icontains=q) | Q(prenom__icontains=q)
                                   | Q(email__icontains=q) | Q(github_login__icontains=q))
        return Response({"personnes": [ser_personne(p) for p in lignes[:LIMITE_LISTE]]})


class PersonneMoi(APIView):
    def get(self, request):
        return Response(ser_personne(_moi(request)))

    def patch(self, request):
        moi = _moi(request)
        _autoriser(request, PERSONNE, moi.sujet, "update", {"ownerId": moi.sujet})
        return _modifier_personne(moi, _corps(request))


class PersonneDetail(APIView):
    def patch(self, request, ident):
        personne = Personne.objects.filter(id=ident).first()
        if not personne:
            return _erreur("introuvable", 404)
        _autoriser(request, PERSONNE, personne.sujet, "update", {"ownerId": personne.sujet})
        return _modifier_personne(personne, _corps(request))


def _modifier_personne(personne, corps):
    if "github_login" in corps:
        login = corps.get("github_login")
        if login is not None and not isinstance(login, str):
            return _erreur("github_login : texte attendu", 400)
        login = (login or "").strip().lstrip("@")
        if login and not all(c.isalnum() or c == "-" for c in login) or len(login) > 39:
            return _erreur("github_login : identifiant GitHub invalide", 400)
        personne.github_login = login
    if "actif" in corps:
        personne.actif = bool(corps["actif"])
    personne.save()
    if personne.github_login:
        github.rattacher_personnes()
    return Response(ser_personne(personne))


# ── Projets ───────────────────────────────────────────────────────────

class Projets(APIView):
    def get(self, request):
        statut = request.query_params.get("statut")
        visibles = _projets_visibles(request)
        if statut:
            visibles = [(p, r) for p, r in visibles if p.statut == statut]
        return Response({"projets": [ser_projet(p, r) for p, r in visibles]})

    def post(self, request):
        moi = _moi(request)
        try:
            champs = formulaires.projet(_corps(request))
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        scope = champs.get("scope_node") or request.user.attr.get("scopeNode", "")
        _autoriser(request, PROJET, "_new", "create",
                   {"ownerId": moi.sujet, "scopeNode": scope, "brand": champs.get("brand", ""),
                    "statut": champs.get("statut", "en_cours"), "roleMembre": ""})
        with transaction.atomic():
            projet = Projet.objects.create(cree_par=moi, **{**champs, "scope_node": scope})
            Membre.objects.create(projet=projet, personne=moi, role_membre="chef")
        return Response(ser_projet(projet, "chef"), status=201)


class ProjetDetail(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        attr = _attributs(projet, request)
        _autoriser(request, PROJET, projet.id, "read", attr)
        droits = {a: _permis(request, PROJET, projet.id, a, attr)
                  for a in ("update", "delete", "manage_members", "sync")}
        droits["creer_tache"] = _permis(request, TACHE, "_new", "create", {**attr, "assigneId": ""})
        droits["proposer"] = _permis(request, PROPOSITION, "_new", "create",
                                     {**attr, "auteurId": request.user.id})
        droits["decider"] = _permis(request, PROPOSITION, "*", "decide", {**attr, "auteurId": ""})
        return Response(ser_projet(projet, attr["roleMembre"], detail=True, droits=droits))

    def patch(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "update", _attributs(projet, request))
        try:
            champs = formulaires.projet(_corps(request), partiel=True)
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        for k, v in champs.items():
            setattr(projet, k, v)
        projet.save()
        return Response(ser_projet(projet, _role_dans(projet, _moi(request))))

    def delete(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return Response(status=status.HTTP_204_NO_CONTENT)
        _autoriser(request, PROJET, projet.id, "delete", _attributs(projet, request))
        projet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Membres ───────────────────────────────────────────────────────────

class Membres(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "read", _attributs(projet, request))
        return Response({"membres": [ser_membre(m) for m in projet.membres.select_related("personne")]})

    def post(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "manage_members", _attributs(projet, request))
        try:
            champs = formulaires.membre(_corps(request))
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        membre, cree = Membre.objects.get_or_create(
            projet=projet, personne=champs["personne"], defaults={"role_membre": champs["role_membre"]})
        if not cree and membre.role_membre != champs["role_membre"]:
            membre.role_membre = champs["role_membre"]
            membre.save(update_fields=["role_membre"])
        if cree:
            courrier.membre_ajoute(membre, _moi(request))
        return Response(ser_membre(membre), status=201 if cree else 200)


class MembreDetail(APIView):
    def _trouver(self, ident, mid):
        projet = _projet_ou_404(ident)
        membre = Membre.objects.select_related("personne").filter(projet=projet, id=mid).first() if projet else None
        return projet, membre

    def patch(self, request, ident, mid):
        projet, membre = self._trouver(ident, mid)
        if not membre:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "manage_members", _attributs(projet, request))
        role = _corps(request).get("role_membre")
        if role not in dict(ROLES_MEMBRE):
            return _erreur("role_membre invalide", 400)
        if membre.role_membre == "chef" and role != "chef" and not \
                projet.membres.filter(role_membre="chef").exclude(id=membre.id).exists():
            return _erreur("un projet garde au moins un chef de projet", 400)
        membre.role_membre = role
        membre.save(update_fields=["role_membre"])
        return Response(ser_membre(membre))

    def delete(self, request, ident, mid):
        projet, membre = self._trouver(ident, mid)
        if not membre:
            return Response(status=status.HTTP_204_NO_CONTENT)
        _autoriser(request, PROJET, projet.id, "manage_members", _attributs(projet, request))
        if membre.role_membre == "chef" and not \
                projet.membres.filter(role_membre="chef").exclude(id=membre.id).exists():
            return _erreur("un projet garde au moins un chef de projet", 400)
        membre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Taches ────────────────────────────────────────────────────────────

class Taches(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "read", _attributs(projet, request))
        return Response({"taches": [ser_tache(t) for t in projet.taches.select_related("assigne")]})

    def post(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        try:
            champs = formulaires.tache(_corps(request))
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        assigne = champs.get("assigne")
        _autoriser(request, TACHE, "_new", "create",
                   _attributs(projet, request, assigneId=assigne.sujet if assigne else ""))
        moi = _moi(request)
        tache = Tache.objects.create(projet=projet, cree_par=moi, **champs)
        courrier.tache_assignee(tache, moi)
        return Response(ser_tache(tache), status=201)


class TacheDetail(APIView):
    def _trouver(self, ident, tid):
        projet = _projet_ou_404(ident)
        tache = Tache.objects.select_related("assigne").filter(projet=projet, id=tid).first() if projet else None
        return projet, tache

    def patch(self, request, ident, tid):
        projet, tache = self._trouver(ident, tid)
        if not tache:
            return _erreur("introuvable", 404)
        _autoriser(request, TACHE, tache.id, "update",
                   _attributs(projet, request, assigneId=tache.assigne.sujet if tache.assigne else ""))
        try:
            champs = formulaires.tache(_corps(request), partiel=True)
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        ancien = tache.assigne_id
        for k, v in champs.items():
            setattr(tache, k, v)
        tache.save()
        if tache.assigne_id != ancien:
            courrier.tache_assignee(tache, _moi(request))
        return Response(ser_tache(tache))

    def delete(self, request, ident, tid):
        projet, tache = self._trouver(ident, tid)
        if not tache:
            return Response(status=status.HTTP_204_NO_CONTENT)
        _autoriser(request, TACHE, tache.id, "delete",
                   _attributs(projet, request, assigneId=tache.assigne.sujet if tache.assigne else ""))
        tache.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Depots GitHub ─────────────────────────────────────────────────────

class Depots(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "read", _attributs(projet, request))
        return Response({"depots": [ser_depot(d) for d in projet.depots.all()]})

    def post(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "update", _attributs(projet, request))
        try:
            champs = formulaires.depot(_corps(request))
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        depot, cree = Depot.objects.get_or_create(
            projet=projet, proprietaire=champs["proprietaire"], nom=champs["nom"], chemin=champs["chemin"],
            defaults={k: champs[k] for k in ("jeton_variable", "toutes_branches")})
        return Response(ser_depot(depot), status=201 if cree else 200)


class DepotDetail(APIView):
    def delete(self, request, ident, did):
        projet = _projet_ou_404(ident)
        depot = Depot.objects.filter(projet=projet, id=did).first() if projet else None
        if not depot:
            return Response(status=status.HTTP_204_NO_CONTENT)
        _autoriser(request, PROJET, projet.id, "update", _attributs(projet, request))
        depot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepotSynchroniser(APIView):
    def post(self, request, ident, did):
        projet = _projet_ou_404(ident)
        depot = Depot.objects.filter(projet=projet, id=did).first() if projet else None
        if not depot:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "sync", _attributs(projet, request))
        try:
            nouveaux = github.synchroniser(depot)
        except github.ErreurGitHub as exc:
            erreurs.noter("synchro", f"synchroniser {depot.plein_nom}", str(exc), user=request.user)
            return _erreur(str(exc), 502)
        github.rattacher_personnes()
        return Response({"nouveaux": nouveaux, "depot": ser_depot(depot)})


# ── Activite hebdomadaire ─────────────────────────────────────────────

def _semaine(request):
    semaine = request.query_params.get("semaine") or github.semaine_courante()
    github.bornes_semaine(semaine)   # ValueError si mal formee
    return semaine


class ProjetActivite(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        _autoriser(request, PROJET, projet.id, "read", _attributs(projet, request))
        try:
            semaine = _semaine(request)
        except ValueError as exc:
            return _erreur(str(exc), 400)
        return Response(github.activite([projet], semaine))


class ActiviteSemaine(APIView):
    def get(self, request):
        try:
            semaine = _semaine(request)
        except ValueError as exc:
            return _erreur(str(exc), 400)
        visibles = [p for p, _ in _projets_visibles(request)]
        resultat = github.activite(visibles, semaine)
        resultat["projets"] = [{"id": p.id, "nom": p.nom, "statut": p.statut, "avancement": p.avancement()}
                               for p in visibles]
        return Response(resultat)


# ── Propositions ──────────────────────────────────────────────────────

def _decideurs(projet):
    return [m.personne for m in projet.membres.filter(role_membre="chef").select_related("personne")]


class ProjetPropositions(APIView):
    def get(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        attr = _attributs(projet, request)
        _autoriser(request, PROJET, projet.id, "read", attr)
        lignes = projet.propositions.select_related("auteur", "decideur", "projet")
        # Sans le droit de decider, chacun ne voit que ses propres propositions.
        if not _permis(request, PROPOSITION, "*", "decide", {**attr, "auteurId": ""}):
            lignes = lignes.filter(auteur=_moi(request))
        return Response({"propositions": [ser_proposition(p) for p in lignes[:LIMITE_LISTE]]})

    def post(self, request, ident):
        projet = _projet_ou_404(ident)
        if not projet:
            return _erreur("introuvable", 404)
        moi = _moi(request)
        _autoriser(request, PROPOSITION, "_new", "create", _attributs(projet, request, auteurId=moi.sujet))
        try:
            champs = formulaires.proposition(_corps(request))
        except formulaires.Invalide as exc:
            return _erreur(str(exc), 400)
        if champs["type"] == "modifier_tache" and not projet.taches.filter(id=champs["cible_id"]).exists():
            return _erreur("cible_id : tâche inconnue dans ce projet", 400)
        # Idempotent : la meme proposition encore en attente n'est pas dupliquee.
        existante = projet.propositions.filter(auteur=moi, statut="soumise", type=champs["type"],
                                               cible_id=champs["cible_id"], contenu=champs["contenu"]).first()
        if existante:
            return Response(ser_proposition(existante), status=200)
        proposition = Proposition.objects.create(projet=projet, auteur=moi, **champs)
        courrier.proposition_soumise(proposition, _decideurs(projet))
        return Response(ser_proposition(proposition), status=201)


class Propositions(APIView):
    def get(self, request):
        """Les miennes, et celles que je peux decider (`a_decider`)."""
        moi = _moi(request)
        miennes = Proposition.objects.filter(auteur=moi).select_related("auteur", "decideur", "projet")
        a_decider = []
        for projet, role in _projets_visibles(request):
            attr = {"ownerId": projet.cree_par.sujet, "scopeNode": projet.scope_node, "brand": projet.brand,
                    "statut": projet.statut, "roleMembre": role, "auteurId": ""}
            if _permis(request, PROPOSITION, "*", "decide", attr):
                a_decider.extend(projet.propositions.filter(statut="soumise")
                                 .select_related("auteur", "decideur", "projet"))
        return Response({"miennes": [ser_proposition(p) for p in miennes[:LIMITE_LISTE]],
                         "a_decider": [ser_proposition(p) for p in a_decider[:LIMITE_LISTE]]})


class PropositionDecision(APIView):
    def post(self, request, pid):
        proposition = Proposition.objects.select_related("projet", "projet__cree_par", "auteur").filter(id=pid).first()
        if not proposition:
            return _erreur("introuvable", 404)
        projet = proposition.projet
        _autoriser(request, PROPOSITION, proposition.id, "decide",
                   _attributs(projet, request, auteurId=proposition.auteur.sujet))
        corps = _corps(request)
        decision = corps.get("decision")
        if decision not in ("acceptee", "refusee"):
            return _erreur("decision : acceptee ou refusee", 400)
        commentaire = corps.get("commentaire") or ""
        if not isinstance(commentaire, str) or len(commentaire) > 5000:
            return _erreur("commentaire : texte de 5000 caractères au plus", 400)
        if proposition.statut != "soumise":
            if proposition.statut == decision:
                return Response(ser_proposition(proposition))   # deja fait : no-op
            return _erreur("proposition déjà tranchée", 409)
        moi = _moi(request)
        with transaction.atomic():
            # Verrou d'ecriture : deux decisions simultanees ne s'appliquent pas deux fois.
            proposition = Proposition.objects.select_for_update().get(id=proposition.id)
            if proposition.statut != "soumise":
                return _erreur("proposition déjà tranchée", 409)
            if decision == "acceptee":
                try:
                    propositions.appliquer(proposition, moi)
                except propositions.Inapplicable as exc:
                    return _erreur(f"inapplicable : {exc}", 409)
            proposition.statut, proposition.decideur = decision, moi
            proposition.decidee_le, proposition.commentaire = timezone.now(), commentaire
            proposition.save()
        courrier.proposition_decidee(proposition)
        return Response(ser_proposition(proposition))


# ── Webhook GitHub ────────────────────────────────────────────────────

class WebhookGitHub(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not github.signature_valide(settings.GITHUB_WEBHOOK_SECRET, request.body,
                                       request.headers.get("X-Hub-Signature-256", "")):
            return _erreur("signature invalide", 403)
        if request.headers.get("X-GitHub-Event") != "push":
            return Response({"ignore": True})
        try:
            charge = json.loads(request.body or b"{}")
        except ValueError:
            return _erreur("corps JSON attendu", 400)
        nouveaux = github.traiter_push(charge if isinstance(charge, dict) else {})
        if nouveaux:
            github.rattacher_personnes()
        return Response({"nouveaux": nouveaux})


# ── Journal des erreurs ───────────────────────────────────────────────

class Erreurs(APIView):
    def get(self, request):
        _autoriser(request, JOURNAL, "*", "read", {"ownerId": request.user.id})
        try:
            nombre = min(max(int(request.query_params.get("nombre", 200)), 1), 500)
        except ValueError:
            nombre = 200
        lignes = Erreur.objects.all()
        if request.query_params.get("origine") in ORIGINES:
            lignes = lignes.filter(origine=request.query_params["origine"])
        return Response({"erreurs": [
            {"id": e.id, "le": e.le.isoformat(), "origine": e.origine, "utilisateur": e.owner,
             "nom": e.nom, "action": e.action, "message": e.message, "detail": e.detail,
             "contexte": e.contexte} for e in lignes[:nombre]]})

    def post(self, request):
        """Une erreur constatee par l'interface (delai, coupure, reponse en erreur)."""
        _autoriser(request, JOURNAL, "_new", "create", {"ownerId": request.user.id})
        corps = _corps(request)
        action = corps.get("action")
        if not isinstance(action, str) or not action.strip():
            return _erreur("action attendue", 400)
        erreurs.noter("portail", action.strip(), corps.get("message") or "",
                      detail=corps.get("detail") or "", user=request.user, contexte=corps.get("contexte"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        _autoriser(request, JOURNAL, "*", "delete", {"ownerId": request.user.id})
        ids = _corps(request).get("ids")
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return _erreur("ids attendus", 400)
        Erreur.objects.filter(id__in=ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
