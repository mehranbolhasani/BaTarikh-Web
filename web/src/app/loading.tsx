import { Skeleton } from '@/components/ui/skeleton'

export default function Loading() {
  return (
    <main className="p-0 md:pr-4 col-span-1 md:col-span-2 min-w-0">
      <div className="flex md:inline-flex h-12 items-center rounded-lg bg-card p-[5px] mb-4 shadow-sm">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-8 flex-1 mx-1" />
        ))}
      </div>
      <div className="columns-1 sm:columns-2 lg:columns-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-card rounded-2xl border border-amber-200 shadow-sm break-inside-avoid mb-4 overflow-hidden">
            <Skeleton className="w-full aspect-video" />
            <div className="p-8 pr-16">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-3/4" />
            </div>
            <div className="px-6 py-4 pr-16 border-t border-amber-200">
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        ))}
      </div>
    </main>
  )
}

