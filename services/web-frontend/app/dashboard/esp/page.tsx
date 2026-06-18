'use client'

import { useEffect, useState, useCallback } from 'react'
import { Thermometer, Gauge, Droplets, Activity, Power, Turtle, Zap, RotateCcw } from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Reading = {
  temperature?: number | null
  humidity?: number | null
  thermocouple?: number | null
  vibration?: number | null
  device_id?: string
  timestamp?: string
  command?: { action: string; speed_percent: number; reason: string; source?: string }
}

type ThermalDetail = {
  model?: 'exponential' | 'linear'
  minutes?: number | null
  asymptote_c?: number
  tau_min?: number
  slope_c_per_min?: number
  r_squared?: number
  current_c?: number
  status_hint?: string
}
type VibrationDetail = {
  minutes?: number | null
  slope_per_min?: number
  r_squared?: number
  current?: number
  status_hint?: string
}
type Status = {
  reading: Reading | null
  override: { action: string; speed_percent: number; reason: string } | null
  mttf: {
    status: string
    minutes: number | null
    dominant_signal?: 'thermal' | 'vibration' | null
    current_c?: number
    thermal?: ThermalDetail
    vibration?: VibrationDetail | null
    samples?: number
    vibration_samples?: number
    window_minutes?: number
  }
  thresholds: { temp_warn: number; temp_critical: number; temp_failure: number; vib_warn: number }
}

type HistoryPoint = {
  time: string
  temperature?: number | null
  humidity?: number | null
  thermocouple?: number | null
  vibration?: number | null
}

function MetricCard({ icon: Icon, label, value, unit, tone = 'neutral' }: {
  icon: React.ElementType; label: string; value: string; unit?: string; tone?: 'neutral' | 'warn' | 'danger' | 'ok'
}) {
  const tones: Record<string, string> = {
    neutral: 'border-border',
    ok: 'border-emerald-500/40',
    warn: 'border-amber-500/50',
    danger: 'border-red-500/60',
  }
  const iconTones: Record<string, string> = {
    neutral: 'text-muted-foreground',
    ok: 'text-emerald-600',
    warn: 'text-amber-600',
    danger: 'text-red-600',
  }
  return (
    <div className={`p-5 rounded-2xl bg-background border ${tones[tone]}`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={`w-5 h-5 ${iconTones[tone]}`} />
        <span className="text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-foreground tabular-nums">{value}</span>
        {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
      </div>
    </div>
  )
}

export default function ESPPage() {
  const [status, setStatus] = useState<Status | null>(null)
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([
        fetch(`${API_URL}/api/esp/status`).then(r => r.json()),
        fetch(`${API_URL}/api/esp/history?minutes=30`).then(r => r.ok ? r.json() : { points: [] }),
      ])
      setStatus(s)
      setHistory(h.points || [])
      setError(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to reach AI engine')
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [refresh])

  const sendCommand = async (action: 'stop' | 'slow' | 'normal' | 'auto') => {
    setSending(true)
    try {
      await fetch(`${API_URL}/api/esp/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      })
      await refresh()
    } catch (e: any) {
      setError(e?.message || 'Command failed')
    } finally {
      setSending(false)
    }
  }

  const r = status?.reading
  const cmd = r?.command
  const th = status?.thresholds

  const thermo = r?.thermocouple ?? null
  const ambient = r?.temperature ?? null
  const humidity = r?.humidity ?? null
  const vibration = r?.vibration ?? null

  const thermoTone: 'neutral' | 'ok' | 'warn' | 'danger' =
    thermo == null ? 'neutral'
      : th && thermo >= th.temp_critical ? 'danger'
      : th && thermo >= th.temp_warn ? 'warn'
      : 'ok'

  const vibTone: 'neutral' | 'ok' | 'warn' | 'danger' =
    vibration == null ? 'neutral'
      : th && vibration >= th.vib_warn * 1.5 ? 'danger'
      : th && vibration >= th.vib_warn ? 'warn'
      : 'ok'

  const mttf = status?.mttf
  const mttfText = !mttf ? '—'
    : mttf.status === 'nominal' ? 'Nominal'
    : mttf.status === 'insufficient_data' ? 'Collecting data…'
    : mttf.status === 'failed' ? 'FAILED'
    : mttf.status === 'unavailable' ? 'n/a'
    : mttf.minutes != null ? `${mttf.minutes} min`
    : '—'

  const mttfTone =
    !mttf ? 'text-muted-foreground'
      : mttf.status === 'critical' ? 'text-red-600'
      : mttf.status === 'warning' ? 'text-amber-600'
      : mttf.status === 'failed' ? 'text-red-500'
      : 'text-emerald-600'

  const t = mttf?.thermal
  const v = mttf?.vibration
  const dominant = mttf?.dominant_signal
  const mttfDetail = (() => {
    if (!mttf) return null
    if (mttf.status === 'insufficient_data') return `${mttf.samples ?? 0} samples · need 3+ over ${mttf.window_minutes ?? 30} min`
    if (mttf.status === 'unavailable') return 'InfluxDB unreachable'
    if (mttf.status === 'error') return 'Computation error'
    const parts: string[] = []
    if (dominant) parts.push(`driven by ${dominant}`)
    if (t?.model === 'exponential' && t.asymptote_c != null) {
      parts.push(`asymptote ${t.asymptote_c}°C, τ=${t.tau_min}min, R²=${t.r_squared}`)
    } else if (t?.model === 'linear' && t.slope_c_per_min != null) {
      parts.push(`linear ${t.slope_c_per_min > 0 ? '+' : ''}${t.slope_c_per_min}°C/min, R²=${t.r_squared}`)
    }
    if (v?.slope_per_min != null && v.slope_per_min > 0.01) {
      parts.push(`vibration ${v.slope_per_min > 0 ? '+' : ''}${v.slope_per_min}/min`)
    }
    parts.push(`window ${mttf.window_minutes ?? 30}min · n=${mttf.samples ?? 0}`)
    return parts.join(' · ')
  })()

  const chartData = history
    .filter(p => p.thermocouple != null || p.temperature != null)
    .map(p => ({
      t: new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      thermocouple: p.thermocouple ?? null,
      ambient: p.temperature ?? null,
    }))

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Motor Telemetry</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Live readings from ESP32 · device: <span className="text-foreground font-mono">{r?.device_id ?? '—'}</span>
          </p>
        </div>
        {r?.timestamp && (
          <div className="text-xs text-muted-foreground font-mono">
            Last reading: {new Date(r.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-700 text-sm">
          {error}
        </div>
      )}

      {!r && !error && (
        <div className="p-4 rounded-xl bg-background border border-border text-muted-foreground text-sm">
          Waiting for the first ESP32 reading… Make sure the board is powered, on Wi-Fi, and POSTing to
          <span className="font-mono text-foreground"> {API_URL}/api/esp/ingest</span>.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard icon={Thermometer} label="Motor (thermocouple)"
          value={thermo != null ? thermo.toFixed(1) : '—'} unit="°C" tone={thermoTone} />
        <MetricCard icon={Thermometer} label="Ambient (DHT22)"
          value={ambient != null ? ambient.toFixed(1) : '—'} unit="°C" />
        <MetricCard icon={Droplets} label="Humidity"
          value={humidity != null ? humidity.toFixed(0) : '—'} unit="%" />
        <MetricCard icon={Activity} label="Vibration"
          value={vibration != null ? vibration.toFixed(1) : '—'} tone={vibTone} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-background border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Gauge className="w-5 h-5 text-muted-foreground" />
            <span className="text-xs uppercase tracking-wider text-muted-foreground">Motor command</span>
          </div>
          <div className="flex items-baseline gap-3 mb-2">
            <span className="text-3xl font-bold text-foreground">{cmd?.action?.toUpperCase() ?? '—'}</span>
            <span className="text-muted-foreground">{cmd?.speed_percent ?? 0}%</span>
            {cmd?.source === 'override' && (
              <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-700">manual</span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{cmd?.reason ?? 'No reading yet.'}</p>
        </div>

        <div className="p-5 rounded-2xl bg-background border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-muted-foreground" />
            <span className="text-xs uppercase tracking-wider text-muted-foreground">MTTF estimate</span>
          </div>
          <div className={`text-3xl font-bold ${mttfTone}`}>{mttfText}</div>
          <p className="text-xs text-muted-foreground mt-2">
            {mttfDetail ?? 'Exponential thermal model + linear vibration trend, EMA-smoothed.'}
          </p>
          {t?.status_hint === 'stabilizing' && t.asymptote_c != null && (
            <p className="text-xs text-emerald-600 mt-1">
              Asymptoting to {t.asymptote_c}°C — below failure threshold ({th?.temp_failure ?? 110}°C).
            </p>
          )}
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-background border border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">Manual override</h2>
          <span className="text-xs text-muted-foreground">
            {status?.override ? `Active: ${status.override.action.toUpperCase()}` : 'Auto (threshold logic)'}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            disabled={sending}
            onClick={() => sendCommand('stop')}
            className="flex items-center justify-center gap-2 py-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-700 hover:bg-red-500/30 transition disabled:opacity-50"
          >
            <Power className="w-4 h-4" /> STOP
          </button>
          <button
            disabled={sending}
            onClick={() => sendCommand('slow')}
            className="flex items-center justify-center gap-2 py-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-700 hover:bg-amber-500/30 transition disabled:opacity-50"
          >
            <Turtle className="w-4 h-4" /> SLOW
          </button>
          <button
            disabled={sending}
            onClick={() => sendCommand('normal')}
            className="flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-700 hover:bg-emerald-500/30 transition disabled:opacity-50"
          >
            <Zap className="w-4 h-4" /> NORMAL
          </button>
          <button
            disabled={sending}
            onClick={() => sendCommand('auto')}
            className="flex items-center justify-center gap-2 py-3 rounded-xl bg-background border border-white/20 text-foreground hover:bg-muted transition disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" /> AUTO
          </button>
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-background border border-border">
        <h2 className="text-lg font-semibold text-foreground mb-3">Thermocouple (last 30 min)</h2>
        <div className="h-64">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No data yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e8eb" />
                <XAxis dataKey="t" stroke="#9aa3ad" fontSize={11} />
                <YAxis stroke="#9aa3ad" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #e6e8eb', borderRadius: 8 }}
                  labelStyle={{ color: '#0b0f12' }}
                />
                {th && <ReferenceLine y={th.temp_warn} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'warn', fill: '#f59e0b', fontSize: 10 }} />}
                {th && <ReferenceLine y={th.temp_critical} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'critical', fill: '#ef4444', fontSize: 10 }} />}
                <Line type="monotone" dataKey="thermocouple" stroke="#10b981" strokeWidth={2} dot={false} name="Motor °C" />
                <Line type="monotone" dataKey="ambient" stroke="#60a5fa" strokeWidth={1.5} dot={false} name="Ambient °C" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
