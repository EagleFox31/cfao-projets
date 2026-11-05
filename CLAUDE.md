# cfao-projets — conventions du dépôt

Gestionnaire de projets, module détachable CFAO Academy. Référence de style et
de structure : `cfao-comptes-rendus` dans le dépôt cfaoacademy.

## Stack
- `api/` Django 5.1 + DRF, Python 3.12, tests pytest (`cd api && python -m pytest -q`, venv `api/.venv`).
- `web/` React 18 + Vite 5, vitest (`npm test`), build `npm run build`. Dev : 5178 → API 5175.
- `gateway/` nginx qui sert `web/dist` et proxifie `/apercu`, `/pj-donnees`.
- `cerbos/` policies + tests (`make policy-test`), image 0.40.0, défaut refus.
- PostgreSQL 16 ; services compose : db, cerbos, api, synchro, gateway (port `PJ_PORT`=8094).

## Préfixes et contrats
- Env `PJ_*`, CSS `pj-*` (`web/src/styles/pj.css`), routes `/apercu/sante` et `/pj-donnees/...`, cookie `cfao_pj_session`.
- Réponses JSON ; erreurs `{ "erreur": "..." }` ; listes enveloppées (`{projets: []}`).
- Semaines ISO `AAAA-Www` partout (`web/src/lib/semaine.js`).
- Identités = plateforme (`profil_portail`) ; pas de superadmin codé en dur ; rôles plateforme + rôle de membre.

## Contraintes
- Secrets jamais en base ni dans les journaux : un dépôt GitHub nomme une variable d'environnement (`jeton_variable`).
- Toute écriture passe par Cerbos (`core/authz`) ; ajouter un test dans `cerbos/tests` avec chaque règle.
- `PASSATION.md` en ajout seulement, entrée datée (`date`).
- Pas de mention d'IA dans commits, PR, code, docs.
- Avant un changement structurant : relire RAIDER (`EagleFox31/project-registry`) et `docs/engineering/lessons-learned.md`.

## Vérification avant « terminé »
`make test`, `make policy-test`, `cd web && npm run build`, `docker compose config -q`.
