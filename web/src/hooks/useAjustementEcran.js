import { useEffect } from 'react'
import { ECHELLE_MIN, echelle } from '../utils/echelle'

/**
 * Fait tenir « Vos priorités » dans le reste de l'écran par une mise à
 * l'échelle, pas en comprimant les cartes.
 *
 * Les cartes gardent la taille de celles des autres sections. Si le
 * contenu dépasse la hauteur laissée par l'appbar et l'entête, il est
 * réduit d'un seul facteur (`zoom`), comme un dézoom limité à la section.
 *
 * La réduction est bornée : l'échelle totale (interface × section) ne
 * descend pas sous `ECHELLE_MIN`, le seuil de lecture de toute l'interface
 * (cf. utils/echelle.js), et la section n'est jamais réduite de plus de
 * 15 %. Au-delà, elle s'allonge et la page défile.
 */
const REDUCTION_MAX = 0.85
// Marge sous les cartes : le bas de la section ne touche pas le bord.
const MARGE = 8

/** Le facteur a appliquer, entre le plancher de lisibilite et 1. */
export function facteurAjustement(disponible, naturelle, echelleRacine = 1) {
  if (!(disponible > 0) || !(naturelle > 0)) return 1
  // Arrondis au millieme : le plancher vers le haut, le facteur vers le bas.
  const plancher = Math.min(1, Math.ceil(Math.max(REDUCTION_MAX, ECHELLE_MIN / echelleRacine) * 1000) / 1000)
  const f = Math.floor(Math.min(1, (disponible - MARGE) / naturelle) * 1000) / 1000
  return Math.max(plancher, f)
}

/**
 * @param {import('react').RefObject<HTMLElement>} ref  le contenu de la section
 *   (`.container` directement sous `.portal-next-actions-viewport`)
 * @param {Array} cles  ce qui fait apparaitre ou disparaitre la section
 */
export default function useAjustementEcran(ref, cles = []) {
  useEffect(() => {
    const contenu = ref?.current
    const section = contenu?.parentElement
    if (!contenu || !section) return undefined

    let facteur = 1
    const ajuster = () => {
      const racine = echelle()
      // Hauteur reservee au contenu, en pixels CSS : `min-height` de la
      // section (bordure comprise), moins ses marges interieures.
      const style = getComputedStyle(section)
      const disponible = parseFloat(style.minHeight)
        - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom)
      // Hauteur du contenu a taille normale : la mesure est en pixels
      // d'ecran, zoom de la racine et de la section compris.
      const naturelle = contenu.getBoundingClientRect().height / (racine * facteur)
      const f = facteurAjustement(disponible, naturelle, racine)
      if (Math.abs(f - facteur) < 0.005) return
      facteur = f
      if (f < 1) contenu.style.zoom = String(f)
      else contenu.style.removeProperty('zoom')
    }

    ajuster()
    const observateur = new ResizeObserver(ajuster)
    observateur.observe(section)
    observateur.observe(contenu)
    window.addEventListener('resize', ajuster)
    return () => {
      observateur.disconnect()
      window.removeEventListener('resize', ajuster)
      contenu.style.removeProperty('zoom')
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref, ...cles])
}
