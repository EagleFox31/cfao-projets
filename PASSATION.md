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

## 2026-11-06 17:16 — Projets CFAO créés avec leurs dépôts, liste Projets en cartes

- Projets créés en base (idempotent, `cree_par` = admin.demo, admin membre `chef`), chacun avec son dépôt rattaché et synchronisé :
  CFAO Comptes rendus (`cfaoacademy/cfao-comptes-rendus`, 60 commits), CFAO Mail (`cfao-academy-mail`, 4), CFAO Core (`cfao-core`, 5),
  CFAO Needs (`cfao-needs`, 29), CFAO Operations (`cfao-operations`, 0), Portail CFAO Academy (`frontend`, 127), CFAO Ops (`EagleFox31/cfao-ops`, 2).
  Pas de module « planning » dans cfaoacademy. Avec MEDACAP84 : 8 projets.
- Page `/projets` : le tableau est remplacé par la grille de cartes du portail (`PortalStaggerGrid` + `PvCard`), partagée avec l'accueil
  via `web/src/components/projet/CarteProjet.jsx` (statut en kicker, note membres/tâches/propositions/échéance, jauge d'avancement).
  Filtres par statut, états vide/erreur et dialogue de création inchangés. Vitest 12/12, build OK, gateway reconstruit, vérifié sur 8094.
- Commits locaux non poussés : 1222548 (zébrage) + celui-ci.

## 2026-11-06 17:28 — Lecture de toutes les branches des dépôts

- Constat : les 8 dépôts étaient rattachés mais lus sur `main` seulement ; le travail de la semaine est sur des branches
  de fonctionnalité (cfaoacademy : `feature/04-5-rapports-formateur`, `feature/15-1-cerbos-pdp-unique`), d'où « 0 commit ».
- Données : `toutes_branches` activé sur les 8 dépôts, `derniere_synchro` remise à nul pour relire la fenêtre initiale (90 j),
  resynchro : +59 commits (Comptes rendus 60 → 97). Semaine 45 de Comptes rendus : 5 commits, 2 contributeurs.
- Piège : activer « toutes branches » après coup ne rattrape rien, la synchro repart de `derniere_synchro - 1 h`.
  Le drapeau n'est réglable qu'à la création ; le formulaire coche désormais « toutes les branches » par défaut.
- Contributeurs « non rattaché » : aucune personne du module ne porte les logins EagleFox31 / MbowouIbrah (mode autonome,
  seul admin.demo existe). Se résout avec les identités plateforme ou le login GitHub sur la fiche personne.
- Dépôts CFAO non suivis repérés : `cfao-suivi-commerciaux-pr-vl`, `planificateur` (privé) ; en attente de décision.

## 2026-11-06 17:34 — Projet Suivi commerciaux créé

- Projet 9 « CFAO Suivi commerciaux PR et VL » créé (admin.demo chef), dépôt `EagleFox31/cfao-suivi-commerciaux-pr-vl`
  rattaché en toutes branches, synchro OK (2 commits, `main`). 9 projets au total.
- `planificateur` écarté : application de planning de réunions pour une congrégation, sans lien avec CFAO.
- État : 3 commits locaux non poussés sur main (1222548, 8f36629, def5d6b). Prochaine étape : push sur accord.

## 2026-11-07 03:39 — Push sur main

- 4 commits poussés sur origin/main (zébrage, liste en cartes, toutes branches par défaut, passation). Rien en attente localement.
- Prochaine étape : rattacher les logins GitHub aux personnes (contributeurs « non rattaché »).

## 2026-11-07 03:48 — Personnes déclarées avant connexion, adresses de commit secondaires

- `Personne.adresses_git` (migration 0003) : autres adresses d'auteur de commit (poste du bureau, ancienne adresse),
  utilisées par `_personne_pour` et `rattacher_personnes`. Réglables sur la page Profil et via `PATCH personnes/moi`.
- Commande idempotente `manage.py declarer_personne --email … [--prenom --nom --github --adresse-git …]` :
  crée une fiche au sujet provisoire `pre:<email>` ; à la première connexion plateforme avec le même e-mail,
  `depuis_principal` lui donne le vrai sujet (pas de doublon, commits conservés). Tests : `test_personnes_git.py`.
- Données locales : 2 personnes déclarées (dev 1 = la propriétaire, login EagleFox31 + adresse du poste MEDACAP + adresse
  Trigenys ; Ibrahim Mbowou, login MbowouIbrah + 3 adresses). Tous les commits rattachés sauf 3 de dependabot.
  E-mails réels gardés en base seulement (dépôt public). Nom de la propriétaire non renseigné : viendra de la plateforme.
- Vérifs : pytest 92 passed, vitest 12, build OK, compose config OK, api/synchro/gateway reconstruits.

## 2026-11-07 03:59 — Projet CFAO Planning

- Le dossier `cfao-planning` de cfaoacademy n'existe que sur la branche `feature/15-1-cerbos-pdp-unique` (pas sur main), d'où l'oubli.
- Projet 10 « CFAO Planning » créé, dépôt cfaoacademy sous-dossier `cfao-planning`, toutes branches : 2 commits, rattachés. 10 projets.
- Leçon : chercher un module sur toutes les branches, pas seulement la branche par défaut.
- État : 1 commit local non poussé (650e068) + cette entrée.

## 2026-11-07 04:09 — Push sur main

- Commits poussés sur origin/main (adresses de commit secondaires, déclaration de personnes, projet CFAO Planning). Rien en attente.
- 10 projets, tous liés à GitHub ; commits attribués aux 2 développeurs sauf dependabot.

## 2026-11-09 08:52 — Projet CFAO Edge

- L'app n'était pas arrêtée (5 services actifs, santé 200) : seul le panneau navigateur était fermé.
- Projet « CFAO Edge » créé en base : dépôt EagleFox31/cfaoacademy, chemin `edge`, toutes branches (le dossier n'existe que sur feature/15-1-cerbos-pdp-unique). 9 commits synchronisés, tous attribués.
- 11 projets au total. Changement de données seulement, rien à commiter hors cette entrée.

## 2026-11-09 11:37 — Accueil vérifié, fuite d'adresses signalée

- Cartes « Où en sont vos projets » vérifiées en base : 11 projets en cours, 0 proposition, semaine 2026-W46 = 1 commit d'Ibrahim (cfao-comptes-rendus, +142/−57). Données réelles ; photos illustratives.
- `.claude/launch.json` ajouté (aperçu attaché à :8094), non commité.
- À trancher par la propriétaire : `api/profils-locaux.json` est suivi par git dans un dépôt PUBLIC avec 4 adresses @cfao.com réelles (depuis 6105e10). Proposé : détracker + exemple `*.demo` ; option purge d'historique ou dépôt privé.

## 2026-11-09 11:55 — Synchro : commits poussés en retard

- Cause : la synchro relisait depuis `derniere_synchro - 1h` (filtre `since` GitHub sur la date du commit) ; un commit daté avant la dernière passe mais poussé après était perdu (2 commits d'Ibrahim du 9/11 manquaient).
- Correctif : relecture de `SYNCHRO_RECOUVREMENT_HEURES` (défaut 72, `.env.example`), sha déjà connus ignorés ; test de non-régression dans `test_github.py`. 93 tests verts ; api + synchro reconstruits ; commits rattrapés.
- Toujours à trancher : `api/profils-locaux.json` (adresses @cfao.com réelles dans le dépôt public).

## 2026-11-09 12:26 — Push sur main

- 5c888e1 (relecture 72 h de la synchro) poussé sur origin/main.
- Reste à trancher : `api/profils-locaux.json` (adresses réelles, dépôt public) ; `.claude/launch.json` non commité.

## 2026-11-09 12:53 — Propositions depuis les issues GitHub

- Les propositions viennent de l'app **et** des issues GitHub ouvertes : chaque issue devient une proposition « ajouter une tâche » (source `github`, référence `owner/depot#n`, une seule fois, contrainte unique), importée à chaque synchro. Migration 0004.
- Règle monorepo : dépôt suivi en entier → toutes les issues ; sous-dossier (`chemin`) → seulement l'étiquette réglée dans Paramètres (« Étiquette des issues à importer »), sinon rien.
- Un jeton sans droit sur les issues n'empêche plus la lecture des commits : avertissement dans `derniere_erreur`. Cas réel : EagleFox31/cfao-ops répond 403 sur /issues.
- Vérifié : 96 tests API, `docker compose config -q`, synchro réelle sans erreur bloquante, santé 200. `make policy-test` non lancé (pas de make ; aucune règle Cerbos modifiée).
- Reste : aucune issue ouverte aujourd'hui ; régler les étiquettes par module cfaoacademy ; décision sur `api/profils-locaux.json` toujours ouverte.

## 2026-11-09 12:55 — Push sur main

- 44738b3 (propositions depuis les issues GitHub) poussé sur origin/main.
- Reste à trancher : `api/profils-locaux.json` (adresses réelles, dépôt public) ; `.claude/launch.json` non commité.

## 2026-11-09 13:07 — Auteurs de commits rattachés comme membres

- `github.rattacher_auteurs(projet)` : chaque auteur reconnu (Personne liée par login ou adresse) devient contributeur, appelé à chaque synchro et à chaque webhook push. Idempotent : rôle existant conservé, bots et logins inconnus ignorés.
- Rattrapage fait : 14 membres ajoutés sur les 11 projets (J. Akaa partout, I. Mbowou sur Portail, Comptes rendus, MEDACAP84) ; second passage = 0.
- Vérifié : 97 tests API, santé 200. Commit local, non poussé.
- Reste : le chef de chaque projet est toujours le compte Démo, à désigner à la main ; tâches toujours vides ; `api/profils-locaux.json` à trancher.

## 2026-11-09 13:09 — Push sur main

- 6ff6de0 (auteurs de commits rattachés comme contributeurs) poussé sur origin/main.
- Reste : désigner le vrai chef de chaque projet (compte Démo partout) ; tâches vides ; `api/profils-locaux.json` à trancher ; `.claude/launch.json` non commité.

## 2026-11-09 14:24 — En-tête sans logos de marques

- `PortalHeader.jsx` : bloc des logos de marques (repris du portail) retiré ; sans objet pour un gestionnaire de projets. Build, 12 tests vitest, page vérifiée (0 logo). `PortalStickyBar.jsx` et `portalCardMedia.js` sont du code mort non importé, laissé tel quel.
- En cours : réécriture des descriptions des 11 projets (claires et disant leur importance), à partir des README des dépôts.

## sur — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## les — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## README — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## et — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## docs — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## des — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## dépôts. — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## CFAO — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## Operations — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## reste — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## « — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## à — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## préciser — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## », — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## car — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## le — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## code — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## na pas encore de fonction métier.\n- `pj.css` : `white-space: pre-line` sur le chapeau de fiche et les `dd` pour afficher les sauts de ligne. Build OK, vérifié sur /projets/11.\n- Commits locaux non poussés : 0a39df5 (logos) et celui-ci.\n — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## 2026-11-09 14:55 — Descriptions des projets réécrites

- Les 11 descriptions (en base, pas dans le code) sont réécrites en langage simple, en deux temps : à quoi sert le projet, puis « Importance : … ». Elles sappuient
## 2026-11-09 14:57 — Push sur main

- 0a39df5 (logos retirés) et d75bb28 (sauts de ligne des descriptions) poussés sur origin/main.
- Reste : désigner les chefs de projet (compte Démo partout) ; tâches vides ; `api/profils-locaux.json` à trancher ; `.claude/launch.json` non commité.

## 2026-11-09 15:27 — Rôles : libellés Pilote et Commanditaire

- Libellés affichés : chef → « Pilote », demandeur → « Commanditaire » (codes inchangés, Cerbos intact). Migration 0005 (choices seulement), textes API/web/README alignés, légende des rôles sous l’équipe.
- Vérifié : 97 tests, build web, migration appliquée, bundle servi.
- Reste : désigner le vrai pilote de chaque projet (Démo partout) ; tâches vides ; `api/profils-locaux.json` ; `.claude/launch.json` non commité.

## 2026-11-10 16:12 — Passerelle : resolution dynamique de l API

- 502 apres reconstruction de l API corrige : nginx resout `api` a chaque requete (`resolver 127.0.0.11`). Verifie : api recree seul, sante 200 sans toucher la passerelle. Lecon ajoutee dans `docs/engineering/lessons-learned.md`.
