'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, Github, Gauge, Activity, AudioWaveform } from 'lucide-react'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-page">
      {/* subtle dotted grid + soft emerald glow */}
      <div className="absolute inset-0 bg-grid opacity-60" />
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[480px] w-[820px] rounded-full bg-emerald-400/10 blur-[120px]" />

      <div className="relative mx-auto max-w-5xl px-6 pt-36 pb-20 text-center sm:pt-40">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3.5 py-1.5 text-sm text-muted-foreground shadow-sm"
        >
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          AI condition monitoring · Industry 4.0
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="mx-auto mt-7 max-w-4xl text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-6xl lg:text-7xl"
        >
          Predictive maintenance
          <br />
          for the modern factory.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl"
        >
          Stop downtime before it happens. Real-time anomaly detection, vibration
          spectrum analysis and an AI maintenance assistant — in one clean console.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/dashboard"
            className="group inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3.5 font-medium text-primary-foreground transition-colors hover:bg-zinc-800 sm:w-auto"
          >
            Open dashboard
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="https://github.com/H0ussamCl4p/SEG-S"
            target="_blank"
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-border bg-background px-6 py-3.5 font-medium text-foreground shadow-sm transition-colors hover:bg-muted sm:w-auto"
          >
            <Github className="h-4 w-4" />
            View on GitHub
          </Link>
        </motion.div>
      </div>

      {/* Clean product mockup */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="relative mx-auto max-w-5xl px-6 pb-24"
      >
        <div className="overflow-hidden rounded-2xl border border-border bg-background shadow-[0_24px_70px_-24px_rgba(11,15,18,0.25)]">
          <div className="flex items-center gap-2 border-b border-border bg-muted/60 px-4 py-3">
            <div className="flex gap-1.5">
              <span className="h-3 w-3 rounded-full bg-zinc-300" />
              <span className="h-3 w-3 rounded-full bg-zinc-300" />
              <span className="h-3 w-3 rounded-full bg-zinc-300" />
            </div>
            <div className="ml-3 flex-1 truncate rounded-md bg-background px-3 py-1 font-mono text-xs text-muted-foreground">
              eneguardian.app/dashboard
            </div>
          </div>

          <div className="grid gap-4 p-5 sm:p-7">
            <div className="grid grid-cols-3 gap-4">
              {[
                { icon: Gauge, label: 'Health score', value: '100', tone: 'text-emerald-600' },
                { icon: Activity, label: 'Active machines', value: '3', tone: 'text-foreground' },
                { icon: AudioWaveform, label: 'Fault freq.', value: '80 Hz', tone: 'text-amber-600' },
              ].map(({ icon: Icon, label, value, tone }) => (
                <div key={label} className="rounded-xl border border-border bg-background p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
                    <Icon className="h-4 w-4 text-emerald-500" /> {label}
                  </div>
                  <div className={`text-2xl font-semibold tabular-nums ${tone}`}>{value}</div>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-border bg-muted/40 p-5">
              <span className="font-mono text-xs text-muted-foreground">VIBRATION TREND</span>
              <div className="mt-4 flex h-28 items-end justify-between gap-1.5">
                {[38, 52, 46, 61, 55, 72, 64, 80, 70, 58, 49, 44].map((h, i) => (
                  <motion.div
                    key={i}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: 1 }}
                    transition={{ delay: 0.5 + i * 0.04, duration: 0.4 }}
                    className="w-full origin-bottom rounded-t bg-emerald-500/80"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  )
}
