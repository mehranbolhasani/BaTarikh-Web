'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error | null; resetError: () => void }>
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  resetError = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const Fallback = this.props.fallback
        return <Fallback error={this.state.error} resetError={this.resetError} />
      }
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <AlertCircle className="size-12 text-destructive mb-4" />
          <h2 className="text-2xl font-semibold mb-2">خطایی رخ داد</h2>
          <p className="text-muted-foreground mb-4">
            متأسفانه مشکلی در نمایش این بخش پیش آمده است.
          </p>
          {this.state.error && process.env.NODE_ENV === 'development' && (
            <pre className="text-xs bg-muted p-4 rounded-md mb-4 text-left max-w-2xl overflow-auto">
              {this.state.error.toString()}
            </pre>
          )}
          <Button onClick={this.resetError} variant="outline">
            تلاش مجدد
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}

