import { getSupabase } from "@/lib/supabase";
import { Post } from "@/types/post";
import { PostsList } from "@/components/posts-list";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn, buildHref } from "@/lib/utils";
import { ArrowRight, ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Script from "next/script";
import {
  POSTS_PER_PAGE,
  DEFAULT_SITE_URL,
  DEFAULT_TELEGRAM_CHANNEL,
  MEDIA_TYPE_LABELS,
  PAGINATION_RANGE,
  isMediaType,
} from "@/lib/constants";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function generateMetadata({ searchParams }: { searchParams?: Promise<{ type?: string; page?: string }> }): Promise<Metadata> {
  const resolved = searchParams ? await searchParams : undefined
  const type = resolved?.type
  const page = Math.max(1, Number(resolved?.page ?? 1) || 1)
  const site = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL
  const titleBase = type && MEDIA_TYPE_LABELS[type] ? MEDIA_TYPE_LABELS[type] : undefined
  const suffix = titleBase
    ? (page > 1 ? `${titleBase} – صفحه ${new Intl.NumberFormat('fa-IR').format(page)}` : titleBase)
    : undefined
  const title = suffix ? `با تاریخ / ${suffix}` : undefined
  const href = buildHref({ type, page: String(page) })
  const canonical = `${site}${href === "/" ? "" : href}`
  const meta: Metadata = {
    alternates: { canonical },
    robots: { index: true, follow: true },
  }
  if (title) meta.title = title
  if (suffix) {
    meta.openGraph = { title }
    meta.twitter = { title }
  }
  return meta
}

export default async function Home({ searchParams }: { searchParams?: Promise<{ type?: string; page?: string }> }) {
  const resolved = searchParams ? await searchParams : undefined;
  const type = resolved?.type;
  const page = Math.max(1, Number(resolved?.page ?? 1) || 1);
  const from = (page - 1) * POSTS_PER_PAGE;
  const to = from + POSTS_PER_PAGE - 1;

  const client = getSupabase();
  let data: Post[] | null = null;
  let count: number | null = null;
  let error: string | null = null;
  
  if (client) {
    try {
      let query = client
        .from("posts")
        .select("id,created_at,content,media_type,media_url,width,height", { count: "exact" })
        .order("created_at", { ascending: false })
        .range(from, to);
      if (type && isMediaType(type)) {
        query = query.eq("media_type", type);
      }
      const res = await query;
      if (res.error) {
        console.error('Supabase query error:', res.error);
        error = 'خطا در دریافت اطلاعات';
        data = [];
        count = 0;
      } else {
        data = res.data || [];
        count = res.count ?? null;
      }
    } catch (err) {
      console.error('Error fetching posts:', err);
      error = 'خطا در اتصال به سرور';
      data = [];
      count = 0;
    }
  } else {
    console.warn('Supabase client not available - missing environment variables');
    data = [];
    count = 0;
  }

  const posts = data || [];

  const active = type ?? "all";
  const total = typeof count === 'number' ? count : posts.length;
  const totalPages = Math.max(1, Math.ceil(total / POSTS_PER_PAGE));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;
  const makePages = (current: number, total: number) => {
    const arr: (number | '...')[] = [];
    const add = (x: number | '...') => { arr.push(x) };
    const start = Math.max(2, current - PAGINATION_RANGE);
    const end = Math.min(total - 1, current + PAGINATION_RANGE);
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
    <main className="p-0 md:pr-4 col-span-1 md:col-span-2 min-w-0">
      <Script id="posts-jsonld" type="application/ld+json">
        {(() => {
          const channel = process.env.NEXT_PUBLIC_TELEGRAM_CHANNEL || DEFAULT_TELEGRAM_CHANNEL
          const items = posts.map((p, i) => ({
            '@type': 'ListItem',
            position: i + 1,
            url: `https://t.me/${channel}/${p.id}`,
          }))
          const sanitize = (s: unknown) => typeof s === 'string' ? s.replace(/\s*@batarikh\s*$/i, '').trim() : ''
          const graph = posts.map((p) => {
            const url = `https://t.me/${channel}/${p.id}`
            const content = sanitize(p.content)
            if (p.media_type === 'image' && p.media_url) {
              return { '@type': 'ImageObject', contentUrl: p.media_url, url, width: p.width || undefined, height: p.height || undefined, datePublished: p.created_at, name: content || undefined }
            }
            if (p.media_type === 'video' && p.media_url) {
              return { '@type': 'VideoObject', contentUrl: p.media_url, url, datePublished: p.created_at, name: content || undefined }
            }
            if (p.media_type === 'audio' && p.media_url) {
              return { '@type': 'AudioObject', contentUrl: p.media_url, url, datePublished: p.created_at, name: content || undefined }
            }
            if (p.media_type === 'document' && p.media_url) {
              return { '@type': 'CreativeWork', url, datePublished: p.created_at, name: content || undefined }
            }
            return { '@type': 'Article', url, datePublished: p.created_at, headline: content || undefined }
          })
          return JSON.stringify({ '@context': 'https://schema.org', '@type': 'ItemList', itemListElement: items, '@graph': graph })
        })()}
      </Script>
      <div className="flex md:inline-flex h-12 items-center rounded-lg bg-card p-[5px] mb-4 shadow-sm">
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
      {error && (
        <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-center">
          <p>{error}</p>
          <p className="text-sm mt-2 text-muted-foreground">لطفاً بعداً تلاش کنید.</p>
        </div>
      )}
      <PostsList posts={posts} />
      <div className="mt-16 flex items-center justify-center w-fit mx-auto gap-1 md:gap-4">
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
                  <Link href={buildHref({ type, page: String(p) })}>{fa(p)}</Link>
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
