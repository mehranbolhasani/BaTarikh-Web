/**
 * Application constants
 */

// Pagination
export const POSTS_PER_PAGE = 18
export const MAX_PAGINATION_PAGES = 10 // Used in sitemap generation

// Default values
export const DEFAULT_SITE_URL = 'https://batarikh.xyz'
export const DEFAULT_TELEGRAM_CHANNEL = 'batarikh'
export const DEFAULT_MEDIA_HOST = 'media.batarikh.xyz'

// Media types
export const MEDIA_TYPES = ['image', 'video', 'audio', 'document', 'none'] as const

export type MediaType = typeof MEDIA_TYPES[number]

/**
 * Type guard to check if a string is a valid media type
 */
export function isMediaType(value: string | undefined | null): value is MediaType {
  return value !== undefined && value !== null && MEDIA_TYPES.includes(value as MediaType)
}

// Media type labels (Persian)
export const MEDIA_TYPE_LABELS: Record<string, string> = {
  image: 'تصویر',
  video: 'ویدئو',
  audio: 'صوت',
  document: 'سند',
  none: 'متن',
}

// Image aspect ratios
export const DEFAULT_IMAGE_ASPECT_RATIO = '4/3'
export const DEFAULT_VIDEO_ASPECT_RATIO = '16/9'

// Pagination display
export const PAGINATION_RANGE = 2 // Number of pages to show on each side of current page

