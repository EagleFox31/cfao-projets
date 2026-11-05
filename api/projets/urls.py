"""Routes explicites, sans barre finale (convention des modules de la plateforme)."""
from django.urls import path

from . import views

urlpatterns = [
    path("apercu/sante", views.Sante.as_view()),
    path("pj-donnees/connexion", views.Connexion.as_view()),
    path("pj-donnees/session", views.Session.as_view()),
    path("pj-donnees/deconnexion", views.Deconnexion.as_view()),
    path("pj-donnees/referentiel", views.Referentiel.as_view()),
    path("pj-donnees/erreurs", views.Erreurs.as_view()),
    path("pj-donnees/personnes", views.Personnes.as_view()),
    path("pj-donnees/personnes/moi", views.PersonneMoi.as_view()),
    path("pj-donnees/personnes/<int:ident>", views.PersonneDetail.as_view()),
    path("pj-donnees/projets", views.Projets.as_view()),
    path("pj-donnees/projets/<int:ident>", views.ProjetDetail.as_view()),
    path("pj-donnees/projets/<int:ident>/membres", views.Membres.as_view()),
    path("pj-donnees/projets/<int:ident>/membres/<int:mid>", views.MembreDetail.as_view()),
    path("pj-donnees/projets/<int:ident>/taches", views.Taches.as_view()),
    path("pj-donnees/projets/<int:ident>/taches/<int:tid>", views.TacheDetail.as_view()),
    path("pj-donnees/projets/<int:ident>/depots", views.Depots.as_view()),
    path("pj-donnees/projets/<int:ident>/depots/<int:did>", views.DepotDetail.as_view()),
    path("pj-donnees/projets/<int:ident>/depots/<int:did>/synchroniser", views.DepotSynchroniser.as_view()),
    path("pj-donnees/projets/<int:ident>/activite", views.ProjetActivite.as_view()),
    path("pj-donnees/projets/<int:ident>/propositions", views.ProjetPropositions.as_view()),
    path("pj-donnees/activite/semaine", views.ActiviteSemaine.as_view()),
    path("pj-donnees/propositions", views.Propositions.as_view()),
    path("pj-donnees/propositions/<int:pid>/decision", views.PropositionDecision.as_view()),
    path("pj-donnees/webhooks/github", views.WebhookGitHub.as_view()),
]
