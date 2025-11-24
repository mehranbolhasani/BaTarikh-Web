import { getSupabase } from "@/lib/supabase";
import { Post } from "@/types/post";
import { MediaCard } from "@/components/media-card";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn, buildHref } from "@/lib/utils";
import { ArrowRight, ArrowLeft } from "lucide-react";

export const revalidate = 30;

export default async function Home({ searchParams }: { searchParams?: Promise<{ type?: string; page?: string }> }) {
  const resolved = searchParams ? await searchParams : undefined;
  const type = resolved?.type;
  const page = Math.max(1, Number(resolved?.page ?? 1) || 1);
  const perPage = 18;
  const from = (page - 1) * perPage;
  const to = from + perPage - 1;

  const client = getSupabase();
  let data: Post[] | null = null;
  let count: number | null = null;
  if (client) {
    let query = client
      .from("posts")
      .select("id,created_at,content,media_type,media_url,width,height", { count: "exact" })
      .order("created_at", { ascending: false })
      .range(from, to);
    if (type && ["image","video","audio","document","none"].includes(type)) {
      query = query.eq("media_type", type);
    }
    const res = await query;
    data = (res.data || []) as Post[];
    count = (res.count ?? null);
  } else {
    data = [];
    count = 0;
  }

  const posts = (data || []) as Post[];

  const active = type ?? "all";
  const total = typeof count === 'number' ? count : posts.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;
  const makePages = (current: number, total: number) => {
    const arr: (number | '...')[] = [];
    const add = (x: number | '...') => { arr.push(x) };
    const start = Math.max(2, current - 2);
    const end = Math.min(total - 1, current + 2);
    add(1);
    if (start > 2) add('...');
    for (let i = start; i <= end; i++) add(i);
    if (end < total - 1) add('...');
    if (total > 1) add(total);
    return arr;
  };
  const pages = makePages(page, totalPages);
  const fa = (n: number) => new Intl.NumberFormat('fa-IR').format(n);

  return (
    <main className="p-0 md:pr-4 col-span-1">
      <div className="flex md:inline-flexh-12 items-center rounded-lg bg-card p-[5px] mb-4 shadow-sm">
        <Link
          href={buildHref({ page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "all" ? "bg-primary text-primary-foreground" : undefined)}
        >
          همه
        </Link>
        <Link
          href={buildHref({ type: "image", page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "image" ? "bg-primary text-primary-foreground" : undefined)}
        >
          تصویر
        </Link>
        <Link
          href={buildHref({ type: "video", page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "video" ? "bg-primary text-primary-foreground" : undefined)}
        >
          ویدئو
        </Link>
        <Link
          href={buildHref({ type: "audio", page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "audio" ? "bg-primary text-primary-foreground" : undefined)}
        >
          صوتی
        </Link>
        <Link
          href={buildHref({ type: "none", page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "none" ? "bg-primary text-primary-foreground" : undefined)}
        >
          متنی
        </Link>
        <Link
          href={buildHref({ type: "document", page: "1" })}
          className={cn("px-2 py-1 rounded-md flex-1 text-center", active === "document" ? "bg-primary text-primary-foreground" : undefined)}
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
      <div className="mt-16 flex items-center justify-center w-fit mx-auto gap-4">
        <Button
          asChild
          variant="outline"
          className={!hasPrev ? "pointer-events-none opacity-50" : undefined}
        >
          <Link href={buildHref({ type, page: String(Math.max(1, page - 1)) })}>
            <ArrowRight className="size-4" />
          </Link>
        </Button>
        <span className="text-sm text-muted-foreground">صفحه {fa(page)} از {fa(totalPages)}</span>
        <div className="flex items-center gap-2">
          {pages.map((p, idx) => (
            p === '...'
              ? <span key={`dots-${idx}`} className="text-muted-foreground">…</span>
              : (
                <Button
                  key={p}
                  asChild
                  variant={p === page ? "default" : "ghost"}
                  size="sm"
                >
                  <Link href={buildHref({ type, page: String(p) })}>{fa(p as number)}</Link>
                </Button>
              )
          ))}
        </div>
        <Button
          asChild
          variant="outline"
          className={!hasNext ? "pointer-events-none opacity-50" : undefined}
        >
          <Link href={buildHref({ type, page: String(Math.min(totalPages, page + 1)) })}>
            <ArrowLeft className="size-4" />
          </Link>
        </Button>
      </div>
    </main>
  );
}
