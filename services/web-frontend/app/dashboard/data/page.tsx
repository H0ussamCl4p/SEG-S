"use client"

import { useState } from 'react'
import useSWR from 'swr'
import TelemetryCharts from '@/components/TelemetryCharts'
import TelemetryTable from '@/components/TelemetryTable'
import MetricCard from '@/components/MetricCard'
import { Gauge, Thermometer, Activity, TrendingUp } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { LiveData, HistoricalData } from '@/types'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export default function DataPage() {
  const [machineId, setMachineId] = useState<string>('MACHINE_001')
  const { data: machines } = useSWR<any[]>(apiUrl('/api/machines'), fetcher, { refreshInterval: 10000 })
  const { data: liveData } = useSWR<LiveData>(
    apiUrl(`/api/live?machine_id=${machineId}`),
    fetcher,
    { refreshInterval: 1000 }
  )
  const { data: historyData } = useSWR<HistoricalData[]>(
    apiUrl(`/api/history?limit=50&machine_id=${machineId}`),
    fetcher,
    { refreshInterval: 5000 }
  )

  return (
    <div className="space-y-6">
      {/* Machine Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <label className="text-slate-400 text-sm whitespace-nowrap">Machine:</label>
        <Select value={machineId} onValueChange={setMachineId}>
          <SelectTrigger className="w-full sm:w-[280px] bg-slate-900/60 border-slate-800 text-white">
            <SelectValue placeholder="Select Machine" />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 border-slate-800">
            {(machines || [
              { machine_id: 'MACHINE_001', name: 'Hydraulic Press' },
              { machine_id: 'MACHINE_002', name: 'Conveyor Belt' },
              { machine_id: 'MACHINE_003', name: 'Industrial Motor' }
            ]).map((machine) => (
              <SelectItem key={machine.machine_id} value={machine.machine_id} className="text-white hover:bg-slate-800">
                {machine.machine_id} - {machine.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Vibration" value={liveData?.vibration || 0} unit="units" icon={<Gauge className="w-5 h-5" />} />
        <MetricCard title="Temperature" value={liveData?.temperature || 0} unit="°C" icon={<Thermometer className="w-5 h-5" />} />
        <MetricCard title="Humidity" value={(liveData as any)?.humidity ?? 0} unit="%" icon={<Activity className="w-5 h-5" />} />
        <MetricCard title="AI Health" value={Math.max(0, Math.min(100, Math.round((liveData?.score || 0) * 100)))} unit="%" icon={<TrendingUp className="w-5 h-5" />} />
      </div>

      {/* Charts */}
      <TelemetryCharts data={historyData || []} />

      {/* Table */}
      <TelemetryTable data={historyData || []} />
    </div>
  )
}
