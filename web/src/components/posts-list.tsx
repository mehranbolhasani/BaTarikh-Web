'use client'

import { ErrorBoundary } from '@/components/error-boundary'
import { MediaCard } from '@/components/media-card'
import type { Post } from '@/types/post'

export function PostsList({ posts }: { posts: Post[] }) {
  return (
    <ErrorBoundary>
      <div className="columns-1 sm:columns-2 lg:columns-2 gap-4">
        {posts.map((p) => (
          <ErrorBoundary key={p.id}>
            <MediaCard post={p} />
          </ErrorBoundary>
        ))}
        {posts.length === 0 && <p className="text-zinc-600">هنوز پستی وجود ندارد.</p>}
      </div>
    </ErrorBoundary>
  )
}

