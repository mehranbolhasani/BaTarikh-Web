'use client'

import 'vidstack/styles/base.css'
import 'vidstack/styles/defaults.css'
import 'vidstack/styles/community-skin/video.css'
import { MediaPlayer, MediaOutlet, MediaCommunitySkin } from '@vidstack/react'

export function VideoPlayer({ src, title, className }: { src: string; title?: string; className?: string }) {
  return (
    <MediaPlayer src={src} title={title || 'Video'} className={className}>
      <MediaOutlet />
      <MediaCommunitySkin />
    </MediaPlayer>
  )
}

