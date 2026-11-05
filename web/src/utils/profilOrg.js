/** BU → libellé filiale CFAO (ex. CFAO EQUIPMENT Cameroun). */
const PREFIXE_FILIALE_PAR_BU = {
  motors: 'CFAO MOTORS',
  equipment: 'CFAO EQUIPMENT',
  carrosserie: 'CFAO MOBILITY',
  'parts-motors': 'CFAO MOBILITY',
  'parts-eq': 'CFAO MOBILITY',
}

/** Pays affiché / drapeau — explicite ou déduit du nom de filiale. */
export function resolveProfilePays(user) {
  if (user?.pays) return user.pays
  const filiale = user?.filiale ?? ''
  if (/^CFAO\s+(?:MOTORS|EQUIPMENT|MOBILITY)\s+/i.test(filiale)) {
    return filiale.replace(/^CFAO\s+(?:MOTORS|EQUIPMENT|MOBILITY)\s+/i, '').trim()
  }
  if (filiale === 'Groupe') return null
  return filiale || null
}

/** Libellé filiale CFAO (CFAO MOTORS Cameroun…). */
export function resolveProfileFilialeLabel(user) {
  if (user?.filiale?.startsWith('CFAO ')) return user.filiale
  const pays = resolveProfilePays(user)
  if (!pays || pays === 'Groupe') return user?.filiale ?? null
  const dept = user?.departments?.[0]
  const prefix = PREFIXE_FILIALE_PAR_BU[dept]
  if (prefix) return `${prefix} ${pays}`
  return user?.filiale ?? pays
}
