import { supabase } from "@/lib/supabase";
import { Post } from "@/types/post";

export default async function Home() {
  const { data } = await supabase
    .from("posts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(50);

  const posts = (data || []) as Post[];

  return (
    <main className="mx-auto max-w-6xl p-6">
      <h1 className="text-2xl font-semibold mb-6">Telegram Archive</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {posts.map((p) => (
          <div key={p.id} className="rounded border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
            {p.media_type === "image" && p.media_url && (
              <img src={p.media_url} alt="" className="w-full object-cover" />
            )}
            {p.media_type === "video" && p.media_url && (
              <video src={p.media_url} controls className="w-full" />
            )}
            {p.media_type === "audio" && p.media_url && (
              <audio src={p.media_url} controls className="w-full" />
            )}
            <div className="p-3">
              {p.content && <p className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">{p.content}</p>}
              <p className="mt-2 text-xs text-zinc-500">{new Date(p.created_at).toLocaleString()}</p>
            </div>
          </div>
        ))}
        {posts.length === 0 && <p className="text-zinc-600">No posts yet.</p>}
      </div>
    </main>
  );
}
