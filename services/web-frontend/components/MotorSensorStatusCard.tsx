"use client"

import useSWR from "swr"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Cpu, Thermometer, Activity } from "lucide-react"
import { apiUrl } from '@/lib/api-config'

type ESPStatus = {
  reading: {
    temperature?: number | null
    humidity?: number | null
    thermocouple?: number | null
    vibration?: number | null
    device_id?: string
    timestamp?: string
    command?: { action: string; speed_percent: number; reason: string; source?: string }
  } | null
  override: { action: string; speed_percent: number } | null
  mttf: {
    status: string
    minutes: number | null
    dominant_signal?: string | null
    samples?: number
    window_minutes?: number
    thermal?: { model?: string; r_squared?: number; asymptote_c?: number; status_hint?: string }
  }
  thresholds: { temp_warn: number; temp_critical: number; temp_failure: number; vib_warn: number }
}

const fetcher = (url: string) => fetch(url).then(r => r.json())

function ageSeconds(iso?: string): number | null {
  if (!iso) return null
  const t = new Date(iso).getTime()
  if (isNaN(t)) return null
  return Math.max(0, Math.floor((Date.now() - t) / 1000))
}

export default function MotorSensorStatusCard() {
  const { data, error } = useSWR<ESPStatus>(apiUrl('/api/esp/status'), fetcher, { refreshInterval: 3000 })

  const r = data?.reading
  const age = ageSeconds(r?.timestamp)
  const online = age != null && age < 30
  const cmd = r?.command
  const mttf = data?.mttf

  const onlineBadge = error ? 'API Unreachable'
    : !r ? 'No Reading'
    : online ? 'Online'
    : 'Stale'

  const mttfText = !mttf ? '—'
    : mttf.status === 'nominal' ? 'Nominal'
    : mttf.status === 'insufficient_data' ? `Collecting (${mttf.samples ?? 0} samples)`
    : mttf.status === 'unavailable' ? 'n/a'
    : mttf.status === 'failed' ? 'FAILED'
    : mttf.minutes != null ? `${mttf.minutes} min (${mttf.status})`
    : '—'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-emerald-500" />
          ESP32 Motor Sensor
        </CardTitle>
        <CardDescription>Live telemetry from the field device · threshold logic + exponential MTTF</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Device</span>
          <div className="flex items-center gap-2">
            <span className="text-white font-mono text-sm">{r?.device_id ?? '—'}</span>
            <Badge variant="outline" className={
              error ? 'bg-red-500/10 text-red-400 border-red-500/30'
              : !r ? 'bg-slate-500/10 text-slate-400 border-slate-500/30'
              : online ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }>{onlineBadge}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <span className="text-slate-400 flex items-center gap-2 text-sm">
              <Thermometer className="w-4 h-4" /> Thermocouple
            </span>
            <p className="text-white font-medium">{r?.thermocouple != null ? `${r.thermocouple.toFixed(1)} °C` : '—'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400 flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4" /> Vibration
            </span>
            <p className="text-white font-medium">{r?.vibration != null ? r.vibration.toFixed(1) : '—'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400 text-sm">Motor command</span>
            <p className="text-white font-medium">
              {cmd?.action?.toUpperCase() ?? '—'} <span className="text-slate-500">{cmd?.speed_percent ?? 0}%</span>
              {cmd?.source === 'override' && (
                <span className="ml-2 text-xs text-amber-400">(manual)</span>
              )}
            </p>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400 text-sm">MTTF estimate</span>
            <p className="text-white font-medium">{mttfText}</p>
            {mttf?.thermal?.model && mttf.samples != null && (
              <p className="text-xs text-slate-500">
                {mttf.thermal.model} fit · R²={mttf.thermal.r_squared ?? 0} · n={mttf.samples}
              </p>
            )}
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800 flex justify-between text-xs text-slate-500">
          <span>{r?.timestamp ? `Last: ${new Date(r.timestamp).toLocaleTimeString()}` : 'Awaiting first reading'}</span>
          <span>Thresholds: warn {data?.thresholds?.temp_warn}°C · crit {data?.thresholds?.temp_critical}°C</span>
        </div>
      </CardContent>
    </Card>
  )
}
