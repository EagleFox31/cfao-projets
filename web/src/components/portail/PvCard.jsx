import { useEffect, useState } from 'react'

const DEFAULT_IMG = '/assets/logo-cfao-mobility.jpg'

export default function PvCard({
  kicker, title, meta, variant, corner,
  img, imgFallback, imgPosition, cardMedia, logo, brandLabel, brandAside,
  cta,
  accentColor,
  hoverHint,
  onClick,
  selected,
  className = '',
  children,
}) {
  const isInteractive = Boolean(onClick)
  const resolvedHoverHint = hoverHint === false || !hoverHint ? null : hoverHint
  const primaryImg = img || DEFAULT_IMG
  const [resolvedImg, setResolvedImg] = useState(primaryImg)

  useEffect(() => {
    setResolvedImg(primaryImg)
  }, [primaryImg])

  function handleImgError() {
    if (imgFallback && resolvedImg !== imgFallback) {
      setResolvedImg(imgFallback)
      return
    }
    if (resolvedImg !== DEFAULT_IMG) setResolvedImg(DEFAULT_IMG)
  }

  const Tag = isInteractive ? 'button' : 'div'
  const cls = [
    'pv-card',
    variant ? `pv-card--${variant}` : '',
    selected ? 'is-selected' : '',
    className,
  ].filter(Boolean).join(' ')
  const outerProps = isInteractive ? { type: 'button', onClick } : {}
  const outerStyle = accentColor ? { '--pv-accent': accentColor } : undefined

  return (
    <Tag className={cls} style={outerStyle} {...outerProps}>
      <div className="pv-card-media">
        {cardMedia ?? (
          <div className="pv-card-img">
            <img
              src={resolvedImg}
              alt=""
              loading="lazy"
              onError={handleImgError}
              style={imgPosition ? { objectPosition: imgPosition } : undefined}
            />
          </div>
        )}
        {resolvedHoverHint && (
          <span className="pv-card-hover-hint" role="tooltip">
            {resolvedHoverHint}
          </span>
        )}
      </div>
      <div className="pv-card-body">
        {(logo || brandLabel || brandAside) && (
          <div className="pv-card-brand-row">
            {logo && <img src={logo} alt="" className="pv-card-brand-logo" loading="lazy" />}
            {!logo && brandLabel && (
              <span className="pv-card-brand-label">{brandLabel}</span>
            )}
            {brandAside}
          </div>
        )}
        {kicker && <div className="kicker">{kicker}</div>}
        <h3>{title}</h3>
        {meta && <div className="meta">{meta}</div>}
        {children}

        {cta && (
          <div className="pv-card-cta">
            <span className="pv-cta-link">{cta} <span className="arrow">→</span></span>
          </div>
        )}

        {corner && <span className="corner">↗</span>}
      </div>
    </Tag>
  )
}
