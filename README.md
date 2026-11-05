# CFAO Academy — Gestionnaire de projets (`cfao-projets`)

Module détachable de la plateforme CFAO Academy : des projets, les personnes qui
y travaillent, leurs tâches et leur avancement, la lecture des commits GitHub
pour voir **le travail accompli chaque semaine, par personne, avec le diff**, et
un circuit de **propositions de modifications** pour les profils qui n'ont pas
le droit d'écrire directement.

Il suit les conventions des autres modules (`cfao-comptes-rendus`, `cfao-needs`) :
un service Django/DRF, une interface React au style des portails, une passerelle
nginx, Cerbos pour les autorisations, PostgreSQL, le tout dockerisé et installable
seul ou intégré à la plateforme.

## Ce que fait le module

| Besoin | Où |
| --- | --- |
| Projets (statut, dates, périmètre, avancement calculé ou manuel) | `/projets`, onglet Paramètres |
| Membres et rôles (chef, contributeur, observateur, demandeur) | onglet Équipe |
| Tâches pondérées → avancement | onglet Avancement et tâches |
| Dépôts GitHub rattachés, synchronisation périodique, webhook `push` | onglet Paramètres |
| Travail de la semaine par personne : commits, lignes, diff par dépôt, derniers commits | onglet Activité GitHub, accueil |
| Propositions (modifier le projet, ajouter/modifier une tâche, ajouter un membre) et décision | onglet Propositions, `/propositions` |
| Courriels (ajout à un projet, proposition reçue/décidée, récapitulatif hebdomadaire) | `MAIL_MODE` |
| Journal des erreurs (service, interface, synchronisation) | `/journal-erreurs` (build team, superadmin) |

Les identités viennent de la plateforme : rôles, périmètre (`scopeNodes`) et
marques sont ceux du portail. Le module n'a pas de superadmin codé en dur.

## Démarrer

```bash
cp .env.example .env
make up          # http://localhost:8094 (mode standalone : profils fictifs, sans mot de passe)
```

Modes d'authentification (`DEPLOYMENT_MODE`) : `standalone` (poste de dev),
`local` (comptes à mot de passe, sans Keycloak), `integrated` (jeton Keycloak de
la plateforme, voir le bloc OIDC de `.env.example`). En production : `deploy.sh`
/ `deploy.ps1` avec `docker-compose.prod.yml` et `env.prod.example`.

Commandes utiles :

```bash
make test            # pytest (API) + vitest (interface)
make policy-test     # cerbos compile --tests
make synchroniser    # lit une fois les dépôts GitHub de tous les projets
make recap           # envoie le récapitulatif hebdomadaire aux chefs de projet
```

Développement de l'interface : `cd web && npm run dev` (port 5178, proxy vers
l'API sur 5175).

## Lecture GitHub

- Un projet rattache des dépôts `owner/nom`. Le service lit les commits avec
  `GITHUB_TOKEN` (lecture seule) ou la variable d'environnement nommée par le
  dépôt (`jeton_variable`) : **aucun jeton n'est saisi dans l'interface ni
  stocké en base**.
- Le service `synchro` relit les dépôts toutes les `SYNCHRO_INTERVALLE`
  secondes ; un webhook `push` (`POST /pj-donnees/webhooks/github`, signé avec
  `GITHUB_WEBHOOK_SECRET`) déclenche une lecture immédiate.
- Un commit est attribué à une personne par son identifiant GitHub (« Mon
  profil ») ou par son adresse e-mail ; sinon il apparaît « non rattaché ».
- L'activité d'une semaine ISO (`?semaine=2026-W45`) donne, par personne, les
  commits, les lignes ajoutées/retirées, la répartition par jour, et par dépôt
  le lien `compare/premier^...dernier` vers le diff de la semaine.

## Autorisations

Cerbos (`cerbos/policies`, défaut : tout refuser). Résumé :

| Action | Qui |
| --- | --- |
| Créer un projet | `superadmin`, `build_team`, `team_manager` |
| Modifier, gérer les membres, synchroniser, décider des propositions | chef de projet, `superadmin`, `build_team` |
| Changer le statut d'une tâche | chef, ou la personne assignée |
| Proposer une modification | tout membre, et tout profil du même périmètre |
| Journal des erreurs | `superadmin`, `build_team` |

`make policy-test` rejoue les cas de `cerbos/tests`.

## Contrat HTTP

`GET /apercu/sante` (sonde) et `/pj-donnees/...` (session, référentiel, projets,
membres, tâches, dépôts, activité, propositions, personnes, erreurs, webhook).
Les réponses sont en JSON ; les erreurs portent `{ "erreur": "..." }`.

## Documentation

- `docs/adr/` : décisions d'architecture.
- `docs/engineering/lessons-learned.md` : mémoire des erreurs et near miss.
- `CLAUDE.md` : conventions courtes du dépôt (stack, préfixes, contraintes).
- `PASSATION.md` : journal de passation (ajout seulement).
