import Reveal from './Reveal.jsx'

/** Section portail — entrée au scroll (fade + translateY). */
export default function PortalReveal({ className = '', ...rest }) {
  return (
    <Reveal
      as="section"
      className={`portal-reveal ${className}`.trim()}
      rootMargin="0px 0px -5% 0px"
      threshold={0.12}
      {...rest}
    />
  )
}
