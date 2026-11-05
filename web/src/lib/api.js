/**
 * Client du service : `fetch` avec le cookie de session, délai borné et
 * erreurs lisibles. Toute réponse en erreur arrive sous `{ erreur }`
 * (contrat de l'API) ; on la relève en `ErreurApi` avec son statut.
 */
export class ErreurApi extends Error {
  constructor(message, statut, corps) {
    super(message)
    this.statut = statut
    this.corps = corps
  }
}

const DELAI = 15000

async function appeler(chemin, options = {}) {
  const controle = new AbortController()
  const minuterie = setTimeout(() => controle.abort(), options.delai ?? DELAI)
  let r
  try {
    r = await fetch(chemin, {
      credentials: 'same-origin',
      signal: controle.signal,
      ...options,
      headers: { Accept: 'application/json', ...(options.headers || {}) },
    })
  } catch (exc) {
    const message = exc?.name === 'AbortError'
      ? 'Le service de gestion de projets met trop de temps à répondre.'
      : 'Le service de gestion de projets ne répond pas.'
    throw new ErreurApi(message, 0, null)
  } finally {
    clearTimeout(minuterie)
  }
  if (r.status === 204) return null
  let corps = null
  try { corps = await r.json() } catch { corps = null }
  if (!r.ok) {
    const message = corps?.erreur || (r.status === 401 ? 'Session expirée : reconnectez-vous.'
      : r.status === 403 ? 'Action non autorisée.' : `Erreur ${r.status}`)
    throw new ErreurApi(message, r.status, corps)
  }
  return corps
}

function ecrire(methode) {
  return (chemin, corps, options = {}) => appeler(chemin, {
    method: methode,
    headers: { 'Content-Type': 'application/json' },
    body: corps === undefined ? undefined : JSON.stringify(corps),
    ...options,
  })
}

/** Transforme un objet de paramètres en chaîne de requête, sans les vides. */
export function requete(params = {}) {
  const u = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') u.set(k, String(v))
  })
  const s = u.toString()
  return s ? `?${s}` : ''
}

export const api = {
  get: (chemin, params) => appeler(`${chemin}${requete(params)}`),
  post: ecrire('POST'),
  patch: ecrire('PATCH'),
  delete: ecrire('DELETE'),
}

const BASE = '/pj-donnees'

/** Les appels du module, nommés d'après ce qu'ils font. */
export const projets = {
  referentiel: () => api.get(`${BASE}/referentiel`),
  moi: () => api.get(`${BASE}/personnes/moi`),
  modifierMoi: (corps) => api.patch(`${BASE}/personnes/moi`, corps),
  personnes: (q) => api.get(`${BASE}/personnes`, { q }),
  liste: (statut) => api.get(`${BASE}/projets`, { statut }),
  creer: (corps) => api.post(`${BASE}/projets`, corps),
  detail: (id) => api.get(`${BASE}/projets/${id}`),
  modifier: (id, corps) => api.patch(`${BASE}/projets/${id}`, corps),
  supprimer: (id) => api.delete(`${BASE}/projets/${id}`),
  ajouterMembre: (id, corps) => api.post(`${BASE}/projets/${id}/membres`, corps),
  modifierMembre: (id, mid, corps) => api.patch(`${BASE}/projets/${id}/membres/${mid}`, corps),
  retirerMembre: (id, mid) => api.delete(`${BASE}/projets/${id}/membres/${mid}`),
  creerTache: (id, corps) => api.post(`${BASE}/projets/${id}/taches`, corps),
  modifierTache: (id, tid, corps) => api.patch(`${BASE}/projets/${id}/taches/${tid}`, corps),
  supprimerTache: (id, tid) => api.delete(`${BASE}/projets/${id}/taches/${tid}`),
  ajouterDepot: (id, corps) => api.post(`${BASE}/projets/${id}/depots`, corps),
  retirerDepot: (id, did) => api.delete(`${BASE}/projets/${id}/depots/${did}`),
  synchroniser: (id, did) => api.post(`${BASE}/projets/${id}/depots/${did}/synchroniser`, undefined, { delai: 60000 }),
  activite: (id, semaine) => api.get(`${BASE}/projets/${id}/activite`, { semaine }),
  activiteSemaine: (semaine) => api.get(`${BASE}/activite/semaine`, { semaine }),
  propositionsDuProjet: (id) => api.get(`${BASE}/projets/${id}/propositions`),
  proposer: (id, corps) => api.post(`${BASE}/projets/${id}/propositions`, corps),
  propositions: () => api.get(`${BASE}/propositions`),
  decider: (pid, corps) => api.post(`${BASE}/propositions/${pid}/decision`, corps),
  erreurs: (params) => api.get(`${BASE}/erreurs`, params),
  purgerErreurs: (ids) => api.delete(`${BASE}/erreurs`, { ids }),
}

/** Signale au service une erreur vue par l'interface ; jamais bloquant. */
export function noterErreur(action, message, detail) {
  api.post(`${BASE}/erreurs`, { action, message: String(message || ''), detail: String(detail || '') })
    .catch(() => {})
}
