import type { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = process.env.NEXT_PUBLIC_SITE_URL || 'https://batarikh.xyz'
  const now = new Date()
  const base: MetadataRoute.Sitemap = [
    { url: `${site}/`, lastModified: now, changeFrequency: 'daily', priority: 1 },
  ]
  const types = ['image', 'video', 'audio', 'document', 'none']
  for (const t of types) {
    base.push({ url: `${site}/?type=${t}`, lastModified: now, changeFrequency: 'weekly', priority: 0.6 })
  }
  for (let p = 2; p <= 10; p++) {
    base.push({ url: `${site}/?page=${p}`, lastModified: now, changeFrequency: 'weekly', priority: 0.5 })
    for (const t of types) {
      base.push({ url: `${site}/?type=${t}&page=${p}`, lastModified: now, changeFrequency: 'weekly', priority: 0.5 })
    }
  }
  return base
}

