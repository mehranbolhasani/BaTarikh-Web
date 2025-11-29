import { describe, it, expect } from 'vitest'
import { MEDIA_TYPES, isMediaType, POSTS_PER_PAGE, DEFAULT_SITE_URL } from '@/lib/constants'

describe('constants', () => {
  it('should have correct media types', () => {
    expect(MEDIA_TYPES).toContain('image')
    expect(MEDIA_TYPES).toContain('video')
    expect(MEDIA_TYPES).toContain('audio')
    expect(MEDIA_TYPES).toContain('document')
    expect(MEDIA_TYPES).toContain('none')
  })

  it('should have correct default values', () => {
    expect(POSTS_PER_PAGE).toBe(18)
    expect(DEFAULT_SITE_URL).toBe('https://batarikh.xyz')
  })
})

describe('isMediaType', () => {
  it('should validate media types', () => {
    expect(isMediaType('image')).toBe(true)
    expect(isMediaType('video')).toBe(true)
    expect(isMediaType('invalid')).toBe(false)
    expect(isMediaType(null)).toBe(false)
    expect(isMediaType(undefined)).toBe(false)
  })
})

