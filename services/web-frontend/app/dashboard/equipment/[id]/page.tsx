"use client"

import { useParams } from 'next/navigation'
import useSWR from 'swr'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import TelemetryCharts from '@/components/TelemetryCharts'
import TelemetryTable from '@/components/TelemetryTable'
import PredictionPanel from '@/components/PredictionPanel'
import HealthScoreCard from '@/components/HealthScoreCard'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export default function EquipmentDetailPage() {
  const params = useParams<{ id: string }>()
  const equipmentId = params?.id as string

  const { data: historyData } = useSWR(
    apiUrl(`/api/history?limit=50&equipmentId=${encodeURIComponent(equipmentId)}`),
    fetcher,
    { refreshInterval: 10000 }
  )
  const { data: liveData } = useSWR(
    apiUrl(`/api/live?equipmentId=${encodeURIComponent(equipmentId)}`),
    fetcher,
    { refreshInterval: 1000 }
  )

  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Equipment: {equipmentId}</CardTitle>
          <CardDescription>Per-equipment telemetry and predictions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
            <div className="lg:col-span-1">
              {liveData?.health ? (
                <HealthScoreCard
                  score={liveData.health.score}
                  status={liveData.health.status}
                  daysUntilMaintenance={liveData.health.days_until_maintenance}
                  maintenanceUrgency={liveData.health.maintenance_urgency}
                />
              ) : (
                <div className="p-8 bg-slate-900/50 border border-slate-800 rounded-xl h-full flex items-center justify-center">
                  <p className="text-slate-500">Loading health...</p>
                </div>
              )}
            </div>
            <div className="lg:col-span-3">
              {historyData && historyData.length > 0 ? (
                <TelemetryCharts data={historyData} />
              ) : (
                <div className="h-48 flex items-center justify-center">
                  <p className="text-slate-500">Waiting for telemetry...</p>
                </div>
              )}
            </div>
          </div>

          <PredictionPanel equipmentId={equipmentId as any} />

          <TelemetryTable data={historyData || []} />
        </CardContent>
      </Card>
    </div>
  )
}
