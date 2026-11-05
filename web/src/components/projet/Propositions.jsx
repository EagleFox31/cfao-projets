import { useState } from 'react'
import { Link } from 'react-router-dom'
import { projets } from '../../lib/api'
import { useAction } from '../../lib/hooks'
import { Statut, dateHeure } from '../PageModule'

const LIBELLES_CHAMPS = {
  nom: 'Nom', description: 'Description', statut: 'Statut', date_debut: 'Début', date_fin: 'Fin',
  avancement_manuel: 'Avancement (%)', titre: 'Titre', poids: 'Poids', echeance: 'Échéance',
  assigne: 'Assigné à', personne: 'Personne', role_membre: 'Rôle', brand: 'Marque', scope_node: 'Périmètre',
}

export function ContenuProposition({ proposition, referentiel }) {
  const statuts = { ...dicoDe(referentiel?.statuts_projet), ...dicoDe(referentiel?.statuts_tache) }
  const roles = dicoDe(referentiel?.roles_membre)
  return (
    <div className="pj-proposition-contenu">
      <dl>
        {Object.entries(proposition.contenu || {}).map(([k, v]) => (
          <FragmentDl key={k}>
            <dt>{LIBELLES_CHAMPS[k] || k}</dt>
            <dd>{k === 'statut' ? (statuts[v] || v) : k === 'role_membre' ? (roles[v] || v) : String(v ?? '—')}</dd>
          </FragmentDl>
        ))}
      </dl>
      {proposition.motif && <p className="pj-note" style={{ marginTop: 6 }}>Motif : {proposition.motif}</p>}
    </div>
  )
}

function FragmentDl({ children }) { return <>{children}</> }
function dicoDe(liste) { return Object.fromEntries((liste || []).map(e => [e.code, e.libelle])) }

/**
 * Une proposition, avec ses boutons de décision si `peutDecider`.
 * `onDecision(proposition)` reçoit la proposition mise à jour.
 */
export function CarteProposition({ proposition, referentiel, peutDecider = false, avecProjet = false, onDecision }) {
  const [commentaire, setCommentaire] = useState('')
  const { enCours, erreur, lancer } = useAction()
  const types = dicoDe(referentiel?.types_proposition)
  const statutsProp = { soumise: 'En attente', acceptee: 'Acceptée', refusee: 'Refusée' }

  function decider(decision) {
    lancer(projets.decider(proposition.id, { decision, commentaire: commentaire.trim() }), (r) => onDecision?.(r))
  }

  return (
    <article className="pj-proposition">
      <div className="pj-proposition-tete">
        <div>
          <strong>{types[proposition.type] || proposition.type}</strong>
          {avecProjet && <> · <Link to={`/projets/${proposition.projet.id}`}>{proposition.projet.nom}</Link></>}
          <div className="pj-note">
            par {proposition.auteur?.nom_complet || proposition.auteur?.sujet} · {dateHeure(proposition.soumise_le)}
            {proposition.cible_id ? ` · cible n° ${proposition.cible_id}` : ''}
          </div>
        </div>
        <Statut code={proposition.statut} libelles={statutsProp} />
      </div>
      <ContenuProposition proposition={proposition} referentiel={referentiel} />
      {proposition.statut !== 'soumise' && (
        <p className="pj-note">
          {statutsProp[proposition.statut]} par {proposition.decideur?.nom_complet || '—'} le {dateHeure(proposition.decidee_le)}
          {proposition.commentaire ? ` — « ${proposition.commentaire} »` : ''}
        </p>
      )}
      {peutDecider && proposition.statut === 'soumise' && (
        <div className="pj-proposition-actions">
          <input placeholder="Commentaire (facultatif)" value={commentaire} onChange={e => setCommentaire(e.target.value)} />
          <button type="button" className="pj-btn pj-btn--petit pj-btn--primaire" disabled={enCours} onClick={() => decider('acceptee')}>Accepter</button>
          <button type="button" className="pj-btn pj-btn--petit pj-btn--danger" disabled={enCours} onClick={() => decider('refusee')}>Refuser</button>
        </div>
      )}
      {erreur && <div className="pj-erreur" style={{ marginTop: 8 }}>{erreur}</div>}
    </article>
  )
}

/**
 * Formulaire « proposer une modification » : un type, la cible, le contenu.
 * Le service valide le contenu comme s'il était appliqué ; l'erreur revient
 * ici telle quelle.
 */
export function FormulaireProposition({ projet, referentiel, type, cible, onFait, onAnnuler }) {
  const [contenu, setContenu] = useState({})
  const [motif, setMotif] = useState('')
  const { enCours, erreur, lancer } = useAction()
  const statutsProjet = referentiel?.statuts_projet || []
  const statutsTache = referentiel?.statuts_tache || []
  const roles = referentiel?.roles_membre || []

  const maj = (k) => (e) => setContenu(c => {
    const v = e.target.value
    if (v === '') { const { [k]: _, ...reste } = c; return reste }
    return { ...c, [k]: k === 'poids' || k === 'avancement_manuel' ? Number(v) : v }
  })

  function envoyer(e) {
    e.preventDefault()
    lancer(projets.proposer(projet.id, { type, cible_id: cible?.id, contenu, motif: motif.trim() }), (r) => onFait?.(r))
  }

  return (
    <form className="pj-formulaire" onSubmit={envoyer}>
      {type === 'modifier_projet' && (
        <>
          <label className="pj-champ"><span>Nom</span><input defaultValue={projet.nom} onChange={maj('nom')} /></label>
          <label className="pj-champ"><span>Statut</span>
            <select defaultValue="" onChange={maj('statut')}>
              <option value="">— inchangé —</option>
              {statutsProjet.map(s => <option key={s.code} value={s.code}>{s.libelle}</option>)}
            </select>
          </label>
          <label className="pj-champ"><span>Avancement manuel (%)</span><input type="number" min="0" max="100" onChange={maj('avancement_manuel')} /></label>
          <label className="pj-champ pj-champ--large"><span>Description</span><textarea defaultValue={projet.description} onChange={maj('description')} /></label>
        </>
      )}
      {(type === 'ajouter_tache' || type === 'modifier_tache') && (
        <>
          <label className="pj-champ"><span>Titre</span><input defaultValue={cible?.titre || ''} onChange={maj('titre')} required={type === 'ajouter_tache'} /></label>
          <label className="pj-champ"><span>Statut</span>
            <select defaultValue="" onChange={maj('statut')}>
              <option value="">{type === 'ajouter_tache' ? 'À faire' : '— inchangé —'}</option>
              {statutsTache.map(s => <option key={s.code} value={s.code}>{s.libelle}</option>)}
            </select>
          </label>
          <label className="pj-champ"><span>Poids</span><input type="number" min="1" max="100" onChange={maj('poids')} /></label>
          <label className="pj-champ"><span>Échéance</span><input type="date" onChange={maj('echeance')} /></label>
          <label className="pj-champ pj-champ--large"><span>Description</span><textarea onChange={maj('description')} /></label>
        </>
      )}
      {type === 'ajouter_membre' && (
        <>
          <label className="pj-champ"><span>Identifiant ou e-mail de la personne</span><input onChange={maj('personne')} required /></label>
          <label className="pj-champ"><span>Rôle</span>
            <select defaultValue="contributeur" onChange={maj('role_membre')}>
              {roles.map(r => <option key={r.code} value={r.code}>{r.libelle}</option>)}
            </select>
          </label>
        </>
      )}
      <label className="pj-champ pj-champ--large"><span>Motif (envoyé au chef de projet)</span><input value={motif} onChange={e => setMotif(e.target.value)} /></label>
      {erreur && <div className="pj-erreur pj-champ--large">{erreur}</div>}
      <div className="pj-formulaire-actions">
        {onAnnuler && <button type="button" className="pj-btn" onClick={onAnnuler}>Annuler</button>}
        <button type="submit" className="pj-btn pj-btn--primaire" disabled={enCours || Object.keys(contenu).length === 0}>Soumettre la proposition</button>
      </div>
    </form>
  )
}

/** Boîte modale légère. */
export function Dialogue({ titre, onFermer, children }) {
  return (
    <div className="pj-dialogue-fond" onMouseDown={(e) => { if (e.target === e.currentTarget) onFermer?.() }}>
      <div className="pj-dialogue" role="dialog" aria-modal="true" aria-label={titre}>
        <h2>{titre}</h2>
        {children}
      </div>
    </div>
  )
}
