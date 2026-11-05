import { describe, expect, it } from 'vitest'
import { liensPour } from './Nav'

describe('liensPour', () => {
  it('cache le journal aux profils ordinaires', () => {
    expect(liensPour({ roles: ['trainer'] }).map(l => l.to)).toEqual(['/', '/projets', '/propositions'])
  })
  it('montre le journal a la build team et au superadmin', () => {
    expect(liensPour({ roles: ['build_team'] }).some(l => l.to === '/journal-erreurs')).toBe(true)
    expect(liensPour({ roles: ['superadmin'] }).some(l => l.to === '/journal-erreurs')).toBe(true)
  })
})
