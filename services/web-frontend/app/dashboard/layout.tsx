"use client"

import { useEffect, useState } from "react"
import { Activity, Home, Menu, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import DashboardNav from "@/components/DashboardNav"
import Link from "next/link"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => setMounted(true), [])

  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-page">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="mx-auto mb-4 h-12 w-12 rounded-full border-[3px] border-emerald-500 border-t-transparent"
          />
          <p className="text-sm text-muted-foreground">Loading dashboard…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-page text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="inline-flex rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-2">
              <Activity className="h-5 w-5 text-emerald-600" />
            </span>
            <div className="hidden sm:block">
              <h1 className="text-base font-semibold tracking-tight">EneGuardian</h1>
              <p className="text-xs text-muted-foreground">Real-time industrial monitoring</p>
            </div>
          </Link>

          <div className="flex items-center gap-2.5">
            <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1.5 lg:flex">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
              <span className="text-xs font-medium text-emerald-700">Live demo</span>
            </div>
            <Link
              href="/"
              title="Back to home"
              className="rounded-xl border border-border bg-background p-2.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <Home className="h-5 w-5" />
            </Link>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-xl border border-border bg-background p-2.5 text-muted-foreground transition-colors hover:bg-muted lg:hidden"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden border-b border-border bg-background lg:hidden"
          >
            <div className="mx-auto max-w-7xl px-4 py-4">
              <DashboardNav mobile onNavigate={() => setMobileMenuOpen(false)} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
        <div className="flex flex-col gap-6 lg:flex-row">
          <aside className="hidden w-60 shrink-0 lg:block">
            <div className="sticky top-24">
              <DashboardNav />
            </div>
          </aside>
          <div className="min-w-0 flex-1">{children}</div>
        </div>
      </main>
    </div>
  )
}
