import { useState } from 'react'
import PageModule, { Avatar } from '../components/PageModule'
import { projets } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAction, useRequete } from '../lib/hooks'

/** Ma fiche dans le module : surtout l'identifiant GitHub qui rattache mes commits. */
export default function Profil() {
  const { user } = useAuth()
  const { donnees, erreur, chargement, remplacer } = useRequete(() => projets.moi(), [])
  const [login, setLogin] = useState(null)
  const action = useAction()
  const valeur = login ?? donnees?.github_login ?? ''
  const [adresses, setAdresses] = useState(null)
  const valeurAdresses = adresses ?? (donnees?.adresses_git || []).join('\n')
  const [enregistre, setEnregistre] = useState(false)

  function envoyer(e) {
    e.preventDefault()
    setEnregistre(false)
    action.lancer(projets.modifierMoi({
      github_login: valeur.trim().replace(/^@/, '') || null,
      adresses_git: valeurAdresses.split(/[\s,;]+/).filter(Boolean),
    }), (r) => {
      remplacer(r)
      setLogin(null)
      setAdresses(null)
      setEnregistre(true)
    })
  }

  return (
    <PageModule titre="Mon profil" sousTitre="Votre identité vient de la plateforme ; seuls l’identifiant GitHub et vos adresses de commit se règlent ici.">
      <div className="pj-grille pj-grille--2">
        <section className="pj-panneau">
          <div className="pj-panneau-titre"><h2>Identité</h2></div>
          <div className="pj-personne">
            <Avatar nom={`${user.firstName || ''} ${user.lastName || ''}`} />
            <div>
              <strong>{user.firstName} {user.lastName}</strong>
              <div className="pj-note">{user.email}</div>
              <div className="pj-note">Rôles plateforme : {(user.roles || []).join(', ') || '—'}</div>
            </div>
          </div>
        </section>
        <section className="pj-panneau">
          <div className="pj-panneau-titre"><h2>GitHub</h2></div>
          {erreur && <div className="pj-erreur">{erreur.message}</div>}
          {chargement && !donnees && <div className="pj-chargement">Chargement…</div>}
          {donnees && (
            <form className="pj-formulaire" onSubmit={envoyer}>
              <label className="pj-champ pj-champ--large"><span>Identifiant GitHub</span>
                <input value={valeur} onChange={e => { setLogin(e.target.value); setEnregistre(false) }} placeholder="votre-login" />
              </label>
              <label className="pj-champ pj-champ--large"><span>Autres adresses de commit</span>
                <textarea rows={3} value={valeurAdresses} placeholder="une adresse par ligne, ex. poste du bureau"
                  onChange={e => { setAdresses(e.target.value); setEnregistre(false) }} />
              </label>
              <p className="pj-note pj-champ--large">
                Les commits dont l’auteur GitHub porte cet identifiant, votre adresse e-mail ou l’une de ces adresses vous sont attribués dans l’activité de la semaine.
              </p>
              {action.erreur && <div className="pj-erreur pj-champ--large">{action.erreur}</div>}
              {enregistre && <div className="pj-succes pj-champ--large">Enregistré.</div>}
              <div className="pj-formulaire-actions">
                <button type="submit" className="pj-btn pj-btn--primaire" disabled={action.enCours || (login === null && adresses === null)}>Enregistrer</button>
              </div>
            </form>
          )}
        </section>
      </div>
    </PageModule>
  )
}
