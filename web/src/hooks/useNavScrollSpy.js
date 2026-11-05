import { useCallback, useEffect, useState } from 'react'

/** Repli stable : un tableau recréé à chaque rendu relancerait l'observation. */
const AUCUNE = []

/** Sous la navbar sticky (~76px) + marge de lecture */
const NAV_MARKER_MIN = 120

/**
 * Ligne de détection dans le viewport : dès qu'une section franchit ce seuil,
 * elle devient active. Gère le hero portail au-dessus de la 1ʳᵉ ancre (#next-actions).
 */
function navViewportMarker() {
  return Math.max(NAV_MARKER_MIN, window.innerHeight * 0.42)
}

export function getNavKeyAtScroll(_y = window.scrollY, sections = AUCUNE) {
  if (!sections?.length) return null

  const marker = navViewportMarker()
  let active = null

  for (const { key, id } of sections) {
    const el = document.getElementById(id)
    if (!el) continue
    if (el.getBoundingClientRect().top <= marker) active = key
  }

  if (active) return active

  // Hero portail : section visible sans avoir encore franchi le marqueur
  for (const { key, id } of sections) {
    const el = document.getElementById(id)
    if (!el) continue
    const { top, bottom } = el.getBoundingClientRect()
    const visible = Math.min(bottom, window.innerHeight) - Math.max(top, NAV_MARKER_MIN)
    if (visible >= 140) return key
  }

  return null
}

export default function useNavScrollSpy(enabled, sections = AUCUNE) {
  const [activeKey, setActiveKey] = useState(null)

  const update = useCallback(() => {
    if (!enabled) return
    setActiveKey(getNavKeyAtScroll(window.scrollY, sections))
  }, [enabled, sections])

  useEffect(() => {
    if (!enabled) {
      setActiveKey(null)
      return undefined
    }

    update()
    let ticking = false
    const onScroll = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        update()
        ticking = false
      })
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll, { passive: true })

    const root = document.querySelector('.portal-page') ?? document.body
    let moTicking = false
    const observer = new MutationObserver(() => {
      if (moTicking) return
      moTicking = true
      requestAnimationFrame(() => {
        update()
        moTicking = false
      })
    })
    observer.observe(root, { childList: true, subtree: true })

    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      observer.disconnect()
    }
  }, [enabled, update])

  return { activeKey, setActiveKey, refresh: update }
}
