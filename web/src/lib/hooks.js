import { useCallback, useEffect, useRef, useState } from 'react'
import { noterErreur, projets } from './api'

/**
 * Charge une ressource et la recharge à la demande. `fn` reçoit rien et
 * renvoie une promesse ; `deps` relance le chargement quand elles changent.
 */
export function useRequete(fn, deps = []) {
  const [etat, setEtat] = useState({ donnees: null, erreur: null, chargement: true })
  const version = useRef(0)

  const recharger = useCallback((silencieux = false) => {
    const v = ++version.current
    if (!silencieux) setEtat(e => ({ ...e, chargement: true, erreur: null }))
    return fn().then(
      donnees => { if (v === version.current) setEtat({ donnees, erreur: null, chargement: false }) },
      erreur => {
        if (v !== version.current) return
        if (erreur?.statut === 0) noterErreur('chargement', erreur.message)
        setEtat(e => ({ ...e, erreur, chargement: false }))
      },
    )
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { recharger() }, [recharger])

  return { ...etat, recharger, remplacer: (donnees) => setEtat(e => ({ ...e, donnees })) }
}

let referentielCache = null

/** Le référentiel du service (statuts, rôles, droits de création), partagé entre pages. */
export function useReferentiel() {
  const [ref, setRef] = useState(referentielCache)
  useEffect(() => {
    if (referentielCache) return
    let actif = true
    projets.referentiel().then(r => {
      referentielCache = r
      if (actif) setRef(r)
    }).catch(() => {})
    return () => { actif = false }
  }, [])
  return ref
}

/** Un appel qui écrit : état d'envoi, message d'erreur, puis callback. */
export function useAction() {
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState(null)
  const lancer = useCallback(async (promesse, apres) => {
    setEnCours(true)
    setErreur(null)
    try {
      const r = await promesse
      if (apres) await apres(r)
      return r
    } catch (exc) {
      setErreur(exc?.message || 'Erreur inattendue')
      return undefined
    } finally {
      setEnCours(false)
    }
  }, [])
  return { enCours, erreur, lancer, effacer: () => setErreur(null) }
}
