'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowRight, Database, AlertTriangle, TrendingUp, Activity,
  AudioWaveform, Cpu, MessageSquare, Wrench,
} from 'lucide-react'

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}
const item = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const stats = [
  { icon: Cpu, label: 'Machines monitored', value: '3', tone: 'text-foreground' },
  { icon: Activity, label: 'Telemetry', value: 'Live', tone: 'text-emerald-600' },
  { icon: AudioWaveform, label: 'Diagnostics', value: 'FFT · envelope', tone: 'text-foreground' },
]

const actions = [
  { href: '/dashboard/data', icon: Database, title: 'Live data', body: 'Real-time sensor telemetry and historical trends.' },
  { href: '/dashboard/signal', icon: AudioWaveform, title: 'Signal analysis', body: 'FFT + envelope vibration diagnostics and bearing fault detection.' },
  { href: '/dashboard/esp', icon: Cpu, title: 'Motor telemetry', body: 'ESP32 thermocouple + vibration with predictive motor control.' },
  { href: '/dashboard/anomaly', icon: AlertTriangle, title: 'Anomaly detection', body: 'AI-powered detection of equipment abnormalities.' },
  { href: '/dashboard/prediction', icon: TrendingUp, title: 'Prediction', body: 'Forecast equipment health and remaining useful life.' },
  { href: '/dashboard/chatbot', icon: MessageSquare, title: 'AI assistant', body: 'Ask maintenance questions grounded in your manuals.' },
]

export default function DashboardPage() {
  return (
    <motion.div variants={container} initial="hidden" animate="visible" className="space-y-8">
      {/* Header */}
      <motion.div variants={item}>
        <p className="text-sm font-medium uppercase tracking-widest text-emerald-600">Overview</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Welcome back</h1>
        <p className="mt-2 text-base text-muted-foreground">Monitor your industrial fleet in real time.</p>
      </motion.div>

      {/* At a glance */}
      <motion.div variants={container} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map(({ icon: Icon, label, value, tone }) => (
          <motion.div key={label} variants={item}
            className="rounded-2xl border border-border bg-background p-6 shadow-sm">
            <div className="mb-4 inline-flex rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-2.5">
              <Icon className="h-5 w-5 text-emerald-600" />
            </div>
            <div className={`text-2xl font-semibold ${tone}`}>{value}</div>
            <div className="mt-1 text-sm text-muted-foreground">{label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick actions */}
      <motion.div variants={item}>
        <div className="mb-4 flex items-center gap-2">
          <Wrench className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Quick actions</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {actions.map(({ href, icon: Icon, title, body }) => (
            <Link key={href} href={href} className="group">
              <div className="h-full rounded-2xl border border-border bg-background p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-md">
                <div className="mb-4 flex items-start justify-between">
                  <div className="inline-flex rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-2.5">
                    <Icon className="h-5 w-5 text-emerald-600" />
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground transition-all group-hover:translate-x-0.5 group-hover:text-foreground" />
                </div>
                <h3 className="text-lg font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{body}</p>
              </div>
            </Link>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}
