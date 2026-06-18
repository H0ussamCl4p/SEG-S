'use client'

import { motion } from 'framer-motion'
import { Activity, Wifi, AudioWaveform, MessageSquare, Gauge, ShieldCheck } from 'lucide-react'

const features = [
  {
    icon: Activity,
    title: 'AI anomaly detection',
    body: 'Isolation-Forest models score every reading in real time and surface anomalies before they become failures — no manual thresholds.',
  },
  {
    icon: AudioWaveform,
    title: 'Vibration spectrum analysis',
    body: 'FFT + envelope analysis with bearing characteristic frequencies (BPFO/BPFI) to catch incipient bearing faults early.',
  },
  {
    icon: Gauge,
    title: 'Health & RUL',
    body: 'A live health score and days-until-maintenance estimate from thermal and vibration degradation models.',
  },
  {
    icon: Wifi,
    title: 'Real-time MQTT',
    body: 'Stream telemetry from ESP32 boards and PLCs with sub-second latency into a time-series store.',
  },
  {
    icon: MessageSquare,
    title: 'AI maintenance assistant',
    body: 'A retrieval-augmented chatbot answers grounded in your equipment manuals — diagnoses, procedures, safety notes.',
  },
  {
    icon: ShieldCheck,
    title: 'Built to deploy',
    body: 'Containerised microservices running on Azure Container Apps with managed TLS and CI/CD.',
  },
]

export default function BentoGrid() {
  return (
    <section className="bg-background py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl"
        >
          <p className="text-sm font-medium uppercase tracking-widest text-emerald-600">Capabilities</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Everything you need to keep machines running.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            From raw sensor data to actionable diagnostics — condition monitoring that mirrors
            real industrial practice.
          </p>
        </motion.div>

        <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => {
            const Icon = f.icon
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.05 }}
                className="group rounded-2xl border border-border bg-background p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-md"
              >
                <div className="mb-5 inline-flex rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-2.5">
                  <Icon className="h-5 w-5 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.body}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
