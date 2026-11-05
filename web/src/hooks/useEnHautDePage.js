import { useEffect } from 'react'

/** Ouvre la page en haut et lui donne son titre dans l'onglet. */
export default function useEnHautDePage(titre) {
  useEffect(() => {
    window.scrollTo(0, 0)
    if (titre) document.title = `${titre} — CFAO Academy`
  }, [titre])
}
