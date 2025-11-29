import type { MediaType } from '@/lib/constants'

export type { MediaType }

export interface Post {
  id: number
  created_at: string
  content: string | null
  media_type: MediaType
  media_url: string | null
  width: number | null
  height: number | null
}
