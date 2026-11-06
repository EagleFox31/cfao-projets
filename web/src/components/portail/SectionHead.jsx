/**
 * En-tête de section du portail : une icône, un sur-titre et un titre, décrits
 * par une entrée de configuration ({ icone, eyebrow, titre }) plutôt qu'écrits
 * en dur dans chaque page.
 */
const ICONES = {
  avancement: (
    <>
      <path d="M3 3v18h18" />
      <path d="M7 15l4-4 4 3 5-6" />
    </>
  ),
  github: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  propositions: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M9 15l2 2 4-4" />
    </>
  ),
  equipe: (
    <>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </>
  ),
}

export function IconeSection({ nom }) {
  const trace = ICONES[nom]
  if (!trace) return null
  return (
    <svg className="portal-section-icon" width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {trace}
    </svg>
  )
}

export default function SectionHead({ section }) {
  const { icone, eyebrow, titre } = section
  return (
    <div className="portal-section-head">
      <p className="portal-section-eyebrow"><IconeSection nom={icone} />{eyebrow}</p>
      <h2 className="portal-section-title">{titre}</h2>
    </div>
  )
}
