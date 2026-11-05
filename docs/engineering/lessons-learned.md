# Mémoire des erreurs — cfao-projets

À consulter avant tout travail proche d'un incident listé. Une erreur répétée
exige un contrôle plus fort (test, garde-fou, règle CI).

## 2026-11-05 — Semaine ISO calculée en UTC alors que l'utilisateur vit en heure locale

- **Contexte** : `codeSemaine(new Date(2024, 11, 30))` rendait `2024-W52` au
  lieu de `2025-W01` sur un poste en UTC+1 : la date locale minuit devenait la
  veille en UTC.
- **Cause racine** : mélange de deux calendriers (champs `getUTC*` sur une date
  construite en local) ; le décalage de semaines repassait par le même chemin.
- **Classification** : logique de date / fuseau.
- **Résolution** : `lundiDe` lit le calendrier local ; `decalerSemaine` repart
  d'une date locale à midi. Tests vitest sur les bascules d'année.
- **Prévention vérifiable** : `web/src/lib/semaine.test.js` (cas 2024-12-30,
  2027-01-01, décalage 2026-W01 → 2025-W52).
- **Leçon** : une fonction de date choisit un calendrier (local ou UTC) et s'y
  tient de bout en bout ; tester toujours une bascule d'année et un lundi minuit.

## 2026-11-05 — Marquage mobile du menu écrit « de mémoire » au lieu de suivre la CSS existante

- **Contexte** : la première version de `Nav.jsx` utilisait des classes
  (`nav-mobile-actions`, backdrop hors panneau) absentes de `index.css` du
  portail ; le tiroir mobile ne s'affichait pas.
- **Cause racine** : composant réécrit sans relire le sélecteur CSS cible.
- **Résolution** : structure alignée sur `.nav-mobile-panel[hidden] > .nav-mobile-backdrop + .nav-mobile-drawer`.
- **Prévention** : pour tout composant repris d'un portail, grep des classes
  dans la feuille réutilisée avant d'écrire le JSX.
- **Leçon** : réutiliser une CSS, c'est en adopter le contrat de classes.

## 2026-11-05 — Chemin de dépôt `../x` accepté par la validation initiale

- **Contexte** : le champ `depot` (`owner/nom`) acceptait une valeur de type
  `../autre`, qui aurait construit une URL GitHub hors du dépôt visé.
- **Résolution** : validation stricte `^[\w.-]+/[\w.-]+$` côté service et côté
  formulaire ; test pytest de refus.
- **Leçon** : toute valeur qui finit dans une URL d'API tierce est validée par
  forme positive, pas par liste noire.

## 2026-11-05 — Suite de tests dépendante du `.env` du poste

- **Contexte** : `test_le_portail_garde_sa_connexion_par_compte` passait tant que
  le dépôt n'avait pas de `.env`, puis échouait (403) une fois `.env` créé pour
  `docker compose config` : `ORIGINES_AUTORISEES` du fichier écrasait le défaut
  du code, qui incluait les origines du portail (5173/5174).
- **Cause racine** : `config/settings/test.py` héritait de `base.py`, qui lit le
  `.env` racine ; les tests dépendaient donc de l'état du poste.
- **Classification** : isolation des tests / configuration.
- **Résolution** : `ORIGINES_AUTORISEES` figé dans `settings/test.py` ;
  `.env.example` aligné sur le défaut du code.
- **Prévention vérifiable** : la CI n'a pas de `.env` au moment de pytest ; le
  job `conteneurs` en crée un seulement pour `compose config`.
- **Leçon** : tout réglage que lit un test est fixé dans les réglages de test,
  jamais hérité d'un fichier local. Le module de référence a la même fragilité.
