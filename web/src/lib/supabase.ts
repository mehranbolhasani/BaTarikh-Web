import { createClient, type SupabaseClient } from '@supabase/supabase-js'

export function getSupabase(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY
  
  if (!url || !key) {
    if (process.env.NODE_ENV === 'development') {
      console.warn(
        'Supabase client not initialized:',
        !url ? 'NEXT_PUBLIC_SUPABASE_URL is missing' : 'NEXT_PUBLIC_SUPABASE_ANON_KEY is missing'
      )
    }
    return null
  }
  
  try {
    return createClient(url, key)
  } catch (error) {
    console.error('Failed to create Supabase client:', error)
    return null
  }
}
