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

## 2026-11-05 18:52 — Dépôt GitHub créé, CI bloquée par la facturation

- Premier commit `4080031` sur `main`, poussé vers https://github.com/EagleFox31/cfao-projets (privé).
- Identité git locale du dépôt : EagleFox31 (adresse noreply GitHub), comme cfao-ops.
- Correctif avant commit : origines de test figées dans `api/config/settings/test.py` (la suite ne dépend plus du `.env` du poste) ; leçon dans lessons-learned.
- Les workflows CI et Release ont été refusés par GitHub : « recent account payments have failed or your spending limit needs to be increased » (Billing & plans du compte EagleFox31). Rien à corriger côté dépôt ; relancer avec `gh run rerun <id>` ou `gh workflow run ci.yml` une fois la facturation régularisée.
- Prochaine étape : régulariser la facturation, relancer la CI, puis protéger `main` (appfactory repository governance, plan puis apply).

## 2026-11-05 19:01 — Release sans secret PAT

- `release.yml` n'utilise plus `APPFACTORY_RELEASE_TOKEN` : `release_token` est optionnel dans le workflow appfactory, `GITHUB_TOKEN` suffit. Effet : la PR de release ne déclenche pas la CI (relance par `workflow_dispatch`).
- L'auth OIDC `broker-user` d'appfactory concerne `reusable-project-automation.yml` (board GitHub Project), pas encore adopté ici ; le broker hébergé annonce les dépôts publics du compte, à vérifier pour ce dépôt privé avant adoption.
- CI toujours bloquée par la facturation du compte GitHub.
