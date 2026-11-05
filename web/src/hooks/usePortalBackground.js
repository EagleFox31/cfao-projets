import { useEffect, useMemo } from 'react'
import { resolvePortalBackground } from '../utils/portalBackground.js'

/**
 * Applique le fond d'écran hero sur `body` pour le portail, restauré au démontage.
 */
export default function usePortalBackground(user) {
  const background = useMemo(() => resolvePortalBackground(user), [user])

  useEffect(() => {
    const body = document.body
    body.classList.add('portal-bg-active')
    body.style.backgroundImage = `url('${background.src}')`
    body.style.backgroundPosition = background.position
    body.style.backgroundSize = 'cover'
    body.style.backgroundAttachment = 'fixed'

    return () => {
      body.classList.remove('portal-bg-active')
      body.style.backgroundImage = ''
      body.style.backgroundPosition = ''
      body.style.backgroundSize = ''
      body.style.backgroundAttachment = ''
    }
  }, [background])

  return background
}
