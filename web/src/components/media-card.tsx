'use client'

import Image from 'next/image'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Post } from '@/types/post'
import { MediaPlayer, MediaOutlet, MediaCommunitySkin } from '@vidstack/react'

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

export function MediaCard({ post }: { post: Post }) {
  return (
    <Card>
      {post.media_type === 'image' && post.media_url && (
        <Image
          src={post.media_url}
          alt=""
          width={post.width ?? 800}
          height={post.height ?? 600}
          className="w-full h-auto object-cover"
        />
      )}
      {post.media_type === 'video' && post.media_url && (
        <MediaPlayer src={post.media_url} title="Video" className="w-full">
          <MediaOutlet />
          <MediaCommunitySkin />
        </MediaPlayer>
      )}
      {post.media_type === 'audio' && post.media_url && (
        <MediaPlayer src={post.media_url} title="Audio" className="w-full">
          <MediaOutlet />
          <MediaCommunitySkin />
        </MediaPlayer>
      )}
      <CardHeader className="border-b">
        <CardTitle className="text-base flex items-center gap-2">
          <Badge variant="secondary">{post.media_type}</Badge>
        </CardTitle>
        <CardDescription suppressHydrationWarning>{formatDate(post.created_at)}</CardDescription>
      </CardHeader>
      <CardContent>
        {post.content && (
          <p className="text-sm whitespace-pre-wrap leading-6">{post.content}</p>
        )}
      </CardContent>
    </Card>
  )
}
