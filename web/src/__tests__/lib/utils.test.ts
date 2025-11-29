import { describe, it, expect } from 'vitest'
import { buildQuery, buildHref, sanitizeContent, escapeHtml } from '@/lib/utils'

describe('buildQuery', () => {
  it('should build query string from params', () => {
    expect(buildQuery({ type: 'image', page: '1' })).toBe('type=image&page=1')
  })

  it('should ignore undefined values', () => {
    expect(buildQuery({ type: 'image', page: undefined })).toBe('type=image')
  })

  it('should return empty string for empty params', () => {
    expect(buildQuery({})).toBe('')
  })
})

describe('buildHref', () => {
  it('should build href with query params', () => {
    expect(buildHref({ type: 'image', page: '1' })).toBe('/?type=image&page=1')
  })

  it('should return root path for empty params', () => {
    expect(buildHref({})).toBe('/')
  })
})

describe('sanitizeContent', () => {
  it('should remove trailing @batarikh mentions', () => {
    expect(sanitizeContent('Test content @batarikh')).toBe('Test content')
    expect(sanitizeContent('Test @BATARIKH')).toBe('Test')
  })

  it('should handle null and undefined', () => {
    expect(sanitizeContent(null)).toBeNull()
    expect(sanitizeContent(undefined)).toBeUndefined()
  })

  it('should trim whitespace', () => {
    expect(sanitizeContent('  Test  ')).toBe('Test')
  })
})

describe('escapeHtml', () => {
  it('should escape HTML entities', () => {
    expect(escapeHtml('<script>alert("xss")</script>')).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
    expect(escapeHtml('Test & more')).toBe('Test &amp; more')
  })
})

