"use client"

import { useState } from 'react'
import useSWR from 'swr'
import PredictionPanel from '@/components/PredictionPanel'
import RULPrediction from '@/components/RULPrediction'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export default function PredictionPage() {
  const [machineId, setMachineId] = useState<string>('MACHINE_002')
  const { data: machines } = useSWR<any[]>(apiUrl('/api/machines'), fetcher, { refreshInterval: 10000 })
  
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
              { machine_id: 'MACHINE_002', name: 'Conveyor Belt' },
              { machine_id: 'MACHINE_003', name: 'Industrial Motor' }
            ]).map((machine) => (
              <SelectItem key={machine.machine_id} value={machine.machine_id} className="text-white hover:bg-slate-800">
                {machine.machine_id} - {machine.machine_id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* RUL Prediction for Selected Machine */}
      <RULPrediction machineId={machineId} />
      
      {/* AI Prediction Panel */}
      <PredictionPanel equipmentId={machineId} />
    </div>
  )
}
