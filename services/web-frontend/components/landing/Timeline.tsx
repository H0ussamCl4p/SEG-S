'use client'

import { motion } from 'framer-motion'
import { Cpu, Radio, AudioWaveform, Bell } from 'lucide-react'

const steps = [
  {
    phase: 'DAY 0',
    title: 'Connect',
    body: 'Wire an ESP32 or PLC and publish sensor data over MQTT — or start instantly with the built-in simulator.',
    icon: Cpu,
    visual: (
      <div className="space-y-2">
        {['Thermocouple', 'Vibration', 'Humidity'].map((s) => (
          <div key={s} className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-xs">
            <span className="text-muted-foreground">{s}</span>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
          </div>
        ))}
      </div>
    ),
  },
  {
    phase: 'REAL-TIME',
    title: 'Ingest',
    body: 'Telemetry streams into a time-series store with sub-second latency, ready to query and chart.',
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
    phase: 'LIVE',
    title: 'Detect',
    body: 'AI anomaly scoring plus FFT + envelope analysis flag bearing faults at their characteristic frequencies.',
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
    phase: 'ONGOING',
    title: 'Act',
    body: 'Health scores, remaining-useful-life estimates, alerts and an AI assistant grounded in your manuals.',
    icon: Bell,
    visual: (
      <div className="space-y-2">
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-xs">
          <div className="font-semibold text-emerald-700">Health 100 · Excellent</div>
          <div className="text-muted-foreground">Next service in 24 days</div>
        </div>
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs">
          <div className="font-semibold text-amber-700">Warning · MACHINE_002</div>
          <div className="text-muted-foreground">High vibration 90.4</div>
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
            Live in a day. Insights from the first signal.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            From raw sensor to actionable diagnostics — here's how a machine goes online.
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
                {/* visual mock */}
                <div className="mb-5 min-h-[140px] rounded-2xl border border-border bg-background p-4 shadow-sm">
                  {s.visual}
                </div>
                {/* label + copy */}
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
