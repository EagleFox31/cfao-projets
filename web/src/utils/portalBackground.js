/**
 * Fond d'écran hero du portail, selon le profil : copie de la règle de
 * `frontend/src/utils/portalBackground.js` et `portalPersona.js`
 * (persona, puis département), sans la vue groupe que le module n'a pas.
 */
export const PORTAL_HERO_IMAGES = {
  default: '/assets/hero/default.jpg',
  vl: '/assets/hero/cta_hover_vl.jpg',
  pl: '/assets/hero/cta_hover_pl.jpg',
  carrossier: '/assets/hero/cta_hover_carrosserie.png',
  savParts: '/assets/hero/cta_hover_sav.jpg',
  b2b: '/assets/hero/cta_hover_b2b.jpg',
}

export const PORTAL_HERO_BG_POSITION = {
  default: '58% top',
  vl: '70% 8%',
  pl: '74% 5%',
  carrossier: '78% 6%',
  savParts: '68% 10%',
  b2b: '58% top',
}

/** Département du profil → visuel hero, comme dans le portail. */
const DEPARTEMENT_VERS_VISUEL = {
  motors: 'vl',
  equipment: 'pl',
  carrosserie: 'carrossier',
  'parts-motors': 'savParts',
  'parts-eq': 'savParts',
}

/**
 * Clé visuelle du profil connecté.
 * @param {object | null | undefined} user
 * @returns {keyof typeof PORTAL_HERO_IMAGES}
 */
export function resolvePortalBackgroundKey(user) {
  if (user?.persona && PORTAL_HERO_IMAGES[user.persona]) return user.persona
  for (const dept of user?.departments ?? []) {
    if (DEPARTEMENT_VERS_VISUEL[dept]) return DEPARTEMENT_VERS_VISUEL[dept]
  }
  return 'default'
}

/**
 * Image et cadrage du fond portail selon le profil.
 * @param {object | null | undefined} user
 * @returns {{ key: string, src: string, position: string }}
 */
export function resolvePortalBackground(user) {
  const key = resolvePortalBackgroundKey(user)
  return { key, src: PORTAL_HERO_IMAGES[key], position: PORTAL_HERO_BG_POSITION[key] }
}
