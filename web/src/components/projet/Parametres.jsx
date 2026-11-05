import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { projets } from '../../lib/api'
import { useAction } from '../../lib/hooks'
import { dateHeure } from '../PageModule'
import FormulaireProjet from './FormulaireProjet'
import { Dialogue, FormulaireProposition } from './Propositions'

function AjoutDepot({ projet, onFait, onAnnuler }) {
  const [depot, setDepot] = useState('')
  const [jeton, setJeton] = useState('')
  const [toutes, setToutes] = useState(false)
  const { enCours, erreur, lancer } = useAction()
  const valide = /^[\w.-]+\/[\w.-]+$/.test(depot.trim())

  function envoyer(e) {
    e.preventDefault()
    lancer(projets.ajouterDepot(projet.id, { depot: depot.trim(), jeton_variable: jeton.trim() || null, toutes_branches: toutes }), onFait)
  }

  return (
    <form className="pj-formulaire" onSubmit={envoyer}>
      <label className="pj-champ pj-champ--large"><span>Dépôt GitHub (owner/nom) *</span>
        <input value={depot} onChange={e => setDepot(e.target.value)} placeholder="organisation/depot" required autoFocus />
      </label>
      <label className="pj-champ"><span>Variable d’environnement du jeton</span>
        <input value={jeton} onChange={e => setJeton(e.target.value)} placeholder="GITHUB_TOKEN (défaut)" />
      </label>
      <label className="pj-champ" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={toutes} onChange={e => setToutes(e.target.checked)} />
        <span>Lire toutes les branches (sinon la branche par défaut)</span>
      </label>
      <p className="pj-note pj-champ--large">Le jeton n’est jamais saisi ici : on nomme seulement la variable que le service lit dans son environnement.</p>
      {erreur && <div className="pj-erreur pj-champ--large">{erreur}</div>}
      <div className="pj-formulaire-actions">
        <button type="button" className="pj-btn" onClick={onAnnuler}>Annuler</button>
        <button type="submit" className="pj-btn pj-btn--primaire" disabled={enCours || !valide}>Rattacher</button>
      </div>
    </form>
  )
}

/** Fiche, dépôts GitHub et suppression. */
export default function Parametres({ projet, referentiel, onChange }) {
  const navigate = useNavigate()
  const [dialogue, setDialogue] = useState(null)
  const action = useAction()
  const [synchroEnCours, setSynchroEnCours] = useState(null)
  const d = projet.droits

  function synchroniser(dep) {
    setSynchroEnCours(dep.id)
    action.lancer(projets.synchroniser(projet.id, dep.id), onChange).finally(() => setSynchroEnCours(null))
  }
  function retirerDepot(dep) {
    if (!window.confirm(`Détacher le dépôt ${dep.depot} ? Les commits déjà lus seront oubliés.`)) return
    action.lancer(projets.retirerDepot(projet.id, dep.id), onChange)
  }
  function supprimerProjet() {
    if (!window.confirm(`Supprimer définitivement le projet « ${projet.nom} » et tout ce qu’il contient ?`)) return
    action.lancer(projets.supprimer(projet.id), () => navigate('/projets'))
  }

  return (
    <div>
      <section className="pj-panneau">
        <div className="pj-panneau-titre">
          <h2>Fiche du projet</h2>
          {d.update
            ? <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue('fiche')}>Modifier</button>
            : d.proposer && <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue('proposer')}>Proposer une modification</button>}
        </div>
        <dl className="pj-proposition-contenu">
          <dt>Description</dt><dd>{projet.description || '—'}</dd>
          <dt>Période</dt><dd>{projet.date_debut || '…'} → {projet.date_fin || '…'}</dd>
          <dt>Périmètre</dt><dd>{projet.scope_node || '—'}{projet.brand ? ` · ${projet.brand}` : ''}</dd>
          <dt>Créé par</dt><dd>{projet.cree_par?.nom_complet || '—'} le {dateHeure(projet.cree_le)}</dd>
        </dl>
      </section>

      <section className="pj-panneau">
        <div className="pj-panneau-titre">
          <h2>Dépôts GitHub <span className="pj-onglet-nb">{projet.depots.length}</span></h2>
          {d.update && <button type="button" className="pj-btn pj-btn--primaire pj-btn--petit" onClick={() => setDialogue('depot')}>Rattacher un dépôt</button>}
        </div>
        {action.erreur && <div className="pj-erreur">{action.erreur}</div>}
        {projet.depots.length === 0 && <div className="pj-vide">Aucun dépôt rattaché : l’activité GitHub restera vide.</div>}
        {projet.depots.length > 0 && (
          <div className="pj-tableau-defilant">
            <table className="pj-tableau">
              <thead><tr><th>Dépôt</th><th>Branches</th><th className="num">Commits lus</th><th>Dernière synchro</th><th /></tr></thead>
              <tbody>
                {projet.depots.map(dep => (
                  <tr key={dep.id}>
                    <td><a className="pj-mono" href={dep.url} target="_blank" rel="noreferrer">{dep.depot}</a>
                      <div className="pj-note">jeton : {dep.jeton_variable || 'GITHUB_TOKEN'}</div></td>
                    <td>{dep.toutes_branches ? 'toutes' : (dep.branche_par_defaut || 'par défaut')}</td>
                    <td className="num">{dep.commits}</td>
                    <td>
                      {dep.derniere_synchro ? dateHeure(dep.derniere_synchro) : <span className="pj-note">jamais</span>}
                      {dep.derniere_erreur && <div className="pj-erreur" style={{ marginTop: 4 }}>{dep.derniere_erreur}</div>}
                    </td>
                    <td className="num">
                      {d.sync && <button type="button" className="pj-btn pj-btn--petit" disabled={synchroEnCours === dep.id} onClick={() => synchroniser(dep)}>
                        {synchroEnCours === dep.id ? 'Lecture…' : 'Synchroniser'}
                      </button>}{' '}
                      {d.update && <button type="button" className="pj-btn pj-btn--petit pj-btn--danger" onClick={() => retirerDepot(dep)}>Détacher</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="pj-note" style={{ marginTop: 10 }}>
          Les commits sont relus périodiquement par le service et à chaque push si le webhook GitHub est configuré.
        </p>
      </section>

      {d.delete && (
        <section className="pj-panneau">
          <div className="pj-panneau-titre"><h2>Zone sensible</h2></div>
          <button type="button" className="pj-btn pj-btn--danger" onClick={supprimerProjet} disabled={action.enCours}>Supprimer le projet</button>
        </section>
      )}

      {dialogue === 'fiche' && (
        <Dialogue titre="Modifier le projet" onFermer={() => setDialogue(null)}>
          <FormulaireProjet projet={projet} referentiel={referentiel} onAnnuler={() => setDialogue(null)} onEnregistre={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
      {dialogue === 'proposer' && (
        <Dialogue titre="Proposer une modification du projet" onFermer={() => setDialogue(null)}>
          <FormulaireProposition projet={projet} referentiel={referentiel} type="modifier_projet" onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
      {dialogue === 'depot' && (
        <Dialogue titre="Rattacher un dépôt GitHub" onFermer={() => setDialogue(null)}>
          <AjoutDepot projet={projet} onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
    </div>
  )
}
