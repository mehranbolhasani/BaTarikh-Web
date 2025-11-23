import { supabase } from "@/lib/supabase";
import { Post } from "@/types/post";
import { MediaCard } from "@/components/media-card";
import Link from "next/link";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";

export default async function Home({ searchParams }: { searchParams?: Promise<{ type?: string; page?: string }> }) {
  const resolved = searchParams ? await searchParams : undefined;
  const type = resolved?.type;
  const page = Math.max(1, Number(resolved?.page ?? 1) || 1);
  const perPage = 30;
  const from = (page - 1) * perPage;
  const to = from + perPage - 1;
  let query = supabase
    .from("posts")
    .select("*", { count: "exact" })
    .order("created_at", { ascending: false })
    .range(from, to);
  if (type && ["image","video","audio","none"].includes(type)) {
    query = query.eq("media_type", type);
  }
  const { data } = await query;

  const posts = (data || []) as Post[];

  const active = type ?? "all";
  const hasPrev = page > 1;
  const hasNext = (posts.length === perPage); // heuristic without count

  return (
    <main className="mx-auto max-w-7xl p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">بـاتاریخ</h1>
        <p className="text-sm text-muted-foreground">آرشیو کانال تلگرام batarikh</p>
      </div>
      <Tabs defaultValue={active} className="mb-4">
        <TabsList>
          <TabsTrigger value="all" asChild>
            <Link href={`/?${new URLSearchParams({ page: "1" }).toString()}`}>همه</Link>
          </TabsTrigger>
          <TabsTrigger value="image" asChild>
            <Link href={`/?${new URLSearchParams({ type: "image", page: "1" }).toString()}`}>تصویر</Link>
          </TabsTrigger>
          <TabsTrigger value="video" asChild>
            <Link href={`/?${new URLSearchParams({ type: "video", page: "1" }).toString()}`}>ویدئو</Link>
          </TabsTrigger>
          <TabsTrigger value="audio" asChild>
            <Link href={`/?${new URLSearchParams({ type: "audio", page: "1" }).toString()}`}>صوتی</Link>
          </TabsTrigger>
          <TabsTrigger value="none" asChild>
            <Link href={`/?${new URLSearchParams({ type: "none", page: "1" }).toString()}`}>متنی</Link>
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <div className="columns-1 sm:columns-2 lg:columns-3 gap-4">
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
          <Link href={`/?${new URLSearchParams({ ...(type ? { type } : {}), page: String(Math.max(1, page - 1)) }).toString()}`}>
            قبلی
          </Link>
        </Button>
        <span className="text-sm text-muted-foreground">صفحه {page}</span>
        <Button
          asChild
          variant="outline"
          className={!hasNext ? "pointer-events-none opacity-50" : undefined}
        >
          <Link href={`/?${new URLSearchParams({ ...(type ? { type } : {}), page: String(page + 1) }).toString()}`}>
            بعدی
          </Link>
        </Button>
      </div>
    </main>
  );
}
