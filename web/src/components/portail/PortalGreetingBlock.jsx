import { Fragment } from 'react'
import PortalFilialeFlag from './PortalFilialeFlag.jsx'
import { resolveProfileFilialeLabel } from '../../utils/profilOrg.js'

/** Phrase d'orientation du portail formateur. */
const ORIENTATION =
  'Vos projets, leur avancement et le travail de la semaine, au même endroit.'

function splitWords(text) {
  return String(text ?? '').trim().split(/\s+/).filter(Boolean)
}

/** Salutation + phrase d'orientation du portail. */
export default function PortalGreetingBlock({ greetingKey, firstName, user }) {
  const filialeLabel = user ? resolveProfileFilialeLabel(user) : null

  const greetingWords = splitWords(greetingKey)
  // Index de cascade partagé entre titre et sous-titre (apparition continue).
  let wi = 0
  const showPill = Boolean(filialeLabel && user)

  return (
    <div className="portal-header-greeting-block">
      <h1 className="page-header-title portal-header-greeting portal-greeting-cascade">
        {greetingWords.map((w, idx) => {
          const isLast = idx === greetingWords.length - 1
          const node = (
            <Fragment key={`g-${idx}`}>
              <span className="portal-word" style={{ '--wi': wi }}>
                {isLast ? `${w},` : w}
              </span>{' '}
            </Fragment>
          )
          wi += 1
          return node
        })}
        <span className="portal-word portal-header-firstname" style={{ '--wi': wi++ }}>
          {firstName}
        </span>{' '}
        <span className="portal-word" style={{ '--wi': wi++ }}>!</span>
        {showPill && (
          <span
            className="portal-header-greeting-org portal-word"
            style={{ '--wi': wi++ }}
          >
            <PortalFilialeFlag user={user} />
          </span>
        )}
      </h1>
      <p className="portal-header-orient portal-greeting-cascade">
        {splitWords(ORIENTATION).map((w, idx) => (
          <Fragment key={`o-${idx}`}>
            <span className="portal-word" style={{ '--wi': wi + idx }}>{w}</span>{' '}
          </Fragment>
        ))}
      </p>
    </div>
  )
}
