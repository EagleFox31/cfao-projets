import Reveal from './Reveal.jsx'

/** Grille portail — apparition décalée des cartes au scroll. */
export default function PortalStaggerGrid({ className = 'cols-4 pv-grid--stretch', children, ...rest }) {
  return (
    <Reveal
      stagger
      className={`portal-stagger-grid pv-grid ${className}`.trim()}
      rootMargin="0px 0px -6% 0px"
      threshold={0.06}
      {...rest}
    >
      {children}
    </Reveal>
  )
}
