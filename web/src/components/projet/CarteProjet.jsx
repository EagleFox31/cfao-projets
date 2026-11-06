import { useNavigate } from 'react-router-dom'
import { Jauge } from '../PageModule'
import PvCard from '../portail/PvCard'

export const VISUEL_PROJET = '/assets/img_cards/clients-carte.jpg'

/** Ligne de synthèse d'un projet : membres, tâches faites, propositions, échéance. */
export function noteProjet(p) {
  const total = Object.values(p.taches_par_statut || {}).reduce((a, b) => a + b, 0)
  const parts = [
    `${p.nb_membres} membre${p.nb_membres > 1 ? 's' : ''}`,
    `${p.taches_par_statut?.fait ?? 0}/${total} tâches faites`,
  ]
  if (p.propositions_en_attente) parts.push(`${p.propositions_en_attente} proposition${p.propositions_en_attente > 1 ? 's' : ''} en attente`)
  if (p.date_fin) parts.push(`échéance ${new Date(p.date_fin).toLocaleDateString('fr-FR')}`)
  return parts.join(' · ')
}

/** Carte d'un projet, même gabarit que les cartes du portail. */
export default function CarteProjet({ projet: p, statuts }) {
  const navigate = useNavigate()
  return (
    <PvCard
      className="pj-carte-projet"
      kicker={statuts?.[p.statut] || p.statut}
      title={p.nom}
      meta={noteProjet(p)}
      img={VISUEL_PROJET}
      cta="Ouvrir le projet"
      onClick={() => navigate(`/projets/${p.id}`)}
    >
      <div className="pj-carte-avancement"><Jauge valeur={p.avancement} /></div>
    </PvCard>
  )
}
