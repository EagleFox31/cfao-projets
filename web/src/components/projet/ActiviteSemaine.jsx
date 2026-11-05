import { useState } from 'react'
import { Link } from 'react-router-dom'
import { projets } from '../../lib/api'
import { useRequete } from '../../lib/hooks'
import { JOURS_COURTS, codeSemaine, decalerSemaine, libelleSemaine, lundiDuCode } from '../../lib/semaine'
import { Avatar, dateHeure } from '../PageModule'

function Barres({ jours, max }) {
  const plafond = Math.max(1, max ?? Math.max(...jours))
  return (
    <div className="pj-jours" aria-hidden="true">
      {jours.map((n, i) => (
        <div key={i} className="pj-jour" title={`${JOURS_COURTS[i]} : ${n} commit${n > 1 ? 's' : ''}`}>
          <div className="pj-jour-barre" style={{ height: `${Math.max(6, (n / plafond) * 100)}%`, opacity: n ? 0.9 : 0.2 }} />
          <span className="pj-jour-lib">{JOURS_COURTS[i][0]}</span>
        </div>
      ))}
    </div>
  )
}

export function SelecteurSemaine({ semaine, onChange }) {
  const courante = codeSemaine()
  return (
    <div className="pj-semaine">
      <button type="button" className="pj-btn pj-btn--petit" onClick={() => onChange(decalerSemaine(semaine, -1))} aria-label="Semaine précédente">←</button>
      <strong>Semaine {semaine.slice(6)}</strong>
      <span className="pj-note">{libelleSemaine(semaine)}</span>
      <button type="button" className="pj-btn pj-btn--petit" onClick={() => onChange(decalerSemaine(semaine, 1))}
        disabled={semaine >= courante} aria-label="Semaine suivante">→</button>
      {semaine !== courante && (
        <button type="button" className="pj-btn pj-btn--petit" onClick={() => onChange(courante)}>Cette semaine</button>
      )}
      <input type="week" value={semaine} onChange={e => { if (lundiDuCode(e.target.value)) onChange(e.target.value) }} aria-label="Choisir une semaine" />
    </div>
  )
}

function Diff({ depots }) {
  return (
    <div className="pj-liens">
      {depots.map(d => (
        <a key={`${d.depot}-${d.premier}`} className="pj-lien-depot" href={d.diff} target="_blank" rel="noreferrer"
          title={`${d.commits} commit${d.commits > 1 ? 's' : ''} · +${d.additions} / −${d.deletions}`}>
          {d.depot.split('/')[1] || d.depot} · diff
        </a>
      ))}
    </div>
  )
}

/**
 * Le travail d'une semaine : totaux, répartition par jour, puis une ligne
 * par personne avec ses dépôts, le lien vers le diff et ses derniers
 * commits. `projetId` absent : toutes les activités visibles.
 */
export default function ActiviteSemaine({ projetId, semaineInitiale, compact = false }) {
  const [semaine, setSemaine] = useState(semaineInitiale || codeSemaine())
  const [ouvert, setOuvert] = useState(null)
  const { donnees, erreur, chargement } = useRequete(
    () => (projetId ? projets.activite(projetId, semaine) : projets.activiteSemaine(semaine)),
    [projetId, semaine],
  )

  const total = donnees?.total || { commits: 0, additions: 0, deletions: 0, fichiers: 0 }
  const personnes = donnees?.personnes || []
  const maxJour = Math.max(1, ...(donnees?.jours || [0]))

  return (
    <div>
      <div className="pj-panneau-titre">
        <SelecteurSemaine semaine={semaine} onChange={setSemaine} />
      </div>
      {erreur && <div className="pj-erreur">{erreur.message}</div>}
      {chargement && !donnees && <div className="pj-chargement">Lecture des commits…</div>}
      {donnees && (
        <>
          <div className="pj-chiffres">
            <div className="pj-chiffre"><b>{total.commits}</b><span>commits</span></div>
            <div className="pj-chiffre"><b className="pj-plus">+{total.additions}</b><span>lignes ajoutées</span></div>
            <div className="pj-chiffre"><b className="pj-moins">−{total.deletions}</b><span>lignes retirées</span></div>
            <div className="pj-chiffre"><b>{personnes.length}</b><span>contributeur{personnes.length > 1 ? 's' : ''}</span></div>
            <div className="pj-chiffre" style={{ gridColumn: 'span 2' }}>
              <Barres jours={donnees.jours} max={maxJour} />
              <span>commits par jour</span>
            </div>
          </div>

          {personnes.length === 0 ? (
            <div className="pj-vide">Aucun commit lu sur cette semaine. Vérifiez les dépôts rattachés et leur dernière synchronisation.</div>
          ) : (
            <div className="pj-tableau-defilant">
              <table className="pj-tableau">
                <thead>
                  <tr>
                    <th>Personne</th>
                    <th className="num">Commits</th>
                    <th className="num">+ / −</th>
                    {!compact && <th>Par jour</th>}
                    <th>Dépôts et diff de la semaine</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {personnes.map(p => {
                    const cle = p.personne?.id ? `p${p.personne.id}` : p.login || p.nom
                    const estOuvert = ouvert === cle
                    return (
                      <FragmentLigne key={cle}>
                        <tr>
                          <td>
                            <div className="pj-personne">
                              <Avatar nom={p.nom} inconnu={!p.personne} />
                              <div>
                                <div>{p.nom || p.login || 'Inconnu'}</div>
                                <div className="pj-note pj-mono">{p.login ? `@${p.login}` : ''}{!p.personne && ' · non rattaché'}</div>
                              </div>
                            </div>
                          </td>
                          <td className="num">{p.commits}</td>
                          <td className="num"><span className="pj-plus">+{p.additions}</span> / <span className="pj-moins">−{p.deletions}</span></td>
                          {!compact && <td style={{ minWidth: 120 }}><Barres jours={p.jours} max={maxJour} /></td>}
                          <td>
                            {!projetId && (
                              <div className="pj-note" style={{ marginBottom: 4 }}>
                                {[...new Set(p.depots.map(d => d.projet_id))].map(id => {
                                  const d = p.depots.find(x => x.projet_id === id)
                                  return <Link key={id} to={`/projets/${id}`} style={{ marginRight: 8 }}>{d.projet}</Link>
                                })}
                              </div>
                            )}
                            <Diff depots={p.depots} />
                          </td>
                          <td className="num">
                            <button type="button" className="pj-btn pj-btn--petit" onClick={() => setOuvert(estOuvert ? null : cle)}
                              aria-expanded={estOuvert}>
                              {estOuvert ? 'Replier' : 'Commits'}
                            </button>
                          </td>
                        </tr>
                        {estOuvert && (
                          <tr>
                            <td colSpan={compact ? 5 : 6}>
                              <ul className="pj-commits">
                                {p.derniers.map(c => (
                                  <li key={c.sha + c.depot}>
                                    <a className="pj-mono" href={c.url} target="_blank" rel="noreferrer">{c.sha}</a>
                                    <span>{c.message}</span>
                                    <span className="pj-note">{c.depot} · {dateHeure(c.date)} · <span className="pj-plus">+{c.additions}</span>/<span className="pj-moins">−{c.deletions}</span></span>
                                  </li>
                                ))}
                              </ul>
                            </td>
                          </tr>
                        )}
                      </FragmentLigne>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function FragmentLigne({ children }) {
  return <>{children}</>
}
