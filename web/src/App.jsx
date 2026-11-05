import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { AuthProvider, useAuth } from './lib/auth'
import Accueil from './pages/Accueil'
import Connexion from './pages/Connexion'
import Projets from './pages/Projets'
import Projet from './pages/Projet'
import Propositions from './pages/Propositions'
import JournalErreurs from './pages/JournalErreurs'
import Profil from './pages/Profil'

/**
 * Page réservée aux connectés : sans session, retour à la connexion, qui
 * revient ici une fois le compte ouvert.
 */
function Protege({ children }) {
  const { user } = useAuth()
  const lieu = useLocation()
  if (!user) return <Navigate to="/connexion" replace state={{ retour: lieu.pathname + lieu.search }} />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/connexion" element={<Connexion />} />
        <Route path="/" element={<Protege><Accueil /></Protege>} />
        <Route path="/projets" element={<Protege><Projets /></Protege>} />
        <Route path="/projets/:id" element={<Protege><Projet /></Protege>} />
        <Route path="/propositions" element={<Protege><Propositions /></Protege>} />
        <Route path="/profil" element={<Protege><Profil /></Protege>} />
        <Route path="/journal-erreurs" element={<Protege><JournalErreurs /></Protege>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
