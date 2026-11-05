import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import Nav from '../components/portail/Nav'
import FormAlert, { FormFieldError } from '../components/portail/FormAlert'
import LoginParticles from '../components/portail/LoginParticles'
import PortalLoader from '../components/portail/PortalLoader'
import useAuthForm from '../hooks/useAuthForm'
import useEnHautDePage from '../hooks/useEnHautDePage'
import useSiteEffects from '../hooks/useSiteEffects'
import { useAuth } from '../lib/auth'

const LOGIN_BG = '/assets/hero/default.jpg'

function EyeIcon({ open }) {
  if (open) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
        <path d="M1 1l22 22" />
        <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      </svg>
    )
  }
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function MicrosoftIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="1" y="1" width="10" height="10" fill="#f25022" />
      <rect x="13" y="1" width="10" height="10" fill="#7fba00" />
      <rect x="1" y="13" width="10" height="10" fill="#00a4ef" />
      <rect x="13" y="13" width="10" height="10" fill="#ffb900" />
    </svg>
  )
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#EA4335" d="M12 11.2v2.4h4.2c-.2 1-1.4 2.9-4.2 2.9-2.5 0-4.6-2.1-4.6-4.7s2.1-4.7 4.6-4.7c1.4 0 2.4.6 3 1.1l2-1.9C16.5 5.4 14.4 4.5 12 4.5 7.9 4.5 4.5 7.9 4.5 12s3.4 7.5 7.5 7.5c4.3 0 7.2-3 7.2-7.3 0-.5 0-.9-.1-1.2H12z" />
    </svg>
  )
}

const SSO_PROVIDERS = [
  { id: 'microsoft', icon: MicrosoftIcon, label: 'Continuer avec Microsoft' },
  { id: 'google', icon: GoogleIcon, label: 'Continuer avec Google' },
]

/**
 * Écran de chargement après la connexion, comme à l'entrée du portail :
 * 'loading' → 'leaving' (fondu) → 'done' (l'accueil prend la suite).
 */
function useEntreeDansLePortail(actif) {
  const [phase, setPhase] = useState('loading')

  useEffect(() => {
    if (!actif) return undefined
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const hold = reduce ? 150 : 850
    const t1 = setTimeout(() => setPhase('leaving'), hold)
    const t2 = setTimeout(() => setPhase('done'), hold + 450)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [actif])

  return phase
}

export default function Connexion() {
  useEnHautDePage('Connexion')
  useSiteEffects()
  const { user, connexion } = useAuth()
  const navigate = useNavigate()
  const lieu = useLocation()
  const retour = lieu.state?.retour || '/'

  // Vrai dès qu'une connexion vient d'aboutir : le chargement s'affiche
  // avant l'accueil. Un compte déjà ouvert à l'arrivée y va directement.
  const dejaConnecte = useRef(Boolean(user))
  const [entree, setEntree] = useState(false)
  const phase = useEntreeDansLePortail(entree)

  const auth = useAuthForm(async (identifiant, motDePasse, seSouvenir) => {
    const refus = await connexion(identifiant, motDePasse, seSouvenir)
    if (!refus) setEntree(true)
    return refus
  })

  const formErrorMessage = auth.formError ? auth.getMessage(auth.formError) : null
  const formSuccessMessage = auth.formSuccess ? auth.getMessage(auth.formSuccess) : null

  if (dejaConnecte.current && user) return <Navigate to={retour} replace />
  if (entree && phase === 'done') return <Navigate to={retour} replace />
  if (entree) return <PortalLoader leaving={phase === 'leaving'} />

  return (
    <div className="login-page">
      <div className="login-bg" aria-hidden="true">
        <div
          className="login-bg-photo"
          style={{ backgroundImage: `url(${LOGIN_BG})` }}
        />
        <div className="login-bg-vignette" />
        <LoginParticles />
      </div>

      <Nav />

      <main className="login-main">
        <div className="login-layout">
          <div className="login-card-wrap">
            <div className="login-card login-card--glass">
              <div className="login-card-brand">
                <img
                  src="/assets/logo-cfao-mobility.jpg"
                  alt="CFAO Academy"
                  className="login-card-logo"
                />
              </div>

              <div className="login-form-slider">
                <div className={`login-form-track${auth.panel === 'forgot' ? ' is-forgot' : ''}`}>
                  <div className="login-form-panel">
                    <div className="login-form-inner">
                      <p className="login-card-lead">
                        Veuillez saisir votre identifiant et votre mot de passe pour vous connecter
                      </p>

                      <div className="login-sso" aria-label="Connexion SSO">
                        {SSO_PROVIDERS.map((provider) => {
                          const Icon = provider.icon
                          return (
                            <button
                              key={provider.id}
                              type="button"
                              className="login-sso-btn"
                              disabled
                              title="Connexion SSO — bientôt disponible"
                              aria-disabled="true"
                            >
                              <Icon />
                              <span className="login-sso-label">{provider.label}</span>
                              <span className="login-sso-badge">Bientôt</span>
                            </button>
                          )
                        })}
                      </div>

                      <div className="login-divider">
                        <span>ou</span>
                      </div>

                      <FormAlert type="error" message={auth.panel === 'login' ? formErrorMessage : null} />

                      <form className="login-form" onSubmit={auth.submitLogin} noValidate>
                        <div className="login-field">
                          <label className="login-label sr-only" htmlFor="login-identifier">Nom d'utilisateur ou e-mail</label>
                          <input
                            id="login-identifier"
                            type="text"
                            className={`login-input${auth.fieldErrors.email ? ' is-invalid' : ''}`}
                            placeholder="Entrez votre nom d'utilisateur"
                            autoComplete="username"
                            value={auth.login.email}
                            onChange={(e) => auth.updateLogin('email', e.target.value)}
                            aria-invalid={Boolean(auth.fieldErrors.email)}
                            aria-describedby={auth.fieldErrors.email ? 'login-identifier-error' : undefined}
                            disabled={auth.loading}
                          />
                          <FormFieldError
                            id="login-identifier-error"
                            error={auth.panel === 'login' && auth.fieldErrors.email ? auth.getMessage(auth.fieldErrors.email) : null}
                          />
                        </div>

                        <div className="login-field">
                          <label className="login-label sr-only" htmlFor="login-password">Mot de passe</label>
                          <div className="login-input-wrap">
                            <input
                              id="login-password"
                              type={auth.showPassword ? 'text' : 'password'}
                              className={`login-input${auth.fieldErrors.password ? ' is-invalid' : ''}`}
                              placeholder="Entrez votre mot de passe"
                              autoComplete="current-password"
                              value={auth.login.password}
                              onChange={(e) => auth.updateLogin('password', e.target.value)}
                              aria-invalid={Boolean(auth.fieldErrors.password)}
                              aria-describedby={auth.fieldErrors.password ? 'login-password-error' : undefined}
                              disabled={auth.loading}
                            />
                            <button
                              type="button"
                              className="login-input-toggle"
                              onClick={() => auth.setShowPassword((v) => !v)}
                              aria-label={auth.showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                              aria-pressed={auth.showPassword}
                              disabled={auth.loading}
                            >
                              <EyeIcon open={auth.showPassword} />
                            </button>
                          </div>
                          <FormFieldError
                            id="login-password-error"
                            error={auth.panel === 'login' && auth.fieldErrors.password ? auth.getMessage(auth.fieldErrors.password) : null}
                          />
                        </div>

                        <div className="login-options">
                          <label className="login-remember">
                            <input
                              type="checkbox"
                              className="login-checkbox"
                              checked={auth.login.remember}
                              onChange={(e) => auth.updateLogin('remember', e.target.checked)}
                              disabled={auth.loading}
                            />
                            <span>Se souvenir de moi</span>
                          </label>
                          <div className="login-forgot-wrap">
                            <button type="button" className="login-forgot" onClick={auth.openForgot}>
                              Mot de passe oublié ?
                            </button>
                          </div>
                        </div>

                        <button type="submit" className="btn btn-primary login-submit" disabled={auth.loading}>
                          {auth.loading ? 'Connexion…' : 'Accédez à votre espace'}
                        </button>
                      </form>
                    </div>
                  </div>

                  <div className="login-form-panel">
                    <div className="login-form-inner">
                      <div className="login-form-head">
                        <div>
                          <p className="mono login-form-eyebrow">Réinitialisation</p>
                          <h2 className="login-form-title">Mot de passe oublié</h2>
                        </div>
                      </div>
                      <p className="login-form-sub">
                        Saisissez l’adresse e-mail de votre compte Academy. Nous vous enverrons un lien de réinitialisation.
                      </p>

                      <FormAlert type="error" message={auth.panel === 'forgot' ? formErrorMessage : null} />
                      <FormAlert type="success" message={auth.panel === 'forgot' ? formSuccessMessage : null} />

                      <form className="login-form" onSubmit={auth.submitForgot} noValidate>
                        <div className="login-field">
                          <label className="login-label" htmlFor="forgot-email">Adresse e-mail</label>
                          <input
                            id="forgot-email"
                            type="email"
                            className={`login-input${auth.fieldErrors.email ? ' is-invalid' : ''}`}
                            placeholder="nom@exemple.com"
                            autoComplete="email"
                            value={auth.forgot.email}
                            onChange={(e) => auth.updateForgot(e.target.value)}
                            aria-invalid={Boolean(auth.fieldErrors.email)}
                            aria-describedby={auth.fieldErrors.email ? 'forgot-email-error' : undefined}
                            disabled={auth.loading || Boolean(auth.formSuccess)}
                          />
                          <FormFieldError
                            id="forgot-email-error"
                            error={auth.panel === 'forgot' && auth.fieldErrors.email ? auth.getMessage(auth.fieldErrors.email) : null}
                          />
                        </div>

                        <button
                          type="submit"
                          className="btn btn-primary login-submit"
                          disabled={auth.loading || Boolean(auth.formSuccess)}
                        >
                          {auth.loading ? 'Envoi…' : 'Envoyer le lien'}
                          {!auth.loading && <span className="arrow">→</span>}
                        </button>
                      </form>

                      <p className="login-back">
                        <button type="button" className="login-back-link login-back-btn" onClick={auth.closeForgot}>
                          ← Retour à la connexion
                        </button>
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
