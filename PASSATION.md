# PASSATION — cfao-projets

Journal en ajout seulement : chaque session ajoute une entrée datée à la fin.

## 2026-11-05 18:39 — Gestionnaire de projets web dockerisable

### Fait
- Module complet créé depuis zéro (référence cfao-comptes-rendus) : api/ (Django 5.1 + DRF : projets, membres, tâches, dépôts, commits, activité hebdo, propositions, courriels, journal des erreurs, auth standalone/local/integrated, Cerbos), web/ (React 18 + Vite 5, style des portails, pages Accueil/Projets/Projet/Propositions/Profil/Journal), gateway/ nginx, cerbos/ (policies + tests), compose dev + prod, Makefile, deploy.sh/.ps1.
- Lecture GitHub : synchronisation périodique (service synchro) + webhook push signé ; jeton par nom de variable d'environnement, jamais en base.
- CI : .github/workflows/ci.yml (appfactory impact analysis épinglé par SHA, gates api/web/cerbos/conteneurs) + release.yml.
- Docs : README.md, CLAUDE.md, docs/adr/0001, docs/engineering/lessons-learned.md.

### Vérifié (local)
- pytest API, vitest + build web, cerbos compile --tests : voir compte rendu de session ; à rejouer avec make test / make policy-test.

### Reste / à savoir
- Aucun commit encore : dépôt initialisé, premier commit à faire après relecture.
- Pas de dépôt GitHub distant ni de secrets CI (APPFACTORY_RELEASE_TOKEN) configurés.
- Mode integrated non testé contre un Keycloak réel (seulement tests unitaires du décodage de jeton).
