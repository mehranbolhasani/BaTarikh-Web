import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function buildQuery(params: Record<string, string | undefined>) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v)
  }
  return q.toString()
}

export function buildHref(params: Record<string, string | undefined>) {
  const s = buildQuery(params)
  return s ? `/?${s}` : "/"
}

/**
 * Sanitize content by removing trailing @batarikh mentions
 * Note: React automatically escapes HTML in JSX, so XSS protection is handled by React
 * This function only removes unwanted content patterns
 */
export function sanitizeContent(s?: string | null): string | null | undefined {
  if (!s) return s
  try {
    // Remove trailing @batarikh mentions (case-insensitive)
    return s.replace(/\s*@batarikh\s*$/i, '').trim()
  } catch {
    return s
  }
}

/**
 * Escape HTML entities for use in attributes or when dangerouslySetInnerHTML is needed
 * For regular JSX, React handles this automatically
 */
export function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, (m) => map[m])
}
