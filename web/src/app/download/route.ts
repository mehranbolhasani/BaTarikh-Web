import type { NextRequest } from "next/server"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const url = searchParams.get("url")
  const name = searchParams.get("name") || "file.pdf"
  if (!url) return new Response("Missing url", { status: 400 })
  let parsed: URL
  try {
    parsed = new URL(url)
  } catch {
    return new Response("Invalid url", { status: 400 })
  }
  if (parsed.protocol !== "https:") return new Response("Invalid protocol", { status: 400 })
  const allowedHost = process.env.NEXT_PUBLIC_MEDIA_HOST || "media.batarikh.xyz"
  if (parsed.hostname !== allowedHost) return new Response("Forbidden host", { status: 403 })
  const upstream = await fetch(url)
  if (!upstream.ok || !upstream.body) return new Response("Upstream error", { status: 502 })
  const filename = name || parsed.pathname.split("/").pop() || "file.pdf"
  const headers = new Headers()
  headers.set("Content-Type", "application/pdf")
  headers.set("Content-Disposition", `attachment; filename="${filename}"`)
  headers.set("Cache-Control", "public, max-age=86400")
  headers.set("X-Content-Type-Options", "nosniff")
  const len = upstream.headers.get("content-length")
  if (len) headers.set("Content-Length", len)
  return new Response(upstream.body, { status: 200, headers })
}
