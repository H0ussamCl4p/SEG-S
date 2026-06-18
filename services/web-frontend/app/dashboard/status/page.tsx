"use client"

import useSWR from 'swr'
import MotorSensorStatusCard from '@/components/MotorSensorStatusCard'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { LiveData } from '@/types'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then(res => res.json())

interface Machine {
  machine_id: string
  name: string
  status: string
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    NORMAL: 'bg-green-500/10 text-emerald-600 border-green-500/30',
    WARNING: 'bg-yellow-500/10 text-amber-600 border-yellow-500/30',
    ANOMALY: 'bg-red-500/10 text-red-500 border-red-500/30',
    UNKNOWN: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
  }
  return <Badge variant="outline" className={variants[status] || variants.UNKNOWN}>{status}</Badge>
}

export default function StatusPage() {
  const { data: machines } = useSWR<Machine[]>(apiUrl('/api/machines'), fetcher, { refreshInterval: 3000 })
  const { data: liveData2 } = useSWR<LiveData>(apiUrl('/api/live?machine_id=MACHINE_002'), fetcher, { refreshInterval: 3000 })
  const { data: liveData3 } = useSWR<LiveData>(apiUrl('/api/live?machine_id=MACHINE_003'), fetcher, { refreshInterval: 3000 })

  const allMachines = [
    { id: 'MACHINE_002', name: 'Conveyor Belt', data: liveData2 },
    { id: 'MACHINE_003', name: 'Industrial Motor', data: liveData3 },
  ]

  return (
    <div className="space-y-6">
      <MotorSensorStatusCard />

      {/* Multi-Machine Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {allMachines.map((machine) => (
          <Card key={machine.id} className="border-slate-800">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{machine.name}</CardTitle>
                {machine.data && <StatusBadge status={machine.data.status} />}
              </div>
              <CardDescription className="text-xs">{machine.id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Vibration</span>
                  <span className="text-foreground font-medium">{machine.data?.vibration?.toFixed(1) || '--'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Temperature</span>
                  <span className="text-foreground font-medium">{machine.data?.temperature?.toFixed(1) || '--'}°C</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">AI Score</span>
                  <span className="text-foreground font-medium">{machine.data?.score?.toFixed(3) || '--'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Health</span>
                  <span className={`font-medium ${
                    (machine.data?.health?.score ?? 0) >= 80 ? 'text-emerald-600' :
                    (machine.data?.health?.score ?? 0) >= 50 ? 'text-amber-600' : 'text-red-600'
                  }`}>
                    {machine.data?.health?.score?.toFixed(0) || '--'}%
                  </span>
                </div>
                <div className="pt-2 border-t border-slate-800">
                  <span className="text-xs text-slate-500">
                    {machine.data?.timestamp ? new Date(machine.data.timestamp).toLocaleTimeString() : 'No data'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>System Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Total Machines</span>
              <span className="text-foreground font-medium">{machines?.length || 2}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">ESP MTTF model</span>
              <span className="text-foreground font-medium">Exponential thermal + linear vibration</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Refresh Interval</span>
              <span className="text-foreground font-medium">3 seconds</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Auto-Maintenance</span>
              <span className="text-emerald-600 font-medium">✓ Enabled</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
