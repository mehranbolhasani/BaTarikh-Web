'use client'

import 'vidstack/styles/base.css'
import 'vidstack/styles/defaults.css'
import 'vidstack/styles/community-skin/audio.css'
import { MediaPlayer, MediaOutlet, MediaCommunitySkin } from '@vidstack/react'

export function AudioPlayer({ src, title, className }: { src: string; title?: string; className?: string }) {
  return (
    <MediaPlayer src={src} title={title || 'Audio'} className={className}>
      <MediaOutlet />
      <MediaCommunitySkin />
    </MediaPlayer>
  )
}

