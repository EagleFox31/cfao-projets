import { describe, expect, it } from 'vitest'
import { codeSemaine, decalerSemaine, libelleSemaine, lundiDe, lundiDuCode } from './semaine'

describe('semaine ISO', () => {
  it('calcule le lundi de la semaine', () => {
    expect(lundiDe(new Date(2026, 10, 5)).getDay()).toBe(1)
    expect(lundiDe(new Date(2026, 10, 8)).getDate()).toBe(2)
  })
  it('code la semaine au format AAAA-Www', () => {
    expect(codeSemaine(new Date(2026, 10, 5))).toBe('2026-W45')
    expect(codeSemaine(new Date(2027, 0, 1))).toBe('2026-W53')
    expect(codeSemaine(new Date(2024, 11, 30))).toBe('2025-W01')
  })
  it('retrouve le lundi depuis le code, refuse un code mal forme', () => {
    expect(lundiDuCode('2026-W45').getDate()).toBe(2)
    expect(lundiDuCode('2026-45')).toBeNull()
    expect(lundiDuCode('')).toBeNull()
  })
  it('decale de n semaines y compris sur une annee', () => {
    expect(decalerSemaine('2026-W01', -1)).toBe('2025-W52')
    expect(decalerSemaine('2026-W45', 2)).toBe('2026-W47')
  })
  it('libelle la semaine en francais', () => {
    expect(libelleSemaine('2026-W45')).toMatch(/2 nov\. au 8 novembre 2026/)
  })
})
