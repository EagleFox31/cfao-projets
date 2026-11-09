import PageModule from '../components/PageModule'
import { CarteProposition } from '../components/projet/Propositions'
import { projets } from '../lib/api'
import { useReferentiel, useRequete } from '../lib/hooks'

/** Les propositions à décider, puis les miennes. */
export default function Propositions() {
  const referentiel = useReferentiel()
  const { donnees, erreur, chargement, recharger } = useRequete(() => projets.propositions(), [])

  const aDecider = donnees?.a_decider || []
  const miennes = donnees?.miennes || []

  return (
    <PageModule
      titre="Propositions"
      sousTitre="Les modifications proposées par d’autres profils : vous tranchez celles de vos projets, et suivez les vôtres."
    >
      {erreur && <div className="pj-erreur">{erreur.message}</div>}
      {chargement && !donnees && <div className="pj-chargement">Chargement…</div>}

      <section className="pj-panneau">
        <div className="pj-panneau-titre"><h2>À décider <span className="pj-onglet-nb">{aDecider.length}</span></h2></div>
        {aDecider.length === 0
          ? <div className="pj-vide">Rien n’attend votre décision.</div>
          : aDecider.map(p => (
            <CarteProposition key={p.id} proposition={p} referentiel={referentiel} peutDecider avecProjet
              onDecision={() => recharger(true)} />
          ))}
      </section>

      <section className="pj-panneau">
        <div className="pj-panneau-titre"><h2>Mes propositions <span className="pj-onglet-nb">{miennes.length}</span></h2></div>
        {miennes.length === 0
          ? <div className="pj-vide">Vous n’avez encore rien proposé. Depuis un projet, le bouton « Proposer » soumet une modification à son pilote.</div>
          : miennes.map(p => <CarteProposition key={p.id} proposition={p} referentiel={referentiel} avecProjet />)}
      </section>
    </PageModule>
  )
}
