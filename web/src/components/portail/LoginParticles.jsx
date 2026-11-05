/** Formes décoratives login — réparties gauche / droite, zone centrale allégée (carte). */
const PARTICLES = [
  { size: 48, top: '14%', left: '12%', delay: '0s', dur: '7.2s', driftY: 68, driftX: 32, spin: 16, opacity: 0.24, round: false },
  { size: 22, top: '28%', left: '22%', delay: '-2.2s', dur: '5.4s', driftY: 44, driftX: -28, spin: 0, opacity: 0.42, round: true },
  { size: 56, top: '46%', left: '8%', delay: '-4.5s', dur: '8.2s', driftY: 80, driftX: 38, spin: 20, opacity: 0.18, round: false },
  { size: 30, top: '68%', left: '18%', delay: '-1.2s', dur: '6.1s', driftY: 52, driftX: -36, spin: 12, opacity: 0.32, round: false },
  { size: 18, top: '82%', left: '10%', delay: '-3.8s', dur: '4.9s', driftY: 58, driftX: 24, spin: 0, opacity: 0.48, round: true },
  { size: 40, top: '22%', left: '78%', delay: '-5.2s', dur: '7.5s', driftY: 88, driftX: -44, spin: 22, opacity: 0.2, round: false },
  { size: 26, top: '36%', left: '88%', delay: '-1.8s', dur: '5.6s', driftY: 50, driftX: 30, spin: 0, opacity: 0.38, round: true },
  { size: 52, top: '54%', left: '72%', delay: '0s', dur: '7s', driftY: 72, driftX: 36, spin: 18, opacity: 0.28, round: false },
  { size: 34, top: '70%', left: '84%', delay: '-2.6s', dur: '6.4s', driftY: 64, driftX: -38, spin: 14, opacity: 0.34, round: false },
  { size: 20, top: '16%', left: '92%', delay: '-4s', dur: '5s', driftY: 46, driftX: 28, spin: 0, opacity: 0.45, round: true },
  { size: 36, top: '88%', left: '76%', delay: '-6s', dur: '7.8s', driftY: 70, driftX: -32, spin: 16, opacity: 0.22, round: false },
  { size: 24, top: '40%', left: '6%', delay: '-3.2s', dur: '5.8s', driftY: 54, driftX: 26, spin: 0, opacity: 0.3, round: true },
]

export default function LoginParticles() {
  return (
    <ul className="login-particles" aria-hidden="true">
      {PARTICLES.map((p, i) => (
        <li
          key={i}
          className={`login-particle${p.round ? ' login-particle--round' : ''}`}
          style={{
            '--p-size': `${p.size}px`,
            '--p-top': p.top,
            '--p-left': p.left,
            '--p-delay': p.delay,
            '--p-dur': p.dur,
            '--p-opacity': p.opacity,
            '--p-drift-y': `${p.driftY}px`,
            '--p-drift-x': `${p.driftX}px`,
            '--p-spin': `${p.spin}deg`,
          }}
        />
      ))}
    </ul>
  )
}
