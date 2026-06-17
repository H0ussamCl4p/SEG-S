// Simple passthrough provider wrapper

'use client'

export default function Providers({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
