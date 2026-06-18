'use client'

import { useEffect, useState, useCallback } from 'react'
import { Activity, Waves, AlertTriangle, Gauge, TrendingUp } from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type SpecPoint = { f: number; m: number }
type Reading = {
  time?: { rms: number; peak: number; peak_to_peak: number; crest_factor: number; kurtosis: number; skewness: number }
  spectrum?: SpecPoint[]
  envelope?: SpecPoint[]
  bearing?: { shaft: number; BPFO: number; BPFI: number; BSF: number; FTF: number }
  fault?: { detected: boolean; type: string; fault_frequency_hz: number | null; confidence: number; ratios: Record<string, number> }
  condition?: string | null
  device_id?: string
  fs?: number
  shaft_hz?: number
  timestamp?: string
}
type Status = { reading: Reading | null; thresholds: { kurtosis_warn: number; crest_warn: number } }
type HistPoint = { time: string; rms?: number; kurtosis?: number; crest_factor?: number; fault_detected?: number }

function Card({ icon: Icon, label, value, unit, tone = 'neutral', sub }: {
  icon: React.ElementType; label: string; value: string; unit?: string
  tone?: 'neutral' | 'ok' | 'warn' | 'danger'; sub?: string
}) {
  const borders: Record<string, string> = {
    neutral: 'border-border', ok: 'border-emerald-500/40', warn: 'border-amber-500/50', danger: 'border-red-500/60',
  }
  const icons: Record<string, string> = {
    neutral: 'text-muted-foreground', ok: 'text-emerald-600', warn: 'text-amber-600', danger: 'text-red-600',
  }
  return (
    <div className={`p-5 rounded-2xl bg-background border ${borders[tone]}`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={`w-5 h-5 ${icons[tone]}`} />
        <span className="text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-foreground tabular-nums">{value}</span>
        {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
      </div>
      {sub && <p className="text-xs text-muted-foreground mt-2">{sub}</p>}
    </div>
  )
}

export default function SignalPage() {
  const [status, setStatus] = useState<Status | null>(null)
  const [history, setHistory] = useState<HistPoint[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([
        fetch(`${API_URL}/api/signal/status`).then(r => r.json()),
        fetch(`${API_URL}/api/signal/history?minutes=30`).then(r => r.ok ? r.json() : { points: [] }),
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

  const r = status?.reading
  const tf = r?.time
  const bf = r?.bearing
  const fault = r?.fault
  const th = status?.thresholds

  const kurt = tf?.kurtosis ?? null
  const crest = tf?.crest_factor ?? null
  const rms = tf?.rms ?? null

  const kurtTone: 'neutral' | 'ok' | 'warn' | 'danger' =
    kurt == null ? 'neutral' : kurt >= 6 ? 'danger' : th && kurt >= th.kurtosis_warn ? 'warn' : 'ok'
  const crestTone: 'neutral' | 'ok' | 'warn' | 'danger' =
    crest == null ? 'neutral' : crest >= 7 ? 'danger' : th && crest >= th.crest_warn ? 'warn' : 'ok'

  const faulty = !!fault?.detected
  const trend = history.map(p => ({
    t: new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    kurtosis: p.kurtosis ?? null,
    crest_factor: p.crest_factor ?? null,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Signal Analysis</h1>
          <p className="text-muted-foreground text-sm mt-1">
            FFT + envelope vibration diagnostics · device{' '}
            <span className="text-foreground font-mono">{r?.device_id ?? '—'}</span>
            {r?.fs && <> · {(r.fs / 1000).toFixed(0)} kHz · shaft {r?.shaft_hz} Hz</>}
          </p>
        </div>
        <div className={`px-3 py-1.5 rounded-full text-sm font-medium border ${faulty ? 'bg-red-500/15 border-red-500/40 text-red-700' : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700'}`}>
          {faulty ? `⚠ ${fault?.type}` : '● Healthy'}
          {fault?.confidence != null && faulty && <span className="ml-2 text-xs opacity-80">conf {(fault.confidence * 100).toFixed(0)}%</span>}
        </div>
      </div>

      {error && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-700 text-sm">{error}</div>}
      {!r && !error && (
        <div className="p-4 rounded-xl bg-background border border-border text-muted-foreground text-sm">
          Waiting for the first vibration window from the analyzer…
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card icon={Activity} label="RMS" value={rms != null ? rms.toFixed(3) : '—'} sub="overall energy" />
        <Card icon={TrendingUp} label="Kurtosis" value={kurt != null ? kurt.toFixed(2) : '—'} tone={kurtTone}
          sub={`warn ≥ ${th?.kurtosis_warn ?? 4} · impulsiveness`} />
        <Card icon={Gauge} label="Crest factor" value={crest != null ? crest.toFixed(2) : '—'} tone={crestTone}
          sub={`warn ≥ ${th?.crest_warn ?? 5}`} />
        <Card icon={AlertTriangle} label="Detected fault" value={faulty ? (fault?.fault_frequency_hz?.toFixed(0) ?? '—') : '—'}
          unit={faulty ? 'Hz' : ''} tone={faulty ? 'danger' : 'ok'}
          sub={faulty ? fault?.type : 'no defect frequency'} />
      </div>

      {/* FFT spectrum */}
      <div className="p-5 rounded-2xl bg-background border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Waves className="w-5 h-5 text-emerald-600" />
          <h2 className="text-lg font-semibold text-foreground">FFT spectrum</h2>
          <span className="text-xs text-muted-foreground ml-2">amplitude vs frequency (Hz)</span>
        </div>
        <div className="h-56">
          {!r?.spectrum?.length ? <Empty /> : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={r.spectrum}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e8eb" />
                <XAxis dataKey="f" stroke="#9aa3ad" fontSize={11} tickFormatter={(v) => `${v}`} />
                <YAxis stroke="#9aa3ad" fontSize={11} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e6e8eb', borderRadius: 8 }} labelStyle={{ color: '#0b0f12' }} />
                <Line type="monotone" dataKey="m" stroke="#10b981" strokeWidth={1.5} dot={false} name="amplitude" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Envelope spectrum with bearing-frequency markers */}
      <div className="p-5 rounded-2xl bg-background border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-5 h-5 text-amber-600" />
          <h2 className="text-lg font-semibold text-foreground">Envelope spectrum</h2>
          <span className="text-xs text-muted-foreground ml-2">reveals bearing defect frequencies</span>
        </div>
        <div className="h-56">
          {!r?.envelope?.length ? <Empty /> : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={r.envelope}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e8eb" />
                <XAxis dataKey="f" stroke="#9aa3ad" fontSize={11} />
                <YAxis stroke="#9aa3ad" fontSize={11} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e6e8eb', borderRadius: 8 }} labelStyle={{ color: '#0b0f12' }} />
                {bf && <ReferenceLine x={Math.round(bf.BPFO)} stroke="#ef4444" strokeDasharray="4 4" label={{ value: `BPFO ${bf.BPFO.toFixed(0)}`, fill: '#ef4444', fontSize: 10, position: 'top' }} />}
                {bf && <ReferenceLine x={Math.round(bf.BPFI)} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: `BPFI ${bf.BPFI.toFixed(0)}`, fill: '#f59e0b', fontSize: 10, position: 'top' }} />}
                <Line type="monotone" dataKey="m" stroke="#60a5fa" strokeWidth={1.5} dot={false} name="envelope" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
        {bf && (
          <p className="text-xs text-muted-foreground mt-3">
            Bearing freqs — BPFO {bf.BPFO.toFixed(1)} Hz · BPFI {bf.BPFI.toFixed(1)} Hz · BSF {bf.BSF.toFixed(1)} Hz · FTF {bf.FTF.toFixed(1)} Hz
            {fault?.ratios && <> · SNR BPFO {fault.ratios.BPFO}× / BPFI {fault.ratios.BPFI}×</>}
          </p>
        )}
      </div>

      {/* Kurtosis / crest trend */}
      <div className="p-5 rounded-2xl bg-background border border-border">
        <h2 className="text-lg font-semibold text-foreground mb-3">Kurtosis & crest factor (last 30 min)</h2>
        <div className="h-56">
          {trend.length === 0 ? <Empty /> : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e8eb" />
                <XAxis dataKey="t" stroke="#9aa3ad" fontSize={11} />
                <YAxis stroke="#9aa3ad" fontSize={11} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e6e8eb', borderRadius: 8 }} labelStyle={{ color: '#0b0f12' }} />
                <ReferenceLine y={th?.kurtosis_warn ?? 4} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'kurtosis warn', fill: '#f59e0b', fontSize: 10 }} />
                <Line type="monotone" dataKey="kurtosis" stroke="#10b981" strokeWidth={2} dot={false} name="kurtosis" />
                <Line type="monotone" dataKey="crest_factor" stroke="#a78bfa" strokeWidth={1.5} dot={false} name="crest factor" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

function Empty() {
  return <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No data yet.</div>
}
