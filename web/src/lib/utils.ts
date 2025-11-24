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
