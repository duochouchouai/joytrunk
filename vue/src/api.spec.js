import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getToken, setToken, clearToken } from './api'

describe('api', () => {
  let storage
  beforeEach(() => {
    storage = {}
    vi.stubGlobal('localStorage', {
      getItem: (k) => storage[k] ?? null,
      setItem: (k, v) => { storage[k] = String(v) },
      removeItem: (k) => { delete storage[k] },
    })
  })

  it('getToken returns null when localStorage is empty', () => {
    expect(getToken()).toBe(null)
  })

  it('setToken and getToken roundtrip', () => {
    setToken('owner-123')
    expect(getToken()).toBe('owner-123')
  })

  it('clearToken removes key', () => {
    setToken('owner-123')
    clearToken()
    expect(getToken()).toBe(null)
  })
})
