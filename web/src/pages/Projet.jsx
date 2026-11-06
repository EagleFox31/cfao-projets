import { useMemo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import FicheDetail from '../components/FicheDetail'
import PageModule, { Jauge, Statut, dico } from '../components/PageModule'
import ActiviteSemaine from '../components/projet/ActiviteSemaine'
import Equipe from '../components/projet/Equipe'
import Parametres from '../components/projet/Parametres'
import { CarteProposition } from '../components/projet/Propositions'
import Taches from '../components/projet/Taches'
import { projets } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useReferentiel, useRequete } from '../lib/hooks'

const ONGLETS = [
  ['taches', 'Avancement et tâches'],
  ['equipe', 'Équipe'],
  ['activite', 'Activité GitHub'],
  ['propositions', 'Propositions'],
  ['parametres', 'Paramètres'],
]

function PropositionsDuProjet({ projet, referentiel, onChange }) {
  const { donnees, erreur, chargement, recharger } = useRequete(() => projets.propositionsDuProjet(projet.id), [projet.id])
  const liste = donnees?.propositions || []
  return (
    <section className="pj-panneau">
      <div className="pj-panneau-titre"><h2>Propositions reçues <span className="pj-onglet-nb">{liste.length}</span></h2></div>
      {erreur && <div className="pj-erreur">{erreur.message}</div>}
      {chargement && !donnees && <div className="pj-chargement">Chargement…</div>}
      {donnees && liste.length === 0 && <div className="pj-vide">Aucune proposition pour ce projet.</div>}
      {liste.map(p => (
        <CarteProposition key={p.id} proposition={p} referentiel={referentiel} peutDecider={projet.droits.decider}
          onDecision={() => { recharger(true); onChange() }} />
      ))}
    </section>
  )
}

/** Fiche d'un projet, en onglets. L'onglet vit dans l'URL (`?onglet=`). */
export default function Projet() {
  const { id } = useParams()
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const referentiel = useReferentiel()
  const onglet = ONGLETS.some(([c]) => c === params.get('onglet')) ? params.get('onglet') : 'taches'
  const { donnees, erreur, chargement, recharger } = useRequete(() => projets.detail(id), [id])

  const projet = useMemo(() => {
    if (!donnees) return null
    return { ...donnees, moi_id: user?.personne?.id ?? null }
  }, [donnees, user])
  const statuts = dico(referentiel?.statuts_projet)
  const roles = dico(referentiel?.roles_membre)
  const rafraichir = () => recharger(true)

  if (erreur && !projet) {
    return <PageModule titre="Projet" fil={[{ to: '/projets', libelle: 'Projets' }]}><div className="pj-erreur">{erreur.message}</div></PageModule>
  }
  if (!projet) {
    return <PageModule titre="Projet" fil={[{ to: '/projets', libelle: 'Projets' }]}><div className="pj-chargement">Chargement…</div></PageModule>
  }

  const nbProps = projet.propositions_en_attente || 0

  const meta = [
    `${projet.nb_membres} membre${projet.nb_membres > 1 ? 's' : ''}`,
    projet.mon_role ? `vous : ${roles[projet.mon_role] || projet.mon_role}` : null,
    <Jauge key="jauge" valeur={projet.avancement} />,
  ].filter(Boolean)

  return (
    <FicheDetail
      titre={projet.nom}
      etiquette={<Statut code={projet.statut} libelles={statuts} />}
      meta={meta}
      chapeau={projet.description}
      repli="/projets"
      fermerLibelle="Fermer le projet"
    >
      {chargement && <div className="pj-note" aria-live="polite">Actualisation…</div>}
      {erreur && <div className="pj-erreur">{erreur.message}</div>}
      <div className="pj-onglets" role="tablist">
        {ONGLETS.map(([code, libelle]) => (
          <button key={code} type="button" role="tab" aria-selected={onglet === code}
            className={`pj-onglet${onglet === code ? ' is-active' : ''}`}
            onClick={() => setParams(code === 'taches' ? {} : { onglet: code })}>
            {libelle}
            {code === 'propositions' && nbProps > 0 && <span className="pj-onglet-nb">{nbProps}</span>}
          </button>
        ))}
      </div>

      {onglet === 'taches' && <Taches projet={projet} referentiel={referentiel} onChange={rafraichir} />}
      {onglet === 'equipe' && <Equipe projet={projet} referentiel={referentiel} onChange={rafraichir} />}
      {onglet === 'activite' && (
        <section className="pj-panneau">
          <ActiviteSemaine projetId={projet.id} />
        </section>
      )}
      {onglet === 'propositions' && <PropositionsDuProjet projet={projet} referentiel={referentiel} onChange={rafraichir} />}
      {onglet === 'parametres' && <Parametres projet={projet} referentiel={referentiel} onChange={rafraichir} />}
    </FicheDetail>
  )
}
