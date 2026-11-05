import { Link } from 'react-router-dom'

// Le module n'a pas les pages du site : les entrées du pied de page restent
// affichées (même rendu que le portail) mais en simple texte.
const NAV_COLS = [
  {
    title: 'Explorer',
    links: ['À propos', 'Formations', 'Publics', 'Actualités'],
  },
  {
    title: 'Accès',
    links: ['Nous contacter', 'Connexion'],
  },
]

const STATS = [
  { value: '35+', label: 'pays' },
  { value: '17', label: 'marques' },
  { value: '120+', label: 'formations' },
]

const EMAIL = 'academy@cfaomobility.com'

export default function Footer() {
  return (
    <footer className="footer">
      {/* Accent top */}
      <div className="footer-accent" aria-hidden="true" />

      <div className="container">

        {/* ── Grille principale ── */}
        <div className="footer-grid">

          {/* Colonne brand */}
          <div className="footer-brand-col">
            <Link to="/" className="footer-brand-link">
              <img src="/assets/logo-cfao-mobility.jpg" alt="CFAO Mobility" className="footer-logo" />
              <span className="footer-brand-name">academy<span className="footer-brand-dot">.</span></span>
            </Link>

            <p className="footer-tagline">
              Formation technique constructeur — présents dans 35 pays africains.
            </p>

            <div className="footer-stats">
              {STATS.map(({ value, label }) => (
                <div key={label} className="footer-stat">
                  <span className="footer-stat-num">{value}</span>
                  <span className="footer-stat-lbl">{label}</span>
                </div>
              ))}
            </div>

            <a href={`mailto:${EMAIL}`} className="footer-email">
              {EMAIL}
            </a>
          </div>

          {/* Colonnes de navigation */}
          {NAV_COLS.map((col) => (
            <div key={col.title} className="footer-col">
              <h6 className="footer-col-title">{col.title}</h6>
              <ul className="footer-col-list">
                {col.links.map((libelle) => (
                  <li key={libelle}>
                    <span className="footer-col-link">{libelle}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}

        </div>

        {/* ── Barre du bas ── */}
        <div className="footer-bottom">
          <span className="footer-copyright">
            © 2026 CFAO Mobility — CFAO Academy
          </span>

          <div className="footer-legal">
            <span className="footer-legal-link">Mentions légales</span>
            <span className="footer-legal-sep" aria-hidden="true" />
            <span className="footer-legal-link">Confidentialité</span>
          </div>

          <span className="footer-location">Douala, Cameroun</span>
        </div>

      </div>

      {/* Watermark décoratif */}
      <div className="footer-watermark" aria-hidden="true">ACADEMY</div>
    </footer>
  )
}
