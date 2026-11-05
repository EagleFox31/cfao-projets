import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PageModule, { Jauge, Statut, dateCourte, dico } from '../components/PageModule'
import { Dialogue } from '../components/projet/Propositions'
import FormulaireProjet from '../components/projet/FormulaireProjet'
import { projets } from '../lib/api'
import { useReferentiel, useRequete } from '../lib/hooks'

/** Les projets que je vois, filtrables par statut, et la création. */
export default function Projets() {
  const navigate = useNavigate()
  const referentiel = useReferentiel()
  const [statut, setStatut] = useState('')
  const [creation, setCreation] = useState(false)
  const { donnees, erreur, chargement } = useRequete(() => projets.liste(statut || undefined), [statut])
  const liste = donnees?.projets || []
  const statuts = dico(referentiel?.statuts_projet)
  const roles = dico(referentiel?.roles_membre)

  const parStatut = useMemo(() => {
    const c = {}
    liste.forEach(p => { c[p.statut] = (c[p.statut] || 0) + 1 })
    return c
  }, [liste])

  return (
    <PageModule
      titre="Projets"
      sousTitre="Chaque projet rassemble ses membres, ses tâches, ses dépôts GitHub et les propositions qu’il reçoit."
      actions={referentiel?.peut_creer_projet && (
        <button type="button" className="pj-btn pj-btn--primaire" onClick={() => setCreation(true)}>Nouveau projet</button>
      )}
    >
      <div className="pj-onglets" role="tablist" aria-label="Filtrer par statut">
        <button type="button" role="tab" className={`pj-onglet${statut === '' ? ' is-active' : ''}`} aria-selected={statut === ''} onClick={() => setStatut('')}>
          Tous
        </button>
        {(referentiel?.statuts_projet || []).map(s => (
          <button key={s.code} type="button" role="tab" className={`pj-onglet${statut === s.code ? ' is-active' : ''}`}
            aria-selected={statut === s.code} onClick={() => setStatut(s.code)}>
            {s.libelle}{statut === '' && parStatut[s.code] ? <span className="pj-onglet-nb">{parStatut[s.code]}</span> : null}
          </button>
        ))}
      </div>

      {erreur && <div className="pj-erreur">{erreur.message}</div>}
      {chargement && !donnees && <div className="pj-chargement">Chargement…</div>}
      {donnees && liste.length === 0 && (
        <div className="pj-vide">Aucun projet{statut ? ' avec ce statut' : ''}.</div>
      )}

      {liste.length > 0 && (
        <div className="pj-panneau pj-tableau-defilant">
          <table className="pj-tableau">
            <thead>
              <tr>
                <th>Projet</th><th>Statut</th><th style={{ minWidth: 160 }}>Avancement</th>
                <th className="num">Membres</th><th>Mon rôle</th><th>Échéance</th><th className="num">Propositions</th>
              </tr>
            </thead>
            <tbody>
              {liste.map(p => (
                <tr key={p.id} onClick={() => navigate(`/projets/${p.id}`)} style={{ cursor: 'pointer' }}>
                  <td>
                    <Link to={`/projets/${p.id}`} onClick={e => e.stopPropagation()}><strong>{p.nom}</strong></Link>
                    {p.description && <div className="pj-note" style={{ maxWidth: 420, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.description}</div>}
                  </td>
                  <td><Statut code={p.statut} libelles={statuts} /></td>
                  <td><Jauge valeur={p.avancement} /></td>
                  <td className="num">{p.nb_membres}</td>
                  <td>{p.mon_role ? (roles[p.mon_role] || p.mon_role) : <span className="pj-note">—</span>}</td>
                  <td>{dateCourte(p.date_fin)}</td>
                  <td className="num">{p.propositions_en_attente || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {creation && (
        <Dialogue titre="Nouveau projet" onFermer={() => setCreation(false)}>
          <FormulaireProjet
            referentiel={referentiel}
            onAnnuler={() => setCreation(false)}
            onEnregistre={(p) => { setCreation(false); navigate(`/projets/${p.id}`) }}
          />
        </Dialogue>
      )}
    </PageModule>
  )
}
