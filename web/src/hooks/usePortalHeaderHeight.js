import { useEffect } from 'react'
import { echelle } from '../utils/echelle'

/**
 * Publie la hauteur réelle de l'entête portail dans `--portal-header-h`.
 *
 * La section « Vos priorités » doit occuper exactement le reste de l'écran
 * (`100dvh - appbar - entête`). Cette hauteur n'est pas connue en CSS : elle
 * dépend du nom affiché, du nombre de marques et de la largeur de fenêtre.
 * On la mesure donc et on la republie à chaque changement de taille.
 *
 * @param {import('react').RefObject<HTMLElement>} ref  entête à mesurer
 * @param {boolean} enabled  n'observe que si la mise en page le demande
 */
export default function usePortalHeaderHeight(ref, enabled = true) {
  useEffect(() => {
    const root = document.documentElement

    if (!enabled) {
      root.style.removeProperty('--portal-header-h')
      return undefined
    }

    const el = ref?.current
    if (!el) return undefined

    const publish = () => {
      // Mesure en pixels d'ecran, reportee en pixels CSS.
      const height = el.getBoundingClientRect().height / echelle()
      root.style.setProperty('--portal-header-h', `${Math.round(height)}px`)
    }

    publish()

    const observer = new ResizeObserver(publish)
    observer.observe(el)

    return () => {
      observer.disconnect()
      root.style.removeProperty('--portal-header-h')
    }
  }, [ref, enabled])
}
