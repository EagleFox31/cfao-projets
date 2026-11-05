import { useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import Footer from '../components/portail/Footer'
import Nav from '../components/portail/Nav'
import PortalHeader from '../components/portail/PortalHeader'
import PortalReveal from '../components/portail/PortalReveal'
import PortalStaggerGrid from '../components/portail/PortalStaggerGrid'
import PvCard from '../components/portail/PvCard'
import ActiviteSemaine from '../components/projet/ActiviteSemaine'
import { Jauge, Statut, dico } from '../components/PageModule'
import useEnHautDePage from '../hooks/useEnHautDePage'
import usePortalBackground from '../hooks/usePortalBackground'
import useSiteEffects from '../hooks/useSiteEffects'
import { projets } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useReferentiel, useRequete } from '../lib/hooks'
import { codeSemaine } from '../lib/semaine'
import { scrollToPortalSection } from '../utils/portalScroll.js'

const VISUELS = {
  projets: '/assets/img_cards/clients-carte.jpg',
  propositions: '/assets/img_cards/certification.jpg',
  activite: '/assets/img_cards/techniciens-carte.jpg',
  equipe: '/assets/img_cards/test_theorie_senior.jpg',
}

const LIBELLES_ROLE = [
  ['superadmin', 'Administration'],
  ['build_team', 'Équipe technique'],
  ['team_manager', 'Responsable d’équipe'],
  ['trainer', 'Formateur'],
  ['ki', 'Instructeur'],
  ['learner', 'Apprenant'],
]

export function libelleRole(roles = []) {
  const trouve = LIBELLES_ROLE.find(([code]) => roles.includes(code))
  return trouve ? trouve[1] : 'Membre'
}

/** Tableau de bord : mes projets, ce qui attend ma décision, le travail de la semaine. */
export default function Accueil() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const referentiel = useReferentiel()
  useEnHautDePage('Projets')
  usePortalBackground(user)
  useSiteEffects()

  const semaine = codeSemaine()
  const liste = useRequete(() => projets.liste(), [])
  const props = useRequete(() => projets.propositions(), [])
  const activite = useRequete(() => projets.activiteSemaine(semaine), [semaine])

  const mesProjets = liste.donnees?.projets || []
  const enCours = useMemo(() => mesProjets.filter(p => p.statut === 'en_cours'), [mesProjets])
  const aDecider = props.donnees?.a_decider || []
  const total = activite.donnees?.total
  const statuts = dico(referentiel?.statuts_projet)

  const compte = (n, chargement) => (chargement ? '…' : String(n))

  return (
    <>
      <Nav />
      <main className="portal-page">
        <PortalHeader user={user} role={libelleRole(user.roles)} />

        <PortalReveal className="portal-section" id="priorites">
          <div className="container">
            <div className="portal-section-head">
              <p className="portal-section-eyebrow">Aujourd’hui</p>
              <h2 className="portal-section-title">Où en sont vos projets</h2>
            </div>
            <PortalStaggerGrid>
              <PvCard
                kicker="Projets"
                title={`${compte(mesProjets.length, liste.chargement)} projet${mesProjets.length > 1 ? 's' : ''}`}
                meta={`${enCours.length} en cours`}
                img={VISUELS.projets}
                cta="Voir les projets"
                onClick={() => navigate('/projets')}
              />
              <PvCard
                kicker="Propositions"
                title={`${compte(aDecider.length, props.chargement)} à décider`}
                meta={aDecider.length ? 'Des modifications attendent votre avis' : 'Rien en attente'}
                img={VISUELS.propositions}
                accentColor={aDecider.length ? 'var(--red)' : undefined}
                cta="Ouvrir"
                onClick={() => navigate('/propositions')}
              />
              <PvCard
                kicker={`Semaine ${semaine.slice(6)}`}
                title={`${compte(total?.commits ?? 0, activite.chargement)} commit${(total?.commits ?? 0) > 1 ? 's' : ''}`}
                meta={total ? `+${total.additions} / −${total.deletions} lignes` : 'Lecture GitHub'}
                img={VISUELS.activite}
                cta="Voir l’activité"
                onClick={() => scrollToPortalSection('activite')}
              />
              <PvCard
                kicker="Contributeurs"
                title={`${compte(activite.donnees?.personnes?.length ?? 0, activite.chargement)} cette semaine`}
                meta="Personnes ayant poussé du code"
                img={VISUELS.equipe}
                cta="Détail"
                onClick={() => scrollToPortalSection('activite')}
              />
            </PortalStaggerGrid>
          </div>
        </PortalReveal>

        <PortalReveal className="portal-section pj-accueil-section" id="projets">
          <div className="container">
            <div className="portal-section-head">
              <p className="portal-section-eyebrow">Avancement</p>
              <h2 className="portal-section-title">Projets en cours</h2>
            </div>
            {liste.erreur && <div className="pj-erreur">{liste.erreur.message}</div>}
            {!liste.chargement && enCours.length === 0 && (
              <div className="pj-vide">
                Aucun projet en cours. {referentiel?.peut_creer_projet ? <Link to="/projets">Créer le premier.</Link> : 'Vous serez ajouté par un chef de projet.'}
              </div>
            )}
            <div className="pj-grille">
              {enCours.map(p => (
                <Link key={p.id} to={`/projets/${p.id}`} className="pj-carte-projet">
                  <div className="pj-carte-avancement">
                    <strong>{p.nom}</strong>
                    <Statut code={p.statut} libelles={statuts} />
                  </div>
                  <Jauge valeur={p.avancement} />
                  <div className="pj-note">
                    {p.nb_membres} membre{p.nb_membres > 1 ? 's' : ''}
                    {' · '}{p.taches_par_statut?.fait ?? 0}/{Object.values(p.taches_par_statut || {}).reduce((a, b) => a + b, 0)} tâches faites
                    {p.propositions_en_attente ? ` · ${p.propositions_en_attente} proposition${p.propositions_en_attente > 1 ? 's' : ''} en attente` : ''}
                    {p.date_fin ? ` · échéance ${new Date(p.date_fin).toLocaleDateString('fr-FR')}` : ''}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </PortalReveal>

        <PortalReveal className="portal-section pj-accueil-section" id="activite">
          <div className="container">
            <div className="portal-section-head">
              <p className="portal-section-eyebrow">GitHub</p>
              <h2 className="portal-section-title">Le travail de la semaine, par personne</h2>
            </div>
            <div className="pj-panneau">
              <ActiviteSemaine semaineInitiale={semaine} />
            </div>
          </div>
        </PortalReveal>
      </main>
      <Footer />
    </>
  )
}
