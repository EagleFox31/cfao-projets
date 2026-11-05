/**
 * Messages et validation du formulaire de connexion, en français.
 *
 * Les motifs de refus (identifiants, réseau, échec général) sont ceux du
 * module ; les erreurs de saisie reprennent le texte du portail.
 */
export const CODES_ERREUR = {
  EMAIL_REQUIRED: 'EMAIL_REQUIRED',
  EMAIL_INVALID: 'EMAIL_INVALID',
  PASSWORD_REQUIRED: 'PASSWORD_REQUIRED',
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  NETWORK: 'NETWORK',
  GENERIC: 'GENERIC',
}

export const CODES_SUCCES = {
  FORGOT_EMAIL_SENT: 'FORGOT_EMAIL_SENT',
}

const MESSAGES = {
  [CODES_ERREUR.EMAIL_REQUIRED]: 'Indiquez votre nom d’utilisateur ou e-mail.',
  [CODES_ERREUR.EMAIL_INVALID]: 'Nom d’utilisateur ou e-mail invalide.',
  [CODES_ERREUR.PASSWORD_REQUIRED]: 'Indiquez votre mot de passe.',
  [CODES_ERREUR.INVALID_CREDENTIALS]: 'Identifiant ou mot de passe incorrect.',
  [CODES_ERREUR.NETWORK]: 'Le service de gestion de projets ne répond pas. Réessayez dans un instant.',
  [CODES_ERREUR.GENERIC]: 'La connexion a échoué. Réessayez, ou contactez votre administrateur.',
  [CODES_SUCCES.FORGOT_EMAIL_SENT]:
    'Si un compte est associé à cette adresse, vous recevrez un e-mail de réinitialisation sous quelques minutes.',
}

export function messageAuth(code) {
  if (!code) return null
  return MESSAGES[code] ?? MESSAGES.GENERIC
}

function adresseValide(valeur) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valeur?.trim() ?? '')
}

export function validerConnexion({ email, password }) {
  const erreurs = {}
  if (!email?.trim()) erreurs.email = CODES_ERREUR.EMAIL_REQUIRED
  if (!password) erreurs.password = CODES_ERREUR.PASSWORD_REQUIRED
  return { ok: Object.keys(erreurs).length === 0, erreurs }
}

export function validerOubli({ email }) {
  const erreurs = {}
  if (!email?.trim()) erreurs.email = CODES_ERREUR.EMAIL_REQUIRED
  else if (!adresseValide(email)) erreurs.email = CODES_ERREUR.EMAIL_INVALID
  return { ok: Object.keys(erreurs).length === 0, erreurs }
}
