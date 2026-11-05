import { useState } from 'react'
import { projets } from '../../lib/api'
import { useAction } from '../../lib/hooks'
import { Jauge, dateCourte, dico } from '../PageModule'
import { Dialogue, FormulaireProposition } from './Propositions'

function FormulaireTache({ projet, tache, referentiel, onFait, onAnnuler }) {
  const [v, setV] = useState({
    titre: tache?.titre || '', description: tache?.description || '', statut: tache?.statut || 'a_faire',
    assigne: tache?.assigne?.sujet || '', echeance: tache?.echeance || '', poids: tache?.poids ?? 1,
  })
  const { enCours, erreur, lancer } = useAction()
  const maj = (k) => (e) => setV(x => ({ ...x, [k]: e.target.value }))

  function envoyer(e) {
    e.preventDefault()
    const corps = {
      titre: v.titre.trim(), description: v.description, statut: v.statut,
      assigne: v.assigne || null, echeance: v.echeance || null, poids: Number(v.poids) || 1,
    }
    lancer(tache ? projets.modifierTache(projet.id, tache.id, corps) : projets.creerTache(projet.id, corps), onFait)
  }

  return (
    <form className="pj-formulaire" onSubmit={envoyer}>
      <label className="pj-champ pj-champ--large"><span>Titre *</span><input value={v.titre} onChange={maj('titre')} required autoFocus /></label>
      <label className="pj-champ pj-champ--large"><span>Description</span><textarea value={v.description} onChange={maj('description')} rows={3} /></label>
      <label className="pj-champ"><span>Statut</span>
        <select value={v.statut} onChange={maj('statut')}>
          {(referentiel?.statuts_tache || []).map(s => <option key={s.code} value={s.code}>{s.libelle}</option>)}
        </select>
      </label>
      <label className="pj-champ"><span>Assignée à</span>
        <select value={v.assigne} onChange={maj('assigne')}>
          <option value="">— personne —</option>
          {projet.membres.map(m => <option key={m.id} value={m.personne.sujet}>{m.personne.nom_complet}</option>)}
        </select>
      </label>
      <label className="pj-champ"><span>Échéance</span><input type="date" value={v.echeance} onChange={maj('echeance')} /></label>
      <label className="pj-champ"><span>Poids</span><input type="number" min="1" max="100" value={v.poids} onChange={maj('poids')} /></label>
      {erreur && <div className="pj-erreur pj-champ--large">{erreur}</div>}
      <div className="pj-formulaire-actions">
        <button type="button" className="pj-btn" onClick={onAnnuler}>Annuler</button>
        <button type="submit" className="pj-btn pj-btn--primaire" disabled={enCours || !v.titre.trim()}>{tache ? 'Enregistrer' : 'Ajouter'}</button>
      </div>
    </form>
  )
}

/** Avancement et tâches du projet. `onChange` recharge le projet. */
export default function Taches({ projet, referentiel, onChange }) {
  const [dialogue, setDialogue] = useState(null) // {mode:'tache'|'proposer', tache?}
  const [filtre, setFiltre] = useState('')
  const action = useAction()
  const statuts = dico(referentiel?.statuts_tache)
  const d = projet.droits
  const taches = projet.taches.filter(t => !filtre || t.statut === filtre)
  const nb = projet.taches.length
  const faites = projet.taches.filter(t => t.statut === 'fait').length

  function changerStatut(t, statut) {
    action.lancer(projets.modifierTache(projet.id, t.id, { statut }), onChange)
  }
  function supprimer(t) {
    if (!window.confirm(`Supprimer la tâche « ${t.titre} » ?`)) return
    action.lancer(projets.supprimerTache(projet.id, t.id), onChange)
  }
  function changerAvancement(e) {
    const val = e.target.value === '' ? null : Number(e.target.value)
    action.lancer(projets.modifier(projet.id, { avancement_manuel: val }), onChange)
  }

  return (
    <div>
      <div className="pj-grille pj-grille--2">
        <section className="pj-panneau">
          <div className="pj-panneau-titre"><h2>Avancement</h2><span className="pj-note">{faites}/{nb} tâches faites</span></div>
          <Jauge valeur={projet.avancement} />
          <p className="pj-note" style={{ marginTop: 8 }}>
            {projet.avancement_manuel == null
              ? 'Calculé depuis le poids des tâches faites.'
              : `Fixé manuellement à ${projet.avancement_manuel} %.`}
          </p>
          {d.update && (
            <label className="pj-champ" style={{ marginTop: 8 }}>
              <span>Avancement manuel (vide = calculé)</span>
              <input type="number" min="0" max="100" defaultValue={projet.avancement_manuel ?? ''} onBlur={changerAvancement} />
            </label>
          )}
        </section>
        <section className="pj-panneau">
          <div className="pj-panneau-titre"><h2>Répartition</h2></div>
          <div className="pj-chiffres">
            {(referentiel?.statuts_tache || []).map(s => (
              <button key={s.code} type="button" className={`pj-chiffre pj-bouton-nu${filtre === s.code ? ' is-active' : ''}`}
                onClick={() => setFiltre(filtre === s.code ? '' : s.code)}>
                <b>{projet.taches_par_statut?.[s.code] ?? 0}</b><span>{s.libelle}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <section className="pj-panneau">
        <div className="pj-panneau-titre">
          <h2>Tâches {filtre && <span className="pj-note">· {statuts[filtre]}</span>}</h2>
          <div className="pj-formulaire-actions">
            {d.creer_tache && <button type="button" className="pj-btn pj-btn--primaire pj-btn--petit" onClick={() => setDialogue({ mode: 'tache' })}>Nouvelle tâche</button>}
            {!d.creer_tache && d.proposer && <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue({ mode: 'proposer', type: 'ajouter_tache' })}>Proposer une tâche</button>}
          </div>
        </div>
        {action.erreur && <div className="pj-erreur">{action.erreur}</div>}
        {taches.length === 0 && <div className="pj-vide">Aucune tâche{filtre ? ' dans cet état' : ''}.</div>}
        <ul className="pj-taches">
          {taches.map(t => {
            const peutModifier = d.update || (t.assigne && t.assigne.id === projet.moi_id)
            return (
              <li key={t.id} className={`pj-tache${t.statut === 'fait' ? ' is-fait' : ''}`}>
                <div>
                  <div className="pj-tache-titre">{t.titre}</div>
                  <div className="pj-tache-meta">
                    {t.assigne ? t.assigne.nom_complet : 'Non assignée'}
                    {t.echeance ? ` · pour le ${dateCourte(t.echeance)}` : ''}
                    {` · poids ${t.poids}`}
                    {t.description ? ` · ${t.description}` : ''}
                  </div>
                </div>
                <div className="pj-formulaire-actions">
                  {peutModifier ? (
                    <select value={t.statut} onChange={e => changerStatut(t, e.target.value)} aria-label="Statut" className={`pj-statut pj-statut--${t.statut}`}>
                      {(referentiel?.statuts_tache || []).map(s => <option key={s.code} value={s.code}>{s.libelle}</option>)}
                    </select>
                  ) : (
                    <span className={`pj-statut pj-statut--${t.statut}`}>{statuts[t.statut] || t.statut}</span>
                  )}
                  {d.update && <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue({ mode: 'tache', tache: t })}>Modifier</button>}
                  {!d.update && d.proposer && <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue({ mode: 'proposer', type: 'modifier_tache', tache: t })}>Proposer</button>}
                  {d.update && <button type="button" className="pj-btn pj-btn--petit pj-btn--danger" onClick={() => supprimer(t)} aria-label="Supprimer">×</button>}
                </div>
              </li>
            )
          })}
        </ul>
      </section>

      {dialogue?.mode === 'tache' && (
        <Dialogue titre={dialogue.tache ? 'Modifier la tâche' : 'Nouvelle tâche'} onFermer={() => setDialogue(null)}>
          <FormulaireTache projet={projet} tache={dialogue.tache} referentiel={referentiel}
            onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
      {dialogue?.mode === 'proposer' && (
        <Dialogue titre={dialogue.type === 'ajouter_tache' ? 'Proposer une tâche' : `Proposer une modification · ${dialogue.tache.titre}`} onFermer={() => setDialogue(null)}>
          <FormulaireProposition projet={projet} referentiel={referentiel} type={dialogue.type} cible={dialogue.tache}
            onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
    </div>
  )
}
