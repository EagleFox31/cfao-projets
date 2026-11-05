import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)

// Le profil connecté, pour les modules qui le lisent hors de React
// (journal des erreurs). Il vient de la session du service ; on
// ne s'y fie jamais sans l'avoir vérifiée auprès de lui.
const CLE = 'cfao_mock_user'
const SESSION = '/pj-donnees/session'

function retenir(profil) {
  try {
    if (profil) sessionStorage.setItem(CLE, JSON.stringify(profil))
    else sessionStorage.removeItem(CLE)
  } catch { /* stockage indisponible : la session du service suffit */ }
}

async function appeler(chemin, options = {}) {
  const controle = new AbortController()
  const minuterie = setTimeout(() => controle.abort(), 5000)
  try {
    return await fetch(chemin, { credentials: 'same-origin', signal: controle.signal, ...options })
  } finally {
    clearTimeout(minuterie)
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Le temps de demander au service si une session est ouverte : sans
  // cette attente, un formateur connecté serait renvoyé vers la connexion.
  const [verification, setVerification] = useState(true)

  useEffect(() => {
    let actif = true
    appeler(SESSION)
      .then(r => (r.ok ? r.json() : null))
      .catch(() => null)
      .then(profil => {
        if (!actif) return
        retenir(profil)
        setUser(profil)
        setVerification(false)
      })
    return () => { actif = false }
  }, [])

  /** Connexion par le formulaire : renvoie null, ou le motif du refus. */
  async function connexion(identifiant, motDePasse, seSouvenir) {
    let r
    try {
      r = await appeler('/pj-donnees/connexion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifiant: identifiant.trim(), motDePasse, seSouvenir }),
      })
    } catch {
      return 'NETWORK'
    }
    if (r.status === 401) return 'INVALID_CREDENTIALS'
    if (!r.ok) return 'GENERIC'
    const profil = await r.json()
    retenir(profil)
    setUser(profil)
    return null
  }

  function logout() {
    appeler('/pj-donnees/deconnexion', { method: 'POST' }).catch(() => {})
    retenir(null)
    setUser(null)
  }

  if (verification) return null

  return (
    <AuthContext.Provider value={{ user, connexion, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
