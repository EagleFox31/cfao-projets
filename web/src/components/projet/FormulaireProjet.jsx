import { useState } from 'react'
import { projets } from '../../lib/api'
import { useAction } from '../../lib/hooks'

const VIDE = { nom: '', description: '', statut: 'propose', date_debut: '', date_fin: '', avancement_manuel: '', scope_node: '', brand: '' }

/** Création ou modification d'un projet (champs du contrat `projet`). */
export default function FormulaireProjet({ projet, referentiel, onEnregistre, onAnnuler }) {
  const [v, setV] = useState(() => (projet ? {
    ...VIDE,
    ...Object.fromEntries(Object.keys(VIDE).map(k => [k, projet[k] ?? ''])),
  } : VIDE))
  const { enCours, erreur, lancer } = useAction()
  const maj = (k) => (e) => setV(x => ({ ...x, [k]: e.target.value }))

  function envoyer(e) {
    e.preventDefault()
    const corps = {
      nom: v.nom.trim(),
      description: v.description,
      statut: v.statut,
      date_debut: v.date_debut || null,
      date_fin: v.date_fin || null,
      avancement_manuel: v.avancement_manuel === '' ? null : Number(v.avancement_manuel),
      scope_node: v.scope_node || null,
      brand: v.brand || null,
    }
    lancer(projet ? projets.modifier(projet.id, corps) : projets.creer(corps), (r) => onEnregistre?.(r))
  }

  return (
    <form className="pj-formulaire" onSubmit={envoyer}>
      <label className="pj-champ pj-champ--large"><span>Nom *</span><input value={v.nom} onChange={maj('nom')} required maxLength={200} autoFocus /></label>
      <label className="pj-champ pj-champ--large"><span>Description</span><textarea value={v.description} onChange={maj('description')} rows={3} /></label>
      <label className="pj-champ"><span>Statut</span>
        <select value={v.statut} onChange={maj('statut')}>
          {(referentiel?.statuts_projet || []).map(s => <option key={s.code} value={s.code}>{s.libelle}</option>)}
        </select>
      </label>
      <label className="pj-champ"><span>Avancement manuel (%)</span>
        <input type="number" min="0" max="100" value={v.avancement_manuel} onChange={maj('avancement_manuel')} placeholder="calculé depuis les tâches" />
      </label>
      <label className="pj-champ"><span>Début</span><input type="date" value={v.date_debut} onChange={maj('date_debut')} /></label>
      <label className="pj-champ"><span>Fin prévue</span><input type="date" value={v.date_fin} onChange={maj('date_fin')} /></label>
      <label className="pj-champ"><span>Périmètre (scope)</span><input value={v.scope_node} onChange={maj('scope_node')} placeholder="facultatif" /></label>
      <label className="pj-champ"><span>Marque</span><input value={v.brand} onChange={maj('brand')} placeholder="facultatif" /></label>
      {erreur && <div className="pj-erreur pj-champ--large">{erreur}</div>}
      <div className="pj-formulaire-actions">
        {onAnnuler && <button type="button" className="pj-btn" onClick={onAnnuler}>Annuler</button>}
        <button type="submit" className="pj-btn pj-btn--primaire" disabled={enCours || !v.nom.trim()}>
          {projet ? 'Enregistrer' : 'Créer le projet'}
        </button>
      </div>
    </form>
  )
}
