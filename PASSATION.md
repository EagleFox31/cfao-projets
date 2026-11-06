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

## 2026-11-05 22:40 — Implémentation du mode broker-app lancée en session séparée

- Décision du propriétaire : implémenter le broker (ADR 0002) plutôt que poser la clé App dans cfao-projets.
- Session « govern-broker-app » démarrée dans `C:\Users\lawry\Documents\Projetsppfactory` : PR dans Trigenys/appfactory (endpoint `/v1/github/installation-token`) et dans EagleFox31/appfactory-project-automation (mode `broker-app` du workflow de gouvernance).
- Ici : commit 899179d (ADR 0002) non poussé (push refusé par la permission de session). Secret `APPFACTORY_APP_PRIVATE_KEY` de cfao-projets toujours vide, à supprimer.
- Prochaine étape cfao-projets, une fois le worker déployé : passer `repository-governance.yml` en `authentication: broker-app` + variable `APPFACTORY_GOVERNANCE_BROKER_URL`, relancer plan → apply → plan.
- Correction : le dossier de la session est `C:/Users/lawry/Documents/Projets/appfactory` (ligne précédente mal encodée).

## 2026-11-06 13:29 — Session broker terminée (PR ouvertes), question « où est mon App »

- Session govern-broker-app : PR #144 (Trigenys/appfactory, endpoint jeton d'installation) et PR #188 (appfactory-project-automation, mode broker-app). Reste au propriétaire : déploiement du worker, allowlists, variable broker côté dépôt.
- Apps GitHub : `appfactory-bot` (org Trigenys, App ID 4935200, client Iv23lisXtkmMFl0u3hs5, administration:write, installée sur l'org) ≠ App de gouvernance d'AgenStart (client Iv23liGQ16lZLLIu0As1, propriétaire et slug non visibles par API : à retrouver dans github.com/settings/apps ou organizations/Trigenys/settings/apps). Point ouvert : quelle App porte la clé `GITHUB_PRIVATE_KEY` du worker (variable `GITHUB_APP_ID` dans Cloudflare).
- Application cfao-projets : dépôt https://github.com/EagleFox31/cfao-projets, local `make up` → http://localhost:8094.

## 2026-11-06 13:31 — Connexion locale

- Mode standalone (.env) : identifiants de `api/profils-locaux.json` (f-demo trainer, ki-demo learner+ki, a-demo learner, c-demo team_manager, s-demo superadmin), aucun mot de passe. Accès http://localhost:8094.

## 2026-11-06 13:32 — Connexion locale (correctif)

- Identifiants de connexion = champ `identifiant` de `api/profils-locaux.json` (admin.demo, chef.demo, formateur.demo, ki.demo, apprenant.demo), mot de passe quelconque en standalone. L'entrée précédente citait les `id` internes par erreur.

## 2026-11-06 13:39 — Mot de passe en standalone

- Le formulaire exige un champ non vide mais le serveur ne le vérifie pas en standalone : n'importe quelle valeur (ex. `demo`) passe.

## 2026-11-06 13:46 — Comptes CFAO et en-têtes de sections de l'accueil

- `api/profils-locaux.json` : 4 comptes ajoutés (identifiant = adresse e-mail) : jakaa-ext@cfao.com et ibmbowou-ext@cfao.com (Ibrahim Mbowou, dev) en `build_team`, aybokally@cfao.com (coordinateur) en `team_manager`, lgonin@cfao.com (directeur du centre) en `center_director`. Périmètre `CMR` / toyota / motors supposé, prénoms inconnus mis en initiale : à corriger si besoin. Les profils sont cuits dans l'image api : `docker compose up -d --build api` après modification (fait, 4 connexions → 200).
- Accueil : nouveau composant `web/src/components/portail/SectionHead.jsx` (icône SVG + eyebrow + titre, piloté par la config `SECTIONS` d'`Accueil.jsx`, plus de libellés en dur) ; la section Avancement est désormais dans une carte `pj-panneau` comme la section GitHub. CSS : eyebrow en inline-flex avec icône (`pj.css`). Build web et gateway reconstruits, vitest 12/12.
- Reste : nouvelles icônes à ajouter dans `ICONES` de SectionHead si d'autres pages adoptent le composant (Projet.jsx, Projets.jsx ont encore leurs titres en dur).

## 2026-11-06 13:53 — Projets en cours rendus en PvCard

- Accueil : chaque projet en cours est une `PvCard` (image, statut en kicker, titre, synthèse `noteProjet`, jauge en enfant, CTA « Ouvrir le projet ») dans un `PortalStaggerGrid`, comme les cartes du haut ; plus de `pj-panneau` ni de `Link` maison. `PvCard` accepte désormais `children` (rendu après `meta`). Vérifié dans le navigateur sur http://localhost:8094, vitest 12/12, build OK, gateway reconstruit.

## 2026-11-06 13:58 — Liaison GitHub : état des lieux

- Un projet suit des dépôts via Projet → Paramètres → « organisation/depot » (+ nom de variable de jeton, optionnel, défaut `GITHUB_TOKEN`, vide dans `.env`). La synchro lit `/repos/{owner}/{repo}/commits` du dépôt entier : **pas de filtre par sous-dossier**.
- Dépôts vus côté EagleFox31 : `cfaoacademy` (public, monorepo : cfao-academy-mail, cfao-comptes-rendus, cfao-core, cfao-needs, cfao-operations, frontend, gateway, keycloak…, pas de dossier planning), `cfao-ops` (privé, jeton requis), `cfao-projets`, `cfao-suivi-commerciaux-pr-vl`, `academy` (privé).
- Prochaine étape probable : ajouter un champ `chemin` (sous-dossier) sur Depot + filtre `path` sur l'appel commits et attribution des fichiers, pour un projet par module du monorepo.

## 2026-11-06 14:04 — Dépôts suivis : filtre par sous-dossier (monorepo)

- `Depot.chemin` (migration `0002_depot_chemin`, unicité projet+owner+nom+chemin) : la synchro passe `path` à l'API commits, ne garde que les fichiers sous le chemin (stats recalculées dessus) et ignore un commit hors dossier (webhook inclus). Formulaire : champ « Sous-dossier suivi », validé côté API (pas de `..`, d'espace ni d'antislash). Sérialiseur : `chemin`, `libelle`, `url` vers le dossier.
- Vérifié : pytest 87/87 (nouveau test `test_un_sous_dossier_filtre_les_commits_et_leurs_stats`), vitest 12/12, build web, compose config, migration appliquée en conteneur, santé 200. Commit 3df0ad2 poussé.
- Usage : un projet par module avec `EagleFox31/cfaoacademy` + chemin `cfao-comptes-rendus`, `cfao-academy-mail`, `cfao-needs`, `cfao-core`, `cfao-operations` ; `cfao-ops` (privé) à part avec une variable de jeton. Une synchro manuelle lance la première lecture.

## 2026-11-06 16:38 — Jeton GitHub vérifié, fiche projet façon article du portail

- Jeton : `GITHUB_TOKEN` chargé dans le conteneur api (valeur jamais affichée), accès au dépôt privé `cfao-ops` confirmé.
- Nouveau gabarit `web/src/components/FicheDetail.jsx` calqué sur `frontend/src/pages/Article.jsx` du portail
  (feuille centrée `pj-fiche`, croix `pj-fiche-fermer` = retour historique sinon `repli`, entête étiquette / pastilles méta /
  titre / chapeau, corps avec onglets). Styles `pj-fiche-*` en fin de `web/src/styles/pj.css`.
- `web/src/pages/Projet.jsx` utilise `FicheDetail` (statut en étiquette, pastilles membres / rôle / jauge, description en chapeau).
  Les états erreur / chargement restent sur `PageModule`.
- Vérifié : vitest 12/12, `npm run build`, gateway reconstruit, croix testée dans le navigateur (`/projets/1` → `/projets`).

## 2026-11-06 17:05 — Dépôt MEDACAP2026 rattaché, zébrage portail neutralisé

- Projet 1 (MEDACAP84) : dépôt `EagleFox31/MEDACAP2026` rattaché via l'UI, synchro OK (102 commits lus, branche `main`).
  Aucun dépôt n'était lié : le jeton donne l'accès, chaque projet déclare ses dépôts dans Paramètres.
- Bug d'affichage : le thème portail applique `section:nth-of-type(2n)` (fond sombre + h2 blanc) à toute 2e section ;
  la 2e `pj-panneau` d'un onglet devenait illisible. Neutralisé en fin de `pj.css` (fond paper, titres ink) pour `.pj-page`
  et `.pj-fiche-page`, comme le portail le fait pour `.article-sheet section`.
- À surveiller : après la première synchro via le bouton, `derniere_synchro` est resté nul en base alors que les commits
  étaient lus ; une synchro depuis le shell l'a renseigné et les suivantes (bouton, service) l'affichent. Non reproduit.
- Prochaine étape côté usage : créer un projet par module cfaoacademy et rattacher `EagleFox31/cfaoacademy` avec le
  sous-dossier (ex. `cfao-comptes-rendus`), puis `cfao-ops`.
