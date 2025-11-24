import { supabase } from "@/lib/supabase";
import { Post } from "@/types/post";
import { MediaCard } from "@/components/media-card";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn, buildHref } from "@/lib/utils";

export const revalidate = 30;

export default async function Home({ searchParams }: { searchParams?: Promise<{ type?: string; after?: string; before?: string }> }) {
  const resolved = searchParams ? await searchParams : undefined;
  const type = resolved?.type;
  const after = resolved?.after;
  const before = resolved?.before;
  const perPage = 18;
  
  let query = supabase
    .from("posts")
    .select("id,created_at,content,media_type,media_url,width,height", { count: "exact" })
    .order("created_at", { ascending: false })
    .limit(perPage);
  if (type && ["image","video","audio","document","none"].includes(type)) {
    query = query.eq("media_type", type);
  }
  if (after) {
    query = query.lt("created_at", after);
  }
  if (before) {
    query = query.gt("created_at", before);
  }
  const { data } = await query;

  const posts = (data || []) as Post[];

  const active = type ?? "all";
  const hasPrev = Boolean(after || before);
  const hasNext = posts.length === perPage;
  const nextCursor = posts.length ? posts[posts.length - 1].created_at : undefined;
  const prevCursor = posts.length ? posts[0].created_at : undefined;

  return (
    <main className="pr-4 col-span-2">
      <div className="inline-flex h-9 items-center rounded-lg bg-muted p-[3px] mb-4">
        <Link
          href={buildHref({})}
          className={cn("px-2 py-1 rounded-md", active === "all" ? "bg-background" : undefined)}
        >
          همه
        </Link>
        <Link
          href={buildHref({ type: "image" })}
          className={cn("px-2 py-1 rounded-md", active === "image" ? "bg-background" : undefined)}
        >
          تصویر
        </Link>
        <Link
          href={buildHref({ type: "video" })}
          className={cn("px-2 py-1 rounded-md", active === "video" ? "bg-background" : undefined)}
        >
          ویدئو
        </Link>
        <Link
          href={buildHref({ type: "audio" })}
          className={cn("px-2 py-1 rounded-md", active === "audio" ? "bg-background" : undefined)}
        >
          صوتی
        </Link>
        <Link
          href={buildHref({ type: "none" })}
          className={cn("px-2 py-1 rounded-md", active === "none" ? "bg-background" : undefined)}
        >
          متنی
        </Link>
        <Link
          href={buildHref({ type: "document" })}
          className={cn("px-2 py-1 rounded-md", active === "document" ? "bg-background" : undefined)}
        >
          سند
        </Link>
      </div>
      <div className="columns-1 sm:columns-2 lg:columns-2 gap-4">
        {posts.map((p) => (
          <MediaCard key={p.id} post={p} />
        ))}
        {posts.length === 0 && <p className="text-zinc-600">هنوز پستی وجود ندارد.</p>}
      </div>
      <div className="mt-6 flex items-center justify-between">
        <Button
          asChild
          variant="outline"
          className={!hasPrev ? "pointer-events-none opacity-50" : undefined}
        >
          <Link href={buildHref({ type, before: prevCursor })}>
            قبلی
          </Link>
        </Button>
        <span className="text-sm text-muted-foreground">{active === 'all' ? 'زمان‌بندی' : 'فیلتر'} {active}</span>
        <Button asChild variant="ghost">
          <Link href={buildHref({ type })}>آخرین</Link>
        </Button>
        <Button
          asChild
          variant="outline"
          className={!hasNext || !nextCursor ? "pointer-events-none opacity-50" : undefined}
        >
          <Link href={buildHref({ type, after: nextCursor })}>
            بعدی
          </Link>
        </Button>
      </div>
    </main>
  );
}
