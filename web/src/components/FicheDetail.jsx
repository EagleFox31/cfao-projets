import { useLocation, useNavigate } from 'react-router-dom'
import Nav from './portail/Nav'
import Footer from './portail/Footer'
import useEnHautDePage from '../hooks/useEnHautDePage'

function IconeCroix() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  )
}

/** Croix de fermeture : retour à la page précédente, sinon `repli`. */
export function BoutonFermer({ repli = '/', ariaLabel = 'Fermer' }) {
  const navigate = useNavigate()
  const location = useLocation()
  const fermer = () => {
    if (location.key !== 'default') navigate(-1)
    else navigate(repli)
  }
  return (
    <button type="button" className="pj-fiche-fermer" onClick={fermer} aria-label={ariaLabel}>
      <IconeCroix />
    </button>
  )
}

/**
 * Gabarit « fiche » des pages de détail, calqué sur la page article du portail :
 * feuille centrée, croix de fermeture, entête (étiquette, méta, titre, chapeau),
 * puis le contenu.
 */
export default function FicheDetail({ titre, etiquette, meta, chapeau, repli = '/', fermerLibelle = 'Fermer', children }) {
  useEnHautDePage(titre)
  return (
    <>
      <Nav />
      <main className="portal-page pj-fiche-page">
        <div className="container pj-fiche-shell">
          <BoutonFermer repli={repli} ariaLabel={fermerLibelle} />
          <article className="pj-fiche">
            <header className="pj-fiche-entete">
              {etiquette && <div className="pj-fiche-etiquette">{etiquette}</div>}
              {meta && meta.length > 0 && (
                <ul className="pj-fiche-meta">
                  {meta.map((m, i) => <li key={i}><span className="pj-fiche-pastille">{m}</span></li>)}
                </ul>
              )}
              <h1>{titre}</h1>
              {chapeau && <p className="pj-fiche-chapeau">{chapeau}</p>}
            </header>
            <div className="pj-fiche-corps">{children}</div>
          </article>
        </div>
      </main>
      <Footer />
    </>
  )
}
