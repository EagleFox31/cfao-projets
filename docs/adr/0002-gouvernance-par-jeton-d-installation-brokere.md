# ADR 0002 — Gouvernance du dépôt par jeton d'installation brokeré (sans clé App par dépôt)

Date : 2026-11-05 · Statut : proposé

## Contexte

La gouvernance AppFactory (`reusable-repository-governance.yml`) n'accepte que deux
modes : `token` (PAT fine-grained) ou `github-app` (clé privée de l'App dans le
secret `APPFACTORY_APP_PRIVATE_KEY` de chaque dépôt consommateur). Seul AgenStart
l'utilise aujourd'hui, avec la clé dupliquée dans ses secrets.

Les autres dépôts (agentshield-ai, Trigenys-Insight, atelier2026, agenStudio,
xeption237, AgenStart) consomment AppFactory **sans secret** via le broker OIDC
`appfactory-project-token-broker` (`authentication: broker-user`), mais ce broker
ne sait produire qu'un **jeton utilisateur OAuth** (fournisseur `oauth-app`) : il
ne détient pas de clé d'App et ne peut pas émettre de jeton d'installation. La
documentation AppFactory le dit explicitement : ce flux est séparé de la
gouvernance, qui exige un jeton d'installation `Administration: write`.

En revanche, l'API AppFactory (`Trigenys/appfactory`, worker `appfactory-api`)
détient déjà la clé privée de l'App comme secret Cloudflare (`GITHUB_PRIVATE_KEY`,
`GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`), sait signer un JWT d'App
(`createGitHubAppJwt`) et émettre des jetons d'installation restreints à un dépôt
et à des permissions précises (motif `seo-github-broker` : `repositories:[...]`,
`permissions:{...}`). Elle authentifie ses appelants par OIDC GitHub avec une liste
blanche `repository` + `workflow_ref` (`src/auth.ts`).

Un compte utilisateur GitHub (EagleFox31) n'a pas de secrets partagés entre dépôts :
sans broker, la seule voie est la copie de la clé dans chaque dépôt.

## Décision proposée

Ajouter un troisième mode `authentication: broker-app` à la gouvernance, servi par
un endpoint de jeton d'installation dans un worker AppFactory qui détient déjà la
clé (de préférence `appfactory-api`, sinon le broker Projects étendu).

### Endpoint `POST /v1/github/installation-token`

1. Reçoit le JWT OIDC du job (audience `appfactory-governance`), valide signature,
   `iss`, `aud`, expiration.
2. Exige `job_workflow_ref` dans une liste blanche **épinglée par SHA** du workflow
   réutilisable de gouvernance (même mécanisme que `ALLOWED_JOB_WORKFLOW_REFS`), et
   `repository_owner` dans une liste blanche de comptes (EagleFox31, Trigenys). Le
   dépôt provient des claims vérifiés, jamais du corps de la requête.
3. Résout l'installation du dépôt avec le JWT d'App :
   `GET /repos/{owner}/{repo}/installation`. Un 404 renvoie une erreur actionnable
   « App non installée sur ce dépôt » (c'est aussi le contrôle d'installation).
4. Émet `POST /app/installations/{id}/access_tokens` avec
   `repositories:[repo]` et `permissions:{administration:"write"}` uniquement.
5. Retourne le seul jeton (durée 1 h) ; le workflow le masque et le révoque en fin
   de job (`DELETE /installation/token`).

### Côté workflow réutilisable

`reusable-repository-governance.yml` : nouvelle valeur `broker-app`, nouvel input
`broker_url`, `permissions: id-token: write` sur le job, échange OIDC avant l'étape
de gouvernance, puis passage du jeton masqué au même input `governance-token`. Le
cœur de la gouvernance ne change pas (même contrat qu'avec `github-app`).

### Côté dépôt consommateur

Une variable `APPFACTORY_GOVERNANCE_BROKER_URL`, aucun secret. Même modèle que
`APPFACTORY_PROJECT_BROKER_URL` pour le board.

## Garanties

- La clé privée reste au seul endroit où elle est déjà : secret Cloudflare du worker.
  Aucun dépôt ne la reçoit ; `APPFACTORY_APP_PRIVATE_KEY` devient inutile.
- Jeton à durée courte, limité au dépôt appelant et à `Administration: write`.
- Frontière d'accès inchangée : l'App doit être installée sur le dépôt (sélection
  d'installation = frontière externe), le `workflow_ref` épinglé = frontière interne.
- Rotation de clé en un point (le worker) au lieu de N dépôts.
- Secrets existants non touchés : aucun changement au broker OAuth ni au secret
  d'AgenStart tant que la migration n'est pas validée (`plan` identique avant/après).

## Alternatives écartées

- Dupliquer la clé dans chaque dépôt (état actuel) : N copies à faire tourner, et
  c'est précisément ce que la proposition veut éviter.
- Jeton utilisateur OAuth via le broker existant : un jeton utilisateur n'est pas
  un jeton d'installation ; les rulesets exigent `Administration: write` sur le
  dépôt et le broker ne demande que `project public_repo`.
- Secret d'organisation : indisponible pour les dépôts d'un compte utilisateur.

## Prérequis à confirmer avant implémentation

- L'App derrière `APPFACTORY_APP_CLIENT_ID` (`Iv23liGQ16lZLLIu0As1`) est-elle celle
  dont `appfactory-api` détient la clé ? Sinon, le worker porte une seconde clé
  (toujours une seule copie, côté Cloudflare).
- L'App est-elle installée sur le compte EagleFox31 avec « tous les dépôts » ou
  « dépôts sélectionnés » ? Dans le second cas, cfao-projets doit être ajouté une
  fois (UI), avec ou sans broker.

## Mesure transitoire pour cfao-projets

Tant que le mode `broker-app` n'existe pas : soit attendre, soit poser le secret
comme AgenStart (le secret vide posé par erreur le 2026-11-05 doit être écrasé ou
supprimé : `gh secret delete APPFACTORY_APP_PRIVATE_KEY -R EagleFox31/cfao-projets`).
