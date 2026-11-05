import { useEffect } from 'react'
import { echelle } from '../utils/echelle'

export default function useSiteEffects() {
  useEffect(() => {
    // hero h1 reveal
    const raf = requestAnimationFrame(() => {
      document.querySelector('.hero-h1')?.classList.add('shown')
    })

    // reveal on scroll
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target) }
      })
    }, { rootMargin: '0px 0px 12% 0px', threshold: 0.01 })
    document.querySelectorAll('.reveal, .stagger').forEach(el => io.observe(el))

    // parallax scroll-linked
    const parallaxEls = [...document.querySelectorAll('.parallax')]
    const parallaxXEls = [...document.querySelectorAll('.parallax-x')]
    let ticking = false
    function onScroll() {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        const vh = window.innerHeight
        parallaxEls.forEach(el => {
          const speed = parseFloat(el.dataset.speed || '0.1')
          const rect = el.getBoundingClientRect()
          const center = rect.top + rect.height / 2
          const offset = (center - vh / 2) * speed
          el.style.transform = `translate3d(0, ${(-offset).toFixed(2)}px, 0)`
        })
        parallaxXEls.forEach(el => {
          const speed = parseFloat(el.dataset.speed || '0.3')
          const rect = el.getBoundingClientRect()
          const center = rect.top + rect.height / 2
          const offset = (center - vh / 2) * speed
          el.style.transform = `translate3d(${offset.toFixed(2)}px, 0, 0)`
        })
        ticking = false
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()

    // scroll progress bar
    const progressBar = document.createElement('div')
    progressBar.className = 'scroll-progress'
    document.body.appendChild(progressBar)
    function updateProgress() {
      const max = document.documentElement.scrollHeight - window.innerHeight
      const pct = max > 0 ? Math.max(0, Math.min(100, (window.scrollY / max) * 100)) : 0
      progressBar.style.width = pct + '%'
    }
    window.addEventListener('scroll', updateProgress, { passive: true })
    updateProgress()

    // cursor glow
    const glow = document.getElementById('cursor-glow')
    let glowRaf
    if (glow && matchMedia('(pointer:fine)').matches) {
      let x = 0, y = 0, tx = 0, ty = 0
      const onMove = e => {
        const z = echelle()
        tx = e.clientX / z; ty = e.clientY / z; glow.style.opacity = '1'
      }
      window.addEventListener('mousemove', onMove)
      const loop = () => {
        x += (tx - x) * 0.12; y += (ty - y) * 0.12
        glow.style.left = x + 'px'; glow.style.top = y + 'px'
        glowRaf = requestAnimationFrame(loop)
      }
      loop()
    }

    // magnetic buttons
    const magnets = [...document.querySelectorAll(
      '.btn-primary, .nav-cta, .nav-links a, .brand-mark, .brand-label',
    )]
    const magnetHandlers = magnets.map(btn => {
      const isNavText = btn.matches('.nav-links a, .brand-mark, .brand-label')
      const factorX = isNavText ? 0.14 : 0.18
      const factorY = isNavText ? 0.18 : 0.25
      const move = (e) => {
        btn.style.transition = ''
        const r = btn.getBoundingClientRect()
        const mx = (e.clientX - r.left - r.width / 2) * factorX
        const my = (e.clientY - r.top - r.height / 2) * factorY
        btn.style.transform = `translate(${mx}px, ${my}px)`
      }
      const leave = () => {
        btn.style.transition = 'transform 0.22s ease-out'
        btn.style.transform = ''
        const resetTransition = (e) => {
          if (e.propertyName !== 'transform') return
          btn.style.transition = ''
          btn.removeEventListener('transitionend', resetTransition)
        }
        btn.addEventListener('transitionend', resetTransition)
      }
      btn.addEventListener('mousemove', move)
      btn.addEventListener('mouseleave', leave)
      return { btn, move, leave }
    })

    // animated counters
    const numObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return
        const el = e.target
        if (el.dataset.done) return
        el.dataset.done = '1'
        const original = el.innerHTML
        const text = el.textContent.replace(/ /g, ' ')
        const m = text.match(/(\d[\d\s]*)/)
        if (!m) return
        const target = parseInt(m[1].replace(/\s/g, ''), 10)
        if (isNaN(target) || target < 5) return
        const dur = 1400, start = performance.now()
        const ease = t => 1 - Math.pow(1 - t, 3)
        const fmt = n => n >= 1000 ? n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : String(n)
        function frame(now) {
          const t = Math.min(1, (now - start) / dur)
          const v = Math.round(target * ease(t))
          el.innerHTML = original.replace(m[1].replace(/\s/g, ' '), fmt(v)).replace(m[1], fmt(v))
          if (t < 1) requestAnimationFrame(frame); else el.innerHTML = original
        }
        requestAnimationFrame(frame)
        numObs.unobserve(el)
      })
    }, { threshold: 0.5 })
    document.querySelectorAll('.kpi .num, .hero-floating-card .num').forEach(el => numObs.observe(el))

    return () => {
      cancelAnimationFrame(raf)
      cancelAnimationFrame(glowRaf)
      io.disconnect()
      numObs.disconnect()
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('scroll', updateProgress)
      progressBar.remove()
      magnetHandlers.forEach(({ btn, move, leave }) => {
        btn.removeEventListener('mousemove', move)
        btn.removeEventListener('mouseleave', leave)
      })
    }
  }, [])
}
