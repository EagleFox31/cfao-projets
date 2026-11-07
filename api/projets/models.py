"""Modele de donnees du gestionnaire de projets.

Les personnes sont des identites de la plateforme (`sujet` = identifiant du
principal) : le module n'a pas de comptes propres. Le reste est le
vocabulaire habituel d'un gestionnaire de projets, avec la lecture GitHub
(depots, commits) et les propositions de modification.
"""
from django.db import models
from django.utils import timezone

STATUTS_PROJET = (
    ("propose", "Proposé"),
    ("en_cours", "En cours"),
    ("en_pause", "En pause"),
    ("termine", "Terminé"),
    ("archive", "Archivé"),
)
ROLES_MEMBRE = (
    ("chef", "Chef de projet"),
    ("contributeur", "Contributeur"),
    ("observateur", "Observateur"),
    ("demandeur", "Demandeur"),
)
STATUTS_TACHE = (
    ("a_faire", "À faire"),
    ("en_cours", "En cours"),
    ("bloque", "Bloqué"),
    ("fait", "Fait"),
)
TYPES_PROPOSITION = (
    ("modifier_projet", "Modifier le projet"),
    ("ajouter_tache", "Ajouter une tâche"),
    ("modifier_tache", "Modifier une tâche"),
    ("ajouter_membre", "Ajouter un membre"),
)
STATUTS_PROPOSITION = (
    ("soumise", "Soumise"),
    ("acceptee", "Acceptée"),
    ("refusee", "Refusée"),
)


PREFIXE_PRE_ENREGISTREMENT = "pre:"


class Personne(models.Model):
    """Une identite de la plateforme vue par le module.

    `sujet` est l'identifiant du principal (Keycloak `sub`, ou `id` d'un
    profil local). Le reste est un cache d'affichage rafraichi a chaque
    passage, plus `github_login` que la personne renseigne elle-meme.
    """
    sujet = models.CharField(max_length=128, unique=True)
    prenom = models.CharField(max_length=120, blank=True)
    nom = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    github_login = models.CharField(max_length=80, blank=True, db_index=True)
    # Autres adresses d'auteur de commit (poste de bureau, ancienne adresse...),
    # en minuscules : les commits sans login GitHub sont rattaches par elles.
    adresses_git = models.JSONField(default=list, blank=True)
    actif = models.BooleanField(default=True)
    vu_le = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("nom", "prenom")

    @staticmethod
    def sujet_pre_enregistre(email):
        """Sujet provisoire d'une fiche declaree avant la premiere connexion."""
        return f"{PREFIXE_PRE_ENREGISTREMENT}{email.strip().lower()}"

    @classmethod
    def depuis_principal(cls, principal):
        """Cree ou rafraichit la personne qui agit. Idempotent."""
        profil = principal.profil or {}
        # Seules les valeurs fournies par la plateforme ecrasent la fiche : une
        # fiche completee a la main (courriel, nom) n'est pas videe.
        champs = {k: v[:254] for k, v in (("prenom", profil.get("firstName") or ""),
                                          ("nom", profil.get("lastName") or ""),
                                          ("email", profil.get("email") or "")) if v}
        email = champs.get("email")
        if email and not cls.objects.filter(sujet=principal.id).exists():
            # Premiere connexion d'une personne declaree a l'avance : la fiche
            # (login GitHub, adresses, commits rattaches) prend son vrai sujet.
            cls.objects.filter(sujet=cls.sujet_pre_enregistre(email)).update(sujet=principal.id)
        personne, cree = cls.objects.get_or_create(sujet=principal.id, defaults=champs)
        if not cree and any(getattr(personne, k) != v for k, v in champs.items()):
            for k, v in champs.items():
                setattr(personne, k, v)
            personne.vu_le = timezone.now()
            personne.save(update_fields=[*champs, "vu_le"])
        return personne

    @property
    def nom_complet(self):
        return " ".join(p for p in (self.prenom, self.nom) if p) or self.email or self.sujet

    def __str__(self):
        return self.nom_complet


class Projet(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS_PROJET, default="en_cours")
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    # Avancement saisi a la main (0-100) ; sinon calcule depuis les taches.
    avancement_manuel = models.PositiveSmallIntegerField(null=True, blank=True)
    # Perimetre de la plateforme : noeud d'organisation et marque, pour Cerbos.
    scope_node = models.CharField(max_length=64, blank=True)
    brand = models.CharField(max_length=64, blank=True)
    cree_par = models.ForeignKey(Personne, on_delete=models.PROTECT, related_name="projets_crees")
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-modifie_le",)

    def avancement(self):
        """Part ponderee des taches faites, sauf avancement saisi a la main."""
        if self.avancement_manuel is not None:
            return self.avancement_manuel
        total = 0
        fait = 0
        for t in self.taches.all():
            total += t.poids
            if t.statut == "fait":
                fait += t.poids
        return round(100 * fait / total) if total else 0

    def __str__(self):
        return self.nom


class Membre(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="membres")
    personne = models.ForeignKey(Personne, on_delete=models.CASCADE, related_name="participations")
    role_membre = models.CharField(max_length=20, choices=ROLES_MEMBRE, default="contributeur")
    ajoute_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Une personne n'a qu'un role par projet : l'ajout est idempotent.
        constraints = [models.UniqueConstraint(fields=("projet", "personne"), name="membre_unique")]
        ordering = ("role_membre", "personne__nom")


class Tache(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="taches")
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS_TACHE, default="a_faire")
    assigne = models.ForeignKey(Personne, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="taches")
    echeance = models.DateField(null=True, blank=True)
    poids = models.PositiveSmallIntegerField(default=1)
    cree_par = models.ForeignKey(Personne, on_delete=models.PROTECT, related_name="taches_creees")
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("statut", "echeance", "id")


class Depot(models.Model):
    """Un depot GitHub suivi par un projet."""
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="depots")
    proprietaire = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    # Decouverte a la premiere synchronisation (jamais supposee « main »).
    branche_par_defaut = models.CharField(max_length=120, blank=True)
    toutes_branches = models.BooleanField(default=False)
    # Sous-dossier suivi dans un monorepo (vide = tout le depot) : seuls les
    # commits qui touchent ce chemin sont lus, et leurs stats s'y limitent.
    chemin = models.CharField(max_length=200, blank=True)
    # Nom d'une variable d'environnement portant un jeton propre a ce depot,
    # jamais le jeton lui-meme.
    jeton_variable = models.CharField(max_length=80, blank=True)
    derniere_synchro = models.DateTimeField(null=True, blank=True)
    derniere_erreur = models.CharField(max_length=500, blank=True)
    ajoute_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("projet", "proprietaire", "nom", "chemin"),
                                               name="depot_unique_par_projet")]
        ordering = ("proprietaire", "nom", "chemin")

    @property
    def plein_nom(self):
        return f"{self.proprietaire}/{self.nom}"

    @property
    def libelle(self):
        return f"{self.plein_nom}/{self.chemin}" if self.chemin else self.plein_nom

    def fichier_suivi(self, chemin_fichier):
        """Le fichier est-il sous le sous-dossier suivi (toujours vrai sans filtre) ?"""
        if not self.chemin:
            return True
        return chemin_fichier == self.chemin or chemin_fichier.startswith(self.chemin + "/")

    def __str__(self):
        return self.plein_nom


class Commit(models.Model):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="commits")
    sha = models.CharField(max_length=40)
    auteur_login = models.CharField(max_length=80, blank=True, db_index=True)
    auteur_nom = models.CharField(max_length=200, blank=True)
    auteur_email = models.CharField(max_length=254, blank=True)
    personne = models.ForeignKey(Personne, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="commits")
    date = models.DateTimeField(db_index=True)
    message = models.CharField(max_length=500, blank=True)
    branche = models.CharField(max_length=120, blank=True)
    additions = models.PositiveIntegerField(default=0)
    deletions = models.PositiveIntegerField(default=0)
    fichiers = models.PositiveIntegerField(default=0)
    # Liste bornee de {chemin, additions, deletions, statut}.
    fichiers_detail = models.JSONField(default=list, blank=True)
    url = models.URLField(blank=True)

    class Meta:
        # Le meme commit vu deux fois (deux synchros, webhook + synchro) ne fait qu'une ligne.
        constraints = [models.UniqueConstraint(fields=("depot", "sha"), name="commit_unique")]
        ordering = ("-date",)


class Proposition(models.Model):
    """Une modification proposee par quelqu'un qui n'a pas le droit de l'appliquer."""
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="propositions")
    auteur = models.ForeignKey(Personne, on_delete=models.PROTECT, related_name="propositions")
    type = models.CharField(max_length=30, choices=TYPES_PROPOSITION)
    cible_id = models.PositiveIntegerField(null=True, blank=True)
    contenu = models.JSONField(default=dict)
    motif = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS_PROPOSITION, default="soumise")
    decideur = models.ForeignKey(Personne, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="decisions")
    decidee_le = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    soumise_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-soumise_le",)


class Courrier(models.Model):
    """Journal des courriels : un par `correlation_id`, donc jamais deux envois."""
    correlation_id = models.CharField(max_length=160, unique=True)
    kind = models.CharField(max_length=60)
    destinataires = models.JSONField(default=list)
    sujet = models.CharField(max_length=300)
    statut = models.CharField(max_length=20, default="envoye")  # envoye | echec | ignore
    detail = models.CharField(max_length=500, blank=True)
    le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-le",)


class Erreur(models.Model):
    """Journal des erreurs applicatives (voir `erreurs.py`)."""
    le = models.DateTimeField(auto_now_add=True, db_index=True)
    origine = models.CharField(max_length=40)
    action = models.CharField(max_length=120, blank=True)
    owner = models.CharField(max_length=128, blank=True)
    nom = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    detail = models.TextField(blank=True)
    contexte = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-le",)
