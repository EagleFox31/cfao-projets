/**
 * Mise a l'echelle de l'interface selon l'ecran.
 *
 * L'interface est dessinee pour un ecran de 1920 pixels de large. Sur un
 * portable dont Windows agrandit l'affichage (125 %, 150 %), le navigateur
 * ne voit plus que 1536 ou 1280 pixels : tout parait trop gros et il
 * fallait dezoomer a la main pour retrouver la page d'un ecran a 100 %.
 * On applique ici ce dezoom, d'apres la largeur de l'ecran — pas de la
 * fenetre : une fenetre reduite garde sa mise en page adaptative.
 *
 * `zoom` sur la racine a deux angles morts, compenses ailleurs :
 * - les unites d'ecran (`vh`, `vw`) ne sont pas corrigees : Vite les
 *   divise par `--echelle` a la compilation (cf. vite.config.js) ;
 * - les requetes `max-height` voient la hauteur reelle : les seuils
 *   passent par l'attribut `data-bas`, calcule sur la hauteur effective.
 * Enfin, les mesures (`getBoundingClientRect`, `clientX`) sont en pixels
 * d'ecran : les reporter en CSS demande de les diviser par `echelle()`.
 */
const REFERENCE = 1920
// Echelle minimale de lecture : 13 px (texte secondaire des cartes) restent
// au moins 10,4 px a l'ecran, 15 px (texte courant) au moins 12 px.
export const ECHELLE_MIN = 0.8
// Les seuils de hauteur des feuilles de style (`:root[data-bas~="820"]`).
const SEUILS_HAUTEUR = [540, 720, 820]

/** Le facteur applique a l'interface (1 sur un ecran de reference). */
export function echelle() {
  return Number(document.documentElement.dataset.echelle) || 1
}

function appliquer() {
  const racine = document.documentElement
  const largeur = window.screen?.width || REFERENCE
  // Au-dessous de 1280, c'est une tablette ou un telephone : leur mise
  // en page propre s'applique, sans reduction.
  const z = largeur >= 1280 && largeur < REFERENCE
    ? Math.round(Math.max(ECHELLE_MIN, largeur / REFERENCE) * 1000) / 1000
    : 1
  if (z < 1) {
    racine.style.zoom = String(z)
    racine.style.setProperty('--echelle', String(z))
    racine.dataset.echelle = String(z)
  } else {
    racine.style.removeProperty('zoom')
    racine.style.removeProperty('--echelle')
    delete racine.dataset.echelle
  }
  const hauteur = window.innerHeight / z
  racine.dataset.bas = SEUILS_HAUTEUR.filter(n => hauteur <= n).join(' ')
}

/** A appeler avant le premier rendu ; suit les changements d'ecran. */
export function suivreEchelle() {
  appliquer()
  window.addEventListener('resize', appliquer)
  // Fenetre passee sur un ecran d'une autre mise a l'echelle.
  const suivreDensite = () => {
    const mq = window.matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`)
    mq.addEventListener('change', () => { appliquer(); suivreDensite() }, { once: true })
  }
  suivreDensite()
}
