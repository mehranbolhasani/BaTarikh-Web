import type { NextRequest } from "next/server"
import { DEFAULT_MEDIA_HOST } from "@/lib/constants"
import { checkRateLimit, getClientIP } from "@/lib/rate-limit"

export async function GET(req: NextRequest) {
  // Rate limiting: 10 requests per minute per IP
  const clientIP = getClientIP(req)
  const rateLimit = checkRateLimit(clientIP, {
    maxRequests: 10,
    windowMs: 60 * 1000, // 1 minute
  })

  if (!rateLimit.allowed) {
    const headers = new Headers()
    headers.set('Retry-After', String(Math.ceil((rateLimit.resetTime - Date.now()) / 1000)))
    headers.set('X-RateLimit-Limit', '10')
    headers.set('X-RateLimit-Remaining', '0')
    headers.set('X-RateLimit-Reset', String(Math.ceil(rateLimit.resetTime / 1000)))
    return new Response('Too Many Requests', { status: 429, headers })
  }

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
  const allowedHost = process.env.NEXT_PUBLIC_MEDIA_HOST || DEFAULT_MEDIA_HOST
  if (parsed.hostname !== allowedHost) return new Response("Forbidden host", { status: 403 })
  const upstream = await fetch(url)
  if (!upstream.ok || !upstream.body) return new Response("Upstream error", { status: 502 })
  const filename = name || parsed.pathname.split("/").pop() || "file.pdf"
  const headers = new Headers()
  headers.set("Content-Type", "application/pdf")
  headers.set("Content-Disposition", `attachment; filename="${filename}"`)
  headers.set("Cache-Control", "public, max-age=86400")
  headers.set("X-Content-Type-Options", "nosniff")
  headers.set('X-RateLimit-Limit', '10')
  headers.set('X-RateLimit-Remaining', String(rateLimit.remaining))
  headers.set('X-RateLimit-Reset', String(Math.ceil(rateLimit.resetTime / 1000)))
  const len = upstream.headers.get("content-length")
  if (len) headers.set("Content-Length", len)
  return new Response(upstream.body, { status: 200, headers })
}
