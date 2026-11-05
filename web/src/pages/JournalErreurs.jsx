import { useState } from 'react'
import PageModule, { dateHeure } from '../components/PageModule'
import { projets } from '../lib/api'
import { useAction, useRequete } from '../lib/hooks'

const ORIGINES = [
  { code: '', libelle: 'Toutes les origines' },
  { code: 'service', libelle: 'Service' },
  { code: 'portail', libelle: 'Interface' },
  { code: 'synchro', libelle: 'Synchronisation GitHub' },
]

/** Journal des erreurs du module, pour l'équipe technique. */
export default function JournalErreurs() {
  const [origine, setOrigine] = useState('')
  const [coches, setCoches] = useState([])
  const [ouvert, setOuvert] = useState(null)
  const { donnees, erreur, chargement, recharger } = useRequete(
    () => projets.erreurs({ nombre: 200, origine }), [origine])
  const action = useAction()
  const lignes = donnees?.erreurs || []

  function cocher(id) {
    setCoches(c => (c.includes(id) ? c.filter(x => x !== id) : [...c, id]))
  }

  function purger() {
    if (!coches.length) return
    action.lancer(projets.purgerErreurs(coches), () => { setCoches([]); recharger(true) })
  }

  return (
    <PageModule
      titre="Journal des erreurs"
      sousTitre="Ce que le service, l’interface et la synchronisation GitHub ont noté. Les secrets n’y figurent jamais."
      actions={(
        <>
          <select className="pj-btn" value={origine} onChange={e => setOrigine(e.target.value)} aria-label="Origine">
            {ORIGINES.map(o => <option key={o.code} value={o.code}>{o.libelle}</option>)}
          </select>
          <button type="button" className="pj-btn" onClick={() => recharger()}>Actualiser</button>
          <button type="button" className="pj-btn pj-btn--danger" disabled={!coches.length || action.enCours} onClick={purger}>
            Supprimer {coches.length ? `(${coches.length})` : ''}
          </button>
        </>
      )}
    >
      {(erreur || action.erreur) && <div className="pj-erreur">{erreur?.message || action.erreur}</div>}
      {chargement && !donnees && <div className="pj-chargement">Chargement…</div>}
      {donnees && lignes.length === 0 && <div className="pj-vide">Aucune erreur notée.</div>}
      {lignes.length > 0 && (
        <div className="pj-panneau pj-tableau-defilant">
          <table className="pj-tableau">
            <thead>
              <tr><th /><th>Quand</th><th>Origine</th><th>Action</th><th>Message</th><th>Utilisateur</th></tr>
            </thead>
            <tbody>
              {lignes.map(l => (
                <FragmentLigne key={l.id}>
                  <tr onClick={() => setOuvert(ouvert === l.id ? null : l.id)} style={{ cursor: 'pointer' }}>
                    <td onClick={e => e.stopPropagation()}>
                      <input type="checkbox" checked={coches.includes(l.id)} onChange={() => cocher(l.id)} aria-label={`Sélectionner l’erreur ${l.id}`} />
                    </td>
                    <td className="pj-mono">{dateHeure(l.le)}</td>
                    <td>{l.origine}</td>
                    <td className="pj-mono">{l.nom || l.action}</td>
                    <td>{l.message}</td>
                    <td className="pj-mono">{l.utilisateur || '—'}</td>
                  </tr>
                  {ouvert === l.id && (l.detail || l.contexte) && (
                    <tr>
                      <td colSpan={6}>
                        {l.detail && <pre className="pj-mono" style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{l.detail}</pre>}
                        {l.contexte && <pre className="pj-mono pj-note" style={{ whiteSpace: 'pre-wrap', margin: '8px 0 0' }}>{JSON.stringify(l.contexte, null, 2)}</pre>}
                      </td>
                    </tr>
                  )}
                </FragmentLigne>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageModule>
  )
}

function FragmentLigne({ children }) { return <>{children}</> }
