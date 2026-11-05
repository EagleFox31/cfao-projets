import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErreurApi, api, projets, requete } from './api'

describe('requete', () => {
  it('ignore les valeurs vides et encode le reste', () => {
    expect(requete({ q: 'a b', statut: '', nombre: 5, x: undefined, y: null })).toBe('?q=a+b&nombre=5')
    expect(requete({})).toBe('')
  })
})

describe('appeler', () => {
  afterEach(() => vi.unstubAllGlobals())

  function reponse(statut, corps) {
    return Promise.resolve(new Response(corps == null ? null : JSON.stringify(corps), {
      status: statut, headers: { 'Content-Type': 'application/json' },
    }))
  }

  it('renvoie le JSON et null pour 204', async () => {
    vi.stubGlobal('fetch', vi.fn(() => reponse(200, { ok: 1 })))
    expect(await api.get('/pj-donnees/x')).toEqual({ ok: 1 })
    vi.stubGlobal('fetch', vi.fn(() => reponse(204)))
    expect(await api.delete('/pj-donnees/x')).toBeNull()
  })

  it('leve ErreurApi avec le message du service', async () => {
    vi.stubGlobal('fetch', vi.fn(() => reponse(409, { erreur: 'Deja decidee.' })))
    await expect(projets.decider(3, { decision: 'acceptee' })).rejects.toMatchObject({ statut: 409, message: 'Deja decidee.' })
  })

  it('a un message par defaut pour 403 et 401', async () => {
    vi.stubGlobal('fetch', vi.fn(() => reponse(403, {})))
    const e = await api.get('/pj-donnees/x').catch(x => x)
    expect(e).toBeInstanceOf(ErreurApi)
    expect(e.message).toMatch(/autoris/i)
    vi.stubGlobal('fetch', vi.fn(() => reponse(401, {})))
    await expect(api.get('/pj-donnees/x')).rejects.toMatchObject({ statut: 401 })
  })

  it('envoie les parametres de semaine', async () => {
    const f = vi.fn(() => reponse(200, {}))
    vi.stubGlobal('fetch', f)
    await projets.activite(7, '2026-W45')
    expect(f.mock.calls[0][0]).toBe('/pj-donnees/projets/7/activite?semaine=2026-W45')
  })
})
