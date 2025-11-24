'use client'

import Image from 'next/image'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Post } from '@/types/post'
import dynamic from 'next/dynamic'
import { useEffect, useRef, useState, type ComponentType } from 'react'
import 'vidstack/styles/base.css'
import 'vidstack/styles/defaults.css'
import 'vidstack/styles/community-skin/audio.css'
import 'vidstack/styles/community-skin/video.css'
import { FileDown } from 'lucide-react'

type MediaPlayerProps = { src: string; title?: string; className?: string; children?: React.ReactNode }
type EmptyProps = Record<string, never>
const MediaPlayer = dynamic<MediaPlayerProps>(
  () => import('@vidstack/react').then(m => m.MediaPlayer as unknown as ComponentType<MediaPlayerProps>),
  { ssr: false }
)
const MediaOutlet = dynamic<EmptyProps>(
  () => import('@vidstack/react').then(m => m.MediaOutlet as unknown as ComponentType<EmptyProps>),
  { ssr: false }
)
const MediaCommunitySkin = dynamic<EmptyProps>(
  () => import('@vidstack/react').then(m => m.MediaCommunitySkin as unknown as ComponentType<EmptyProps>),
  { ssr: false }
)

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr)
    return new Intl.DateTimeFormat('fa-IR', {
      dateStyle: 'short',
      timeStyle: 'short',
      hourCycle: 'h24',
      timeZone: 'UTC',
    }).format(d)
  } catch {
    return new Date(dateStr).toISOString()
  }
}

function sanitizeContent(s?: string | null) {
  if (!s) return s
  try {
    return s.replace(/\s*@batarikh\s*$/i, '')
  } catch {
    return s
  }
}

export function MediaCard({ post }: { post: Post }) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry.isIntersecting) {
          setInView(true)
          obs.disconnect()
        }
      },
      { rootMargin: '200px', threshold: 0.1 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  

  return (
    <Card ref={ref}>
      {post.media_type === 'image' && post.media_url && (
        <div style={{ aspectRatio: (post.width && post.height) ? `${post.width}/${post.height}` : '4/3' }} className="w-full">
          <Image
            src={post.media_url}
            alt=""
            width={post.width ?? 800}
            height={post.height ?? 600}
            sizes="(min-width:1024px) 33vw, (min-width:640px) 50vw, 100vw"
            className="w-full h-full object-cover"
          />
        </div>
      )}
      {post.media_type === 'video' && post.media_url && (
        <div style={{ aspectRatio: (post.width && post.height) ? `${post.width}/${post.height}` : '16/9' }} className="w-full">
          {inView && (
            <MediaPlayer src={post.media_url} title="Video" className="w-full h-full">
              <MediaOutlet />
              <MediaCommunitySkin />
            </MediaPlayer>
          )}
        </div>
      )}
      {post.media_type === 'audio' && post.media_url && inView && (
        <MediaPlayer src={post.media_url} title="Audio" className="w-full">
          <MediaOutlet />
          <MediaCommunitySkin />
        </MediaPlayer>
      )}
      {post.media_type === 'document' && post.media_url && (
        <div className="w-full px-6">
          <Button asChild variant="outline" className="w-full justify-start">
            <a href={post.media_url} target="_blank" rel="noreferrer" download>
              <FileDown className="mr-2" />
              دانلود PDF
            </a>
          </Button>
        </div>
      )}
      <CardContent>
        {post.content && (
          <p className="text-sm whitespace-pre-wrap leading-6">{sanitizeContent(post.content)}</p>
        )}
      </CardContent>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Badge variant="secondary">{post.media_type}</Badge>
        </CardTitle>
        <CardDescription suppressHydrationWarning>
          <a
            href={`https://t.me/${process.env.NEXT_PUBLIC_TELEGRAM_CHANNEL || 'batarikh'}/${post.id}`}
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            {formatDate(post.created_at)}
          </a>
        </CardDescription>
      </CardHeader>
    </Card>
  )
}
