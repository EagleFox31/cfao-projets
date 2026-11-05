import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth'

const PORTAIL_URL = import.meta.env.VITE_PORTAIL_URL || ''

/** Rôles qui voient le journal des erreurs du module. */
const ROLES_TECHNIQUES = ['superadmin', 'build_team']

export function liensPour(user) {
  const liens = [
    { to: '/', libelle: 'Accueil', fin: true },
    { to: '/projets', libelle: 'Projets' },
    { to: '/propositions', libelle: 'Propositions' },
  ]
  if ((user?.roles || []).some(r => ROLES_TECHNIQUES.includes(r))) {
    liens.push({ to: '/journal-erreurs', libelle: 'Journal' })
  }
  return liens
}

function UserMenu({ user, onLogout }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const initials = `${user.firstName?.[0] ?? ''}${user.lastName?.[0] ?? ''}`.toUpperCase() || '·'

  useEffect(() => {
    if (!open) return undefined
    const onClick = (e) => { if (!ref.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  return (
    <div className="nav-user-menu" ref={ref}>
      <button type="button" className="nav-user-btn" aria-expanded={open} onClick={() => setOpen(o => !o)}>
        <span className="nav-user-avatar">{initials}</span>
        <span className="nav-user-name">{user.firstName}</span>
      </button>
      {open && (
        <div className="nav-user-dropdown" role="menu">
          <div className="nav-user-dropdown-head">
            <span className="nav-user-dropdown-name">{user.firstName} {user.lastName}</span>
            <span className="nav-user-dropdown-filiale">{user.filiale || 'CFAO Academy'}</span>
          </div>
          <Link to="/profil" className="nav-user-dropdown-item" role="menuitem" onClick={() => setOpen(false)}>
            Mon profil
          </Link>
          <button type="button" className="nav-user-dropdown-item" role="menuitem" onClick={onLogout}>
            Se déconnecter
          </button>
        </div>
      )}
    </div>
  )
}

function NavLinkList({ variant, liens, onItemActivate }) {
  const listClass = variant === 'mobile' ? 'nav-mobile-links' : 'nav-links'
  return (
    <ul className={listClass}>
      {liens.map(l => (
        <li key={l.to}>
          <NavLink
            to={l.to}
            end={l.fin}
            className={({ isActive }) => (variant === 'mobile'
              ? `nav-mobile-link${isActive ? ' active' : ''}`
              : (isActive ? 'active' : ''))}
            onClick={onItemActivate}
          >
            {l.libelle}
          </NavLink>
        </li>
      ))}
    </ul>
  )
}

/**
 * La barre du haut, au rendu de celle du portail.
 *
 * Connecté : liens du module (accueil, projets, propositions, journal pour
 * l'équipe technique) et menu du compte. Sur la connexion : mode « non
 * connecté », sans lien vers d'autres pages.
 */
export default function Nav() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const onLogin = pathname === '/connexion'
  const onPortal = Boolean(user) && !onLogin
  const liens = onPortal ? liensPour(user) : []

  const [menuOpen, setMenuOpen] = useState(false)
  const toggleRef = useRef(null)
  const panelRef = useRef(null)
  const menuInstanceId = useId()
  const mobileMenuId = `nav-mobile-menu${menuInstanceId}`

  const closeMenu = useCallback(() => setMenuOpen(false), [])

  function handleLogout() {
    logout()
    navigate('/connexion', { replace: true })
    closeMenu()
  }

  useEffect(() => { closeMenu() }, [pathname, closeMenu])

  useEffect(() => {
    if (!menuOpen) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        closeMenu()
        toggleRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const focusTimer = window.setTimeout(() => {
      panelRef.current?.querySelector('a, button')?.focus()
    }, 0)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      window.clearTimeout(focusTimer)
    }
  }, [menuOpen, closeMenu])

  return (
    <nav
      className={`nav${onLogin ? ' nav--login' : ''}${onPortal ? ' nav--portal' : ''}${menuOpen ? ' nav--menu-open' : ''}`}
      aria-label="Navigation principale"
    >
      <div className="nav-shell">
        <Link to="/" className="brand nav-brand" style={{ textDecoration: 'none' }}>
          <img src="/assets/logo-cfao-mobility.jpg" alt="cfao mobility" className="brand-mark" />
          <div className="brand-label">Academy<span>.</span><em className="pj-brand-module">Projets</em></div>
        </Link>

        <button
          ref={toggleRef}
          type="button"
          className="nav-toggle"
          aria-expanded={menuOpen}
          aria-controls={mobileMenuId}
          aria-label="Menu"
          onClick={() => setMenuOpen(o => !o)}
        >
          <span className="nav-toggle-bars" aria-hidden="true"><span /><span /><span /></span>
        </button>

        <NavLinkList variant="desktop" liens={liens} />

        <div className="nav-actions">
          {onPortal && PORTAIL_URL && (
            <a href={PORTAIL_URL} className="nav-cta nav-cta--ghost nav-home-btn">← Retour au site</a>
          )}
          {onPortal ? (
            <UserMenu user={user} onLogout={handleLogout} />
          ) : (
            <Link
              to="/connexion"
              className={`nav-cta${onLogin ? ' nav-cta--primary' : ' nav-cta--ghost'}`}
              aria-current={onLogin ? 'page' : undefined}
            >
              Se connecter
            </Link>
          )}
        </div>
      </div>

      <div id={mobileMenuId} ref={panelRef} className="nav-mobile-panel" hidden={!menuOpen}>
        <button type="button" className="nav-mobile-backdrop" aria-label="Fermer le menu" onClick={closeMenu} />
        <div className="nav-mobile-drawer">
          <NavLinkList variant="mobile" liens={liens} onItemActivate={closeMenu} />
          <div className="nav-mobile-foot">
            {onPortal && PORTAIL_URL && (
              <a href={PORTAIL_URL} className="nav-mobile-foot-link">← Retour au site</a>
            )}
            {onPortal ? (
              <button type="button" className="nav-mobile-foot-link pj-bouton-nu" onClick={handleLogout}>Se déconnecter</button>
            ) : (
              <Link to="/connexion" className="nav-mobile-foot-link" onClick={closeMenu}>Se connecter</Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
