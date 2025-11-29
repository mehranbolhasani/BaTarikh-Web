import type { MetadataRoute } from 'next'
import { DEFAULT_SITE_URL } from '@/lib/constants'

export default function robots(): MetadataRoute.Robots {
  const site = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL
  return {
    rules: [{ userAgent: '*', allow: '/' }],
    sitemap: [`${site}/sitemap.xml`],
  }
}

