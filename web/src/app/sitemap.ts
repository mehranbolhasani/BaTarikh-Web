import type { MetadataRoute } from 'next'
import { DEFAULT_SITE_URL, MEDIA_TYPES, MAX_PAGINATION_PAGES, type MediaType } from '@/lib/constants'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL
  const now = new Date()
  const base: MetadataRoute.Sitemap = [
    { url: `${site}/`, lastModified: now, changeFrequency: 'daily', priority: 1 },
  ]
  for (const t of MEDIA_TYPES as readonly MediaType[]) {
    base.push({ url: `${site}/?type=${t}`, lastModified: now, changeFrequency: 'weekly', priority: 0.6 })
  }
  for (let p = 2; p <= MAX_PAGINATION_PAGES; p++) {
    base.push({ url: `${site}/?page=${p}`, lastModified: now, changeFrequency: 'weekly', priority: 0.5 })
    for (const t of MEDIA_TYPES as readonly MediaType[]) {
      base.push({ url: `${site}/?type=${t}&page=${p}`, lastModified: now, changeFrequency: 'weekly', priority: 0.5 })
    }
  }
  return base
}

