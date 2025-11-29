'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
      <AlertCircle className="size-12 text-destructive mb-4" />
      <h2 className="text-2xl font-semibold mb-2">خطایی رخ داد</h2>
      <p className="text-muted-foreground mb-4">
        متأسفانه مشکلی در نمایش صفحه پیش آمده است.
      </p>
      {process.env.NODE_ENV === 'development' && (
        <pre className="text-xs bg-muted p-4 rounded-md mb-4 text-left max-w-2xl overflow-auto">
          {error.message}
          {error.stack && (
            <>
              {'\n\n'}
              {error.stack}
            </>
          )}
        </pre>
      )}
      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          تلاش مجدد
        </Button>
        <Button onClick={() => window.location.href = '/'} variant="outline">
          بازگشت به صفحه اصلی
        </Button>
      </div>
    </div>
  )
}

