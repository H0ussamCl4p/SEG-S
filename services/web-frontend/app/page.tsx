import Link from 'next/link'
import { Activity, ArrowRight } from 'lucide-react'
import Hero from '@/components/landing/Hero'
import BentoGrid from '@/components/landing/BentoGrid'
import Timeline from '@/components/landing/Timeline'
import StackMarquee from '@/components/landing/StackMarquee'
import FAQ from '@/components/landing/FAQ'

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <span className="inline-flex rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-1.5">
        <Activity className="h-5 w-5 text-emerald-600" />
      </span>
      <span className="text-lg font-semibold tracking-tight text-foreground">EneGuardian</span>
    </Link>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-emerald-500/20">
      {/* Nav */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Logo />
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="hidden text-sm font-medium text-muted-foreground transition-colors hover:text-foreground sm:block">
              Dashboard
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-zinc-800"
            >
              Try now
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      <main>
        <Hero />
        <BentoGrid />
        <Timeline />
        <StackMarquee />
        <FAQ />

        {/* Final CTA */}
        <section className="bg-background py-24 sm:py-32">
          <div className="mx-auto max-w-4xl px-6">
            <div className="relative overflow-hidden rounded-3xl border border-border bg-page px-8 py-16 text-center sm:px-16">
              <div className="pointer-events-none absolute -top-24 left-1/2 h-64 w-96 -translate-x-1/2 rounded-full bg-emerald-400/10 blur-3xl" />
              <div className="relative">
                <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
                  Ready to prevent downtime?
                </h2>
                <p className="mx-auto mt-4 max-w-xl text-lg text-muted-foreground">
                  Explore the live console — real-time telemetry, vibration diagnostics and an AI assistant.
                </p>
                <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                  <Link
                    href="/dashboard"
                    className="group inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-7 py-3.5 font-medium text-primary-foreground transition-colors hover:bg-zinc-800 sm:w-auto"
                  >
                    Open dashboard
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </Link>
                  <Link
                    href="https://github.com/H0ussamCl4p/SEG-S"
                    target="_blank"
                    className="inline-flex w-full items-center justify-center rounded-full border border-border bg-background px-7 py-3.5 font-medium text-foreground shadow-sm transition-colors hover:bg-muted sm:w-auto"
                  >
                    Documentation
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-background">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-10 sm:flex-row">
          <Logo />
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} EneGuardian · Energy optimisation & predictive maintenance for Industry 4.0
          </p>
        </div>
      </footer>
    </div>
  )
}
