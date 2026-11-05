import { useEffect, useState } from 'react'
import { projets } from '../../lib/api'
import { useAction } from '../../lib/hooks'
import { Avatar, dateCourte, dico } from '../PageModule'
import { Dialogue, FormulaireProposition } from './Propositions'

function AjoutMembre({ projet, referentiel, onFait, onAnnuler }) {
  const [q, setQ] = useState('')
  const [resultats, setResultats] = useState([])
  const [choix, setChoix] = useState(null)
  const [role, setRole] = useState('contributeur')
  const { enCours, erreur, lancer } = useAction()
  const deja = new Set(projet.membres.map(m => m.personne.sujet))

  useEffect(() => {
    if (q.trim().length < 2) { setResultats([]); return undefined }
    const t = setTimeout(() => {
      projets.personnes(q.trim()).then(r => setResultats((r.personnes || []).filter(p => !deja.has(p.sujet)).slice(0, 8))).catch(() => setResultats([]))
    }, 250)
    return () => clearTimeout(t)
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  function envoyer(e) {
    e.preventDefault()
    if (!choix) return
    lancer(projets.ajouterMembre(projet.id, { personne: choix.sujet, role_membre: role }), onFait)
  }

  return (
    <form className="pj-formulaire" onSubmit={envoyer}>
      <label className="pj-champ pj-champ--large"><span>Rechercher une personne (nom, e-mail, identifiant GitHub)</span>
        <input value={q} onChange={e => { setQ(e.target.value); setChoix(null) }} autoFocus />
      </label>
      {resultats.length > 0 && !choix && (
        <ul className="pj-taches pj-champ--large">
          {resultats.map(p => (
            <li key={p.sujet} className="pj-tache">
              <div className="pj-personne"><Avatar nom={p.nom_complet} /><div>{p.nom_complet}<div className="pj-note">{p.email}{p.github_login ? ` · @${p.github_login}` : ''}</div></div></div>
              <button type="button" className="pj-btn pj-btn--petit" onClick={() => setChoix(p)}>Choisir</button>
            </li>
          ))}
        </ul>
      )}
      {q.trim().length >= 2 && resultats.length === 0 && !choix && (
        <p className="pj-note pj-champ--large">Personne ne correspond parmi les comptes connus du service.</p>
      )}
      {choix && <p className="pj-succes pj-champ--large">{choix.nom_complet} ({choix.email})</p>}
      <label className="pj-champ"><span>Rôle</span>
        <select value={role} onChange={e => setRole(e.target.value)}>
          {(referentiel?.roles_membre || []).map(r => <option key={r.code} value={r.code}>{r.libelle}</option>)}
        </select>
      </label>
      {erreur && <div className="pj-erreur pj-champ--large">{erreur}</div>}
      <div className="pj-formulaire-actions">
        <button type="button" className="pj-btn" onClick={onAnnuler}>Annuler</button>
        <button type="submit" className="pj-btn pj-btn--primaire" disabled={enCours || !choix}>Ajouter</button>
      </div>
    </form>
  )
}

/** Les membres du projet, leur rôle, et l'ajout si autorisé. */
export default function Equipe({ projet, referentiel, onChange }) {
  const [dialogue, setDialogue] = useState(null)
  const action = useAction()
  const roles = dico(referentiel?.roles_membre)
  const d = projet.droits

  function changerRole(m, role_membre) {
    action.lancer(projets.modifierMembre(projet.id, m.id, { role_membre }), onChange)
  }
  function retirer(m) {
    if (!window.confirm(`Retirer ${m.personne.nom_complet} du projet ?`)) return
    action.lancer(projets.retirerMembre(projet.id, m.id), onChange)
  }

  return (
    <section className="pj-panneau">
      <div className="pj-panneau-titre">
        <h2>Équipe <span className="pj-onglet-nb">{projet.membres.length}</span></h2>
        <div>
          {d.manage_members && <button type="button" className="pj-btn pj-btn--primaire pj-btn--petit" onClick={() => setDialogue('ajout')}>Ajouter un membre</button>}
          {!d.manage_members && d.proposer && <button type="button" className="pj-btn pj-btn--petit" onClick={() => setDialogue('proposer')}>Proposer un membre</button>}
        </div>
      </div>
      {action.erreur && <div className="pj-erreur">{action.erreur}</div>}
      <div className="pj-tableau-defilant">
        <table className="pj-tableau">
          <thead><tr><th>Personne</th><th>E-mail</th><th>GitHub</th><th>Rôle</th><th>Depuis</th><th /></tr></thead>
          <tbody>
            {projet.membres.map(m => (
              <tr key={m.id}>
                <td><div className="pj-personne"><Avatar nom={m.personne.nom_complet} /><span>{m.personne.nom_complet}</span></div></td>
                <td className="pj-note">{m.personne.email}</td>
                <td className="pj-mono">{m.personne.github_login ? `@${m.personne.github_login}` : <span className="pj-note">non renseigné</span>}</td>
                <td>
                  {d.manage_members ? (
                    <select value={m.role_membre} onChange={e => changerRole(m, e.target.value)} aria-label="Rôle">
                      {(referentiel?.roles_membre || []).map(r => <option key={r.code} value={r.code}>{r.libelle}</option>)}
                    </select>
                  ) : (roles[m.role_membre] || m.role_membre)}
                </td>
                <td>{dateCourte(m.ajoute_le)}</td>
                <td className="num">{d.manage_members && <button type="button" className="pj-btn pj-btn--petit pj-btn--danger" onClick={() => retirer(m)}>Retirer</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="pj-note" style={{ marginTop: 10 }}>
        Les commits GitHub sont rattachés à une personne par son identifiant GitHub ; chacun peut renseigner le sien dans « Mon profil ».
      </p>

      {dialogue === 'ajout' && (
        <Dialogue titre="Ajouter un membre" onFermer={() => setDialogue(null)}>
          <AjoutMembre projet={projet} referentiel={referentiel} onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
      {dialogue === 'proposer' && (
        <Dialogue titre="Proposer un membre" onFermer={() => setDialogue(null)}>
          <FormulaireProposition projet={projet} referentiel={referentiel} type="ajouter_membre"
            onAnnuler={() => setDialogue(null)} onFait={() => { setDialogue(null); onChange() }} />
        </Dialogue>
      )}
    </section>
  )
}
