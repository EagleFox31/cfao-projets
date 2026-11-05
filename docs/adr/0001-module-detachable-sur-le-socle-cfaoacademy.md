# ADR 0001 — Un module détachable sur le socle des portails CFAO Academy

Date : 2026-11-05 · Statut : accepté

## Contexte

Il faut un gestionnaire de projets pour l'équipe : projets, intervenants,
avancement, lecture du travail GitHub de la semaine par personne, et un circuit
de propositions pour les profils sans droit d'écriture. Les identités, les rôles
et le style visuel doivent être ceux de la plateforme CFAO Academy.

## Décision

1. **Même socle que les modules existants** (`cfao-comptes-rendus` pris comme
   référence) : Django/DRF, React/Vite, nginx, Cerbos, PostgreSQL, trois modes
   d'authentification (`standalone`, `local`, `integrated`), préfixes propres au
   module (`PJ_`, `pj-`, `/pj-donnees`, cookie `cfao_pj_session`, port 8094).
   Le module s'installe seul (compose) ou derrière la plateforme.
2. **Autorisations dans Cerbos, défaut refus**, avec des rôles dérivés du rôle de
   membre (chef / contributeur / observateur / demandeur) et des rôles plateforme.
   Aucun identifiant de superadmin dans le code.
3. **Lecture GitHub côté service**, jamais côté navigateur : jeton en lecture
   seule dans l'environnement, désigné par nom de variable par dépôt ; cache des
   commits en base ; synchronisation périodique + webhook `push` signé. L'activité
   hebdomadaire est calculée depuis ce cache, le diff de la semaine est un lien
   `compare` GitHub.
4. **Propositions** comme objets de première classe (type, cible, contenu,
   motif, statut) : le service valide le contenu comme s'il était appliqué, la
   décision l'applique dans la même transaction, et notifie par courriel.
5. **Courriels** par le hub mail de la plateforme quand il existe
   (`MAIL_MODE=hub`), sinon SMTP ; `console`/`aucun` en dev et test.

## Alternatives écartées

- Un plugin dans le portail principal : couplerait le cycle de vie du
  gestionnaire à celui du portail et interdirait l'installation isolée.
- Lire GitHub depuis le navigateur avec un jeton par utilisateur : jeton exposé,
  quotas par poste, pas d'historique agrégé.
- GitHub Projects comme gestionnaire : pas d'identités plateforme, pas de
  propositions soumises à nos rôles, dépendance à l'organisation GitHub.

## Conséquences

- Les contrats (routes `/pj-donnees`, formes JSON, variables `PJ_*`) sont
  documentés dans le README et couverts par pytest ; toute rupture est versionnée.
- La CI est change-scoped (appfactory impact analysis) : api, web, cerbos,
  conteneurs.
- Les modules frères peuvent reprendre `web/src/lib/semaine.js`,
  `ActiviteSemaine` et le circuit de propositions tels quels.
