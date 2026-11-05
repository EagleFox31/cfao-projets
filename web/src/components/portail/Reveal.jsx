import { useEffect, useRef } from 'react'

export default function Reveal({
  as: Tag = 'div',
  stagger = false,
  className = '',
  style,
  children,
  rootMargin = '0px 0px 12% 0px',
  threshold = 0.01,
  ...rest
}) {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { el.classList.add('in'); io.unobserve(el) }
      })
    }, { rootMargin, threshold })
    io.observe(el)
    return () => io.disconnect()
  }, [rootMargin, threshold])
  return (
    <Tag ref={ref} className={`${stagger ? 'stagger' : 'reveal'} ${className}`.trim()} style={style} {...rest}>
      {children}
    </Tag>
  )
}
