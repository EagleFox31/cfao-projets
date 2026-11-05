import { useState } from 'react'
import PortalGreetingBlock from './PortalGreetingBlock.jsx'

/* ─── Salutation ───────────────────────────────────────────────── */

const SPECIAL_DATE_KEYS = { '12-25': 'greeting_xmas', '01-01': 'greeting_newyear', '12-31': 'greeting_nye' }

const SALUTATIONS = {
  greeting_return: 'Bon retour',
  greeting_morning: 'Bonjour',
  greeting_afternoon: 'Bon après-midi',
  greeting_evening: 'Bonsoir',
  greeting_xmas: 'Joyeux Noël',
  greeting_newyear: 'Bonne année',
  greeting_nye: "Bonne fin d'année",
}

function computeGreetingKey() {
  const now = new Date()
  const hour = now.getHours()
  const mmdd = `${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

  const specialKey = SPECIAL_DATE_KEYS[mmdd]
  if (specialKey) return specialKey

  const isReturn = sessionStorage.getItem('cfao_portal_visited') === 'true'
  if (!isReturn) sessionStorage.setItem('cfao_portal_visited', 'true')
  if (isReturn) return 'greeting_return'

  if (hour >= 5  && hour < 12) return 'greeting_morning'
  if (hour >= 12 && hour < 18) return 'greeting_afternoon'
  return 'greeting_evening'
}

/* ─── Marques ──────────────────────────────────────────────────── */

const BRAND_LOGOS = {
  toyota:    '/assets/logos/toyota.png',
  mercedes:  '/assets/logos/mercedes.png',
  suzuki:    '/assets/logos/suzuki.png',
  mitsubishi:'/assets/logos/mitsubishi.png',
  byd:       '/assets/logos/byd.png',
  citroen:   '/assets/logos/citroen.png',
  yamaha:    '/assets/logos/yamaha.png',
  fuso:      '/assets/logos/fuso.png',
  hino:      '/assets/logos/hino.png',
  jcb:       '/assets/logos/jcb.png',
  lovol:     '/assets/logos/lovol.png',
  'renault-trucks': '/assets/logos/renault-trucks.png',
  'king-long': '/assets/logos/kinglong.png',
}

function BrandLogo({ brand }) {
  const src = BRAND_LOGOS[brand]
  if (src) {
    return (
      <span className="portal-header-brand-logo-wrap portal-header-brand-logo-wrap--geo" title={brand}>
        <img src={src} alt={brand} className="portal-header-brand-logo" />
      </span>
    )
  }
  return (
    <span className={`portal-brand-chip ${brand} portal-header-brand-chip`}>
      {brand}
    </span>
  )
}

function RoleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 11l-5 3-5-3" />
    </svg>
  )
}

/* ─── Entête portail formateur ─────────────────────────────────── */

export default function PortalHeader({ user, role = 'Membre' }) {
  const [greetingKey] = useState(() => computeGreetingKey())
  const userBrands = user.brands || []
  const showGeoBrands = userBrands.length > 0
  return (
    <section className="page-header portal-page-header">
      <div className="portal-hero-fx" aria-hidden="true">
        <span className="portal-hero-orb portal-hero-orb--a parallax" data-speed="0.08" />
        <span className="portal-hero-orb portal-hero-orb--b parallax" data-speed="0.16" />
      </div>
      <div className="container portal-header-container">
        <div className="portal-header-main">
          <p className="page-header-eyebrow portal-header-eyebrow">
            <span className="portal-header-role-badge">
              <RoleIcon />
              {role}
            </span>
          </p>
          <PortalGreetingBlock
            greetingKey={SALUTATIONS[greetingKey]}
            firstName={user.firstName}
            user={user}
          />
          {showGeoBrands && (
            <div className="portal-header-geo-row">
              <div className="portal-header-geo-brands">
                {userBrands.map(brand => (
                  <BrandLogo key={brand} brand={brand} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
