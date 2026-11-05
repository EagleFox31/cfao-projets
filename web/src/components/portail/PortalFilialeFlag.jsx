import { resolveProfileFilialeLabel, resolveProfilePays } from '../../utils/profilOrg.js'

const FILIALE_FLAGS = {
  "Côte d'Ivoire": '/assets/flags/ivory-coast.svg',
  Maroc: '/assets/flags/morocco.svg',
  Sénégal: '/assets/flags/senegal.svg',
  Cameroun: '/assets/flags/cameroon.svg',
  Ghana: '/assets/flags/ghana.svg',
  Nigeria: '/assets/flags/nigeria.svg',
  Kenya: '/assets/flags/kenya.svg',
  Tanzanie: '/assets/flags/tanzania.svg',
  Angola: '/assets/flags/angola.svg',
  Madagascar: '/assets/flags/madagascar.svg',
  Mozambique: '/assets/flags/mozambique.svg',
  Zambie: '/assets/flags/zambia.svg',
}

/** Pastille drapeau pays + libellé filiale (ex. CFAO EQUIPMENT Cameroun). */
export default function PortalFilialeFlag({ user, className = '' }) {
  const pays = resolveProfilePays(user)
  const displayLabel = resolveProfileFilialeLabel(user)
  const src = pays ? FILIALE_FLAGS[pays] : null

  if (!displayLabel) return null

  const buPaysMatch = displayLabel.match(/^(CFAO\s+(?:MOTORS|EQUIPMENT|MOBILITY))\s+(.+)$/i)

  return (
    <span className={`portal-header-filiale-pill${className ? ` ${className}` : ''}`}>
      {src && (
        <span className="portal-header-filiale-pill-flag" aria-hidden="true">
          <img src={src} alt="" className="portal-header-flag" loading="eager" />
        </span>
      )}
      {buPaysMatch ? (
        <>
          <span className="portal-header-filiale-pill-bu">{buPaysMatch[1]}</span>
          <span className="portal-header-filiale-pill-pays">{buPaysMatch[2]}</span>
        </>
      ) : (
        <span className="portal-header-filiale-pill-pays portal-header-filiale-pill-pays--solo">
          {displayLabel}
        </span>
      )}
    </span>
  )
}
