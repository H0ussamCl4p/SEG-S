'use client'

import { motion } from 'framer-motion'
import { Cpu, Radio, AudioWaveform, TrendingUp } from 'lucide-react'

const steps = [
  {
    phase: 'DAYS 1–2',
    title: 'Connect',
    body: 'Old machines get a small sensor box; modern lines tap straight into existing protocols (MQTT / PLC).',
    icon: Cpu,
    visual: (
      <div className="space-y-2">
        <div className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-xs">
          <span className="text-muted-foreground">Legacy machine</span>
          <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-700">sensor box</span>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-xs">
          <span className="text-muted-foreground">Modern line</span>
          <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-700">MQTT / PLC</span>
        </div>
      </div>
    ),
  },
  {
    phase: 'DAYS 3–4',
    title: 'Stream',
    body: 'Telemetry streams continuously to the AI; baselines and models calibrate to your equipment.',
    icon: Radio,
    visual: (
      <div className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
        {['factory/plc → 41.0', 'factory/plc → 78.2', 'factory/plc → 64.5'].map((t, i) => (
          <div key={i} className="truncate rounded-md border border-border bg-background px-2.5 py-1.5">{t}</div>
        ))}
      </div>
    ),
  },
  {
    phase: 'UNDER 1 WEEK',
    title: 'Go live',
    body: 'Anomaly detection plus FFT + envelope vibration analysis go live — dashboards, alerts and health scores.',
    icon: AudioWaveform,
    visual: (
      <div className="flex h-[88px] items-end justify-between gap-1 rounded-lg border border-border bg-background p-3">
        {[30, 44, 36, 70, 40, 88, 38, 52, 34].map((h, i) => (
          <div key={i} className={`w-full rounded-t ${h > 80 ? 'bg-red-500' : 'bg-emerald-500/70'}`} style={{ height: `${h}%` }} />
        ))}
      </div>
    ),
  },
  {
    phase: 'UNDER 7 MONTHS',
    title: 'Payback',
    body: 'Avoided unplanned downtime and condition-based maintenance deliver ROI in under seven months.',
    icon: TrendingUp,
    visual: (
      <div className="space-y-2">
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-xs">
          <div className="font-semibold text-emerald-700">Payback &lt; 7 months</div>
          <div className="text-muted-foreground">Downtime avoided</div>
        </div>
        <div className="rounded-lg border border-border bg-background px-3 py-2 text-xs">
          <div className="font-semibold text-foreground">Health 100 · Excellent</div>
          <div className="text-muted-foreground">Next service in 24 days</div>
        </div>
      </div>
    ),
  },
]

export default function Timeline() {
  return (
    <section className="bg-page py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl"
        >
          <p className="text-sm font-medium uppercase tracking-widest text-emerald-600">Timeline</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Live in under a week. Payback in under seven months.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Old or new machines — we connect, stream and act fast. Here's how a line goes online.
          </p>
        </motion.div>

        <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s, i) => {
            const Icon = s.icon
            return (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.08 }}
              >
                <div className="mb-5 min-h-[140px] rounded-2xl border border-border bg-background p-4 shadow-sm">
                  {s.visual}
                </div>
                <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">{s.phase}</p>
                <div className="mt-2 flex items-center gap-2">
                  <Icon className="h-4 w-4 text-emerald-600" />
                  <h3 className="text-lg font-semibold text-foreground">{s.title}</h3>
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
