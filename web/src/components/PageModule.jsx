import { Link } from 'react-router-dom'
import Nav from './portail/Nav'
import Footer from './portail/Footer'
import useEnHautDePage from '../hooks/useEnHautDePage'

/**
 * Gabarit des pages intérieures : barre, entête (fil d'Ariane, titre,
 * actions), contenu, pied. L'accueil garde son propre gabarit « portail ».
 */
export default function PageModule({ titre, sousTitre, fil, actions, children }) {
  useEnHautDePage(titre)
  return (
    <>
      <Nav />
      <main className="portal-page pj-page">
        <div className="container">
          <header className="pj-entete">
            <div>
              {fil && (
                <nav className="pj-fil" aria-label="Fil d’Ariane">
                  {fil.map((f, i) => (
                    <span key={f.to || f.libelle}>
                      {i > 0 && ' › '}
                      {f.to ? <Link to={f.to}>{f.libelle}</Link> : f.libelle}
                    </span>
                  ))}
                </nav>
              )}
              <h1>{titre}</h1>
              {sousTitre && <p>{sousTitre}</p>}
            </div>
            {actions && <div className="pj-entete-actions">{actions}</div>}
          </header>
          {children}
        </div>
      </main>
      <Footer />
    </>
  )
}

/** Jauge d'avancement, de 0 à 100. */
export function Jauge({ valeur, className = '' }) {
  const pct = Math.max(0, Math.min(100, Math.round(Number(valeur) || 0)))
  return (
    <div className={`pj-jauge ${className}`} role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="pj-jauge-piste"><div className="pj-jauge-remplie" style={{ width: `${pct}%` }} /></div>
      <span className="pj-jauge-pct">{pct}%</span>
    </div>
  )
}

/** Pastille de statut (projet, tâche ou proposition). */
export function Statut({ code, libelles }) {
  return <span className={`pj-statut pj-statut--${code}`}>{libelles?.[code] || code}</span>
}

/** Initiales d'une personne, pour l'avatar. */
export function Avatar({ nom, inconnu = false }) {
  const parties = String(nom || '').trim().split(/\s+/).filter(Boolean)
  const initiales = parties.length ? parties.slice(0, 2).map(p => p[0]).join('').toUpperCase() : '?'
  return <span className={`pj-avatar${inconnu ? ' pj-avatar--inconnu' : ''}`} aria-hidden="true">{initiales}</span>
}

const DATE_COURTE = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })
const DATE_HEURE = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export function dateCourte(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : DATE_COURTE.format(d)
}

export function dateHeure(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : DATE_HEURE.format(d)
}

/** Transforme un référentiel `[{code, libelle}]` en dictionnaire. */
export function dico(liste) {
  return Object.fromEntries((liste || []).map(e => [e.code, e.libelle]))
}
