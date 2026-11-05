/**
 * Semaines ISO (`2026-W45`) : le service parle en semaines, l'interface
 * les fait défiler et les affiche en dates.
 */
const JOUR = 86400000

function utc(annee, mois, jour) {
  return new Date(Date.UTC(annee, mois, jour))
}

/** Lundi (UTC) de la semaine ISO qui contient `date`, lue dans le calendrier local. */
export function lundiDe(date) {
  const d = utc(date.getFullYear(), date.getMonth(), date.getDate())
  const decalage = (d.getUTCDay() + 6) % 7
  return new Date(d.getTime() - decalage * JOUR)
}

/** Code ISO (`AAAA-Www`) de la semaine qui contient `date`. */
export function codeSemaine(date = new Date()) {
  const lundi = lundiDe(date)
  const jeudi = new Date(lundi.getTime() + 3 * JOUR)
  const annee = jeudi.getUTCFullYear()
  const premierJeudi = lundiDe(utc(annee, 0, 4))
  const numero = 1 + Math.round((lundi - premierJeudi) / (7 * JOUR))
  return `${annee}-W${String(numero).padStart(2, '0')}`
}

/** Lundi (UTC) d'un code ISO ; null si le code est mal formé. */
export function lundiDuCode(code) {
  const m = /^(\d{4})-W(\d{2})$/.exec(code || '')
  if (!m) return null
  const annee = Number(m[1])
  const numero = Number(m[2])
  if (numero < 1 || numero > 53) return null
  const premier = lundiDe(utc(annee, 0, 4))
  return new Date(premier.getTime() + (numero - 1) * 7 * JOUR)
}

/** Le code de la semaine décalée de `n` (négatif : vers le passé). */
export function decalerSemaine(code, n) {
  const lundi = lundiDuCode(code)
  if (!lundi) return codeSemaine()
  // Date locale à midi : le code ne dépend pas du fuseau de l'utilisateur.
  return codeSemaine(new Date(lundi.getUTCFullYear(), lundi.getUTCMonth(), lundi.getUTCDate() + n * 7, 12))
}

const FORMAT = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const FORMAT_LONG = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })

/** « du 2 au 8 nov. » pour un code de semaine. */
export function libelleSemaine(code) {
  const lundi = lundiDuCode(code)
  if (!lundi) return code || ''
  const dimanche = new Date(lundi.getTime() + 6 * JOUR)
  return `du ${FORMAT.format(lundi)} au ${FORMAT_LONG.format(dimanche)}`
}

export const JOURS_COURTS = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']
