/**
 * Défilement d'ancrage du portail.
 *
 * Objectif : le HAUT du conteneur de la section cible vient se coller sous
 * l'appbar, sans aucun espace, de sorte que la section précédente ne soit
 * plus visible du tout.
 *
 * Deux pièges gérés ici :
 *  1. Les sections entrent au scroll (`PortalReveal` → `.reveal` / `.stagger`).
 *     Tant qu'une section n'est pas révélée elle porte un `translateY` et sa
 *     hauteur n'est pas définitive : si une section SITUÉE AU-DESSUS de la cible
 *     se révèle pendant le défilement, la cible se décale en cours de route.
 *     → on révèle TOUTES les sections de la page avant de défiler.
 *  2. La sticky-bar n'est affichée que lorsque l'entête de page est sorti du
 *     champ : au moment du clic elle est encore masquée. On mesure donc sa
 *     hauteur telle qu'elle sera À L'ARRIVÉE, sinon le défilement s'arrête
 *     44px trop bas et l'entête reste visible. C'est ce que `scrollIntoView`
 *     + `scroll-margin-top` ne savent pas faire : l'offset CSS est figé.
 */

/** Repli si la barre de navigation n'est pas mesurable. */
const FALLBACK_NAV_HEIGHT = 77

/**
 * Bas réel de l'appbar, en pixels depuis le haut du viewport, tel qu'il sera
 * À L'ARRIVÉE du défilement.
 *
 * Deux subtilités :
 *  - La sticky-bar n'apparaît que lorsque l'entête de page sort du champ : au
 *    moment du clic elle est encore masquée, mais elle SERA affichée une fois
 *    arrivé sur une section. Il faut donc la compter par anticipation.
 *  - Elle est en `position: fixed; top: 76px`, donc positionnée par rapport au
 *    VIEWPORT et non empilée à la suite de la Nav : elle recouvre la bordure
 *    basse de celle-ci. Additionner les deux hauteurs donnerait 1px de trop et
 *    laisserait un liseré. On lit donc son `top` CSS, auquel on ajoute sa
 *    hauteur de bordure comprise.
 */
function appbarBottom() {
  const sticky = document.querySelector('.portal-sticky-bar')

  if (sticky) {
    const styles = getComputedStyle(sticky)
    const top = Number.parseFloat(styles.top)
    // `getBoundingClientRect().height` reste juste même translatée hors champ
    // (`translateY(-100%)`) et inclut déjà la bordure basse.
    const height = sticky.getBoundingClientRect().height
    if (Number.isFinite(top)) return top + height
  }

  const nav = document.querySelector('.nav')
  return nav ? nav.getBoundingClientRect().height : FALLBACK_NAV_HEIGHT
}

const SNAP_CLASS = 'portal-section-snap-hl'
const SNAP_DURATION = 1600

/**
 * Sections qui doivent révéler l'entête plutôt que se coller à l'appbar.
 *
 * « Vos priorités » partage l'écran avec l'entête (sa hauteur est calculée
 * comme le reste de l'écran) : l'ancrer sous l'appbar ferait sortir l'entête du
 * champ alors que les deux sont conçues pour être vues ensemble. Remonter en
 * haut de page les affiche toutes les deux.
 */
function scrollsToPageTop(section) {
  return section.classList.contains('portal-next-actions-viewport')
}

/**
 * Fige toutes les animations d'entrée de la page : chaque `.reveal` / `.stagger`
 * passe en état final (`.in`), donc plus aucune hauteur ne bouge pendant le
 * défilement. Sans cela, une section au-dessus de la cible qui se révèle
 * pendant le smooth-scroll fausse la position d'arrivée.
 */
function freezePageReveals() {
  const animated = document.querySelectorAll(
    '.portal-page .reveal:not(.in), .portal-page .stagger:not(.in)',
  )
  animated.forEach(el => el.classList.add('in'))
}

/**
 * Défile jusqu'à `sectionId` en collant le haut de son conteneur sous l'appbar.
 *
 * @param {string} sectionId  id de la section cible
 * @param {object} [options]
 * @param {boolean} [options.highlight=true] halo bref à l'arrivée
 * @returns {boolean} true si la section existe
 */
export function scrollToPortalSection(sectionId, { highlight = true } = {}) {
  if (typeof document === 'undefined' || !sectionId) return false

  const el = document.getElementById(sectionId)
  if (!el) return false

  // On garde la structure de mise en page normale : la cible ne doit pas
  // "manger" le padding du conteneur, afin de laisser visible l'entête et la
  // section qui précède lors d'un déplacement par ancre.
  freezePageReveals()

  const prefersReduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  // rAF : laisse le navigateur recalculer le layout (retrait des `translateY`
  // et du padding) avant de mesurer la position cible.
  const go = () => {
    // « Vos priorités » est dimensionnée pour tenir dans l'écran AVEC l'entête
    // (cf. --portal-priorities-h) : on remonte donc en haut de page plutôt que
    // de coller la section sous l'appbar, ce qui masquerait l'entête.
    const top = scrollsToPageTop(el)
      ? 0
      : el.getBoundingClientRect().top + window.scrollY - appbarBottom()
    // `ceil` plutôt que `round` : sur les hauteurs fractionnaires (zoom, DPI),
    // arrondir vers le bas laisserait un liseré de la section précédente.
    window.scrollTo({
      top: Math.max(0, Math.ceil(top)),
      behavior: prefersReduced ? 'auto' : 'smooth',
    })
  }

  if (prefersReduced) go()
  else requestAnimationFrame(go)

  if (highlight) {
    el.classList.add(SNAP_CLASS)
    window.setTimeout(() => el.classList.remove(SNAP_CLASS), SNAP_DURATION)
  }
  return true
}
