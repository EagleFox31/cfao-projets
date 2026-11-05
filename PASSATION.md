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

## 2026-11-05 20:17 — Gouvernance du dépôt préparée (plan non lancé)

- CI relancée : toujours refusée par GitHub (facturation Actions du compte). Aucun run n'a encore exécuté un job.
- Ajout de `.github/project-config.json` (governance solo) et `.github/workflows/repository-governance.yml` (appfactory, auth `github-app`, manuel, épinglé SHA v1). Aucun dépôt du compte n'utilise encore la gouvernance : la voie zéro PAT demande une action unique du propriétaire (enregistrer/installer l'App appfactory, puis variable `APPFACTORY_APP_CLIENT_ID` + secret `APPFACTORY_APP_PRIVATE_KEY` sur ce dépôt). Sans cela, ne pas lancer le workflow.
- Verrous : facturation GitHub ; identifiants App appfactory.
- Prochaine étape : une fois débloqué, `plan` → relecture → `apply` → `plan` (NO-OP) ; puis CI verte sur main.

## 2026-11-05 20:24 — Dépôt public, CI exécutée

- Dépôt passé en public (aucun secret versionné, scan fait) : les minutes Actions ne dépendent plus de la facturation.
- Premier run réel : api, web, cerbos OK ; job conteneurs corrigé (variables obligatoires du compose de prod fournies à l'étape `config`).
- Prochaine étape : CI verte sur main, puis gouvernance appfactory (App à installer par le propriétaire, ou broker public si pris en charge pour la gouvernance).

## 2026-11-05 20:40 — Plan de gouvernance : workflow valide, clé App manquante

- Variable `APPFACTORY_APP_CLIENT_ID` posée sur ce dépôt (même App que AgenStart). Le `concurrency` du workflow appelant retiré (porté par le réutilisable) : le run démarre désormais.
- Le `plan` s'arrête à « Validate governance authentication » : secret `APPFACTORY_APP_PRIVATE_KEY` absent sur cfao-projets (présent sur AgenStart, non lisible). À faire par le propriétaire : installer l'App appfactory sur cfao-projets et copier le secret.
- Ensuite : relancer `plan` (workflow_dispatch), relire, `apply`, `plan` → NO-OP.

## 2026-11-05 20:55 — Plan relancé : toujours bloqué par la clé App

- Run plan 42098267663 : échec à « Validate governance authentication », secret `APPFACTORY_APP_PRIVATE_KEY` absent. Un secret Actions n'est pas relisible par API : impossible de le copier depuis AgenStart. L'installation de l'App sur le dépôt n'est pas faisable avec le jeton `gh` (endpoints réservés aux jetons d'App) : action UI du propriétaire (github.com/settings/installations).
- Commande une fois la clé en main : `gh secret set APPFACTORY_APP_PRIVATE_KEY -R EagleFox31/cfao-projets < chemin/cle.pem`, puis relancer le plan.

## 2026-11-05 22:24 — Tour d'horizon des dépôts qui réutilisent appfactory

- Dépôts consommateurs : AgenStart, agentshield-ai, Trigenys-Insight, atelier2026, agenStudio, xeption237 → `reusable-project-automation.yml` en `authentication: broker-user` (OIDC, variable `APPFACTORY_PROJECT_BROKER_URL`, zéro secret), plus `readme-quality` (Trigenys/appfactory). Seul AgenStart utilise `reusable-repository-governance.yml`, et avec la même clé App (`github-app`).
- Le workflow de gouvernance n'accepte que `token` ou `github-app` ; la doc `project-github-app-user-onboarding.md` dit explicitement que le broker OIDC est séparé de la gouvernance (jeton d'installation requis). Le blocage sur `APPFACTORY_APP_PRIVATE_KEY` est donc structurel, pas un choix de cfao-projets.
- Commande PowerShell (le `<` de bash n'existe pas) : `Get-Content -Raw chemin\cle.pem | gh secret set APPFACTORY_APP_PRIVATE_KEY -R EagleFox31/cfao-projets`.
- Prochaine étape possible sans secret : brancher le board Projects comme les frères (`project-automation.yml` broker-user + section `project` dans `.github/project-config.json`, variable broker URL copiée d'AgenStart).

## 2026-11-05 22:36 — Gouvernance : ne pas dupliquer la clé App, proposition broker

- Demande : vérifier si l'authentification de gouvernance peut passer par le broker OIDC AppFactory au lieu d'une clé App par dépôt.
- Constat : broker `appfactory-project-token-broker` = jetons utilisateur OAuth seulement (pas de clé d'App). L'API `appfactory-api` (Trigenys/appfactory) détient déjà la clé (`GITHUB_PRIVATE_KEY`), signe des JWT d'App et émet des jetons d'installation restreints (motif `seo-github-broker`), avec auth OIDC par liste blanche repo+workflow_ref.
- Proposition écrite : `docs/adr/0002-gouvernance-par-jeton-d-installation-brokere.md` (mode `broker-app`, endpoint `/v1/github/installation-token`, jeton 1 h limité au dépôt et à `administration:write`, zéro secret côté dépôt).
- Attention : le secret `APPFACTORY_APP_PRIVATE_KEY` de cfao-projets a été posé **vide** (fichier inexistant dans le pipe PowerShell) ; à écraser ou supprimer. Aucune clé n'a été générée.
- Prochaine étape : décision du propriétaire (implémenter le mode broker dans appfactory, ou poser la clé comme AgenStart en transitoire).
