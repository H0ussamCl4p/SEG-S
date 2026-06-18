"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import useSWR from 'swr'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

type Shift = {
  id: string
  name: string
  startTime: string
  endTime: string
  operator: string
  status: 'ACTIVE' | 'COMPLETED' | 'SCHEDULED'
  productionCount: number
  downtime: number
  efficiency: number
}

function StatusIcon({ status }: { status: Shift['status'] }) {
  if (status === 'ACTIVE') return <CheckCircle className="w-4 h-4 text-emerald-600" />
  if (status === 'COMPLETED') return <XCircle className="w-4 h-4 text-muted-foreground" />
  return <Clock className="w-4 h-4 text-amber-600" />
}

export default function ShiftManagementPage() {
  const { data: shifts = [], isLoading } = useSWR<Shift[]>(apiUrl('/api/shifts'), fetcher, {
    refreshInterval: 10000,
  })
  const { data: oeeData } = useSWR<any>(apiUrl('/api/production/oee'), fetcher, {
    refreshInterval: 10000,
  })

  // Get current shift metrics
  const activeShift = shifts.find(s => s.status === 'ACTIVE')
  const productionCount = activeShift?.productionCount || 0
  const downtime = activeShift?.downtime || 0
  const efficiency = oeeData?.oee || (activeShift?.efficiency || 0)

  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Shift Management</CardTitle>
          <CardDescription>Current and scheduled shifts with operator assignments</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading shifts...</div>
          ) : (
            <div className="space-y-3">
              {shifts.map(shift => (
                <div key={shift.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-background border border-border rounded-lg gap-4">
                  <div className="flex items-center gap-4">
                    <StatusIcon status={shift.status} />
                    <div>
                      <p className="text-foreground font-medium">{shift.name}</p>
                      <p className="text-muted-foreground text-sm">{shift.startTime} - {shift.endTime}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto">
                    <div className="text-left sm:text-right">
                      <p className="text-muted-foreground text-xs">Operator</p>
                      <p className="text-foreground text-sm">{shift.operator}</p>
                    </div>
                    <Badge variant="outline" className="border-border text-muted-foreground">
                      {shift.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Production Count</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{productionCount.toLocaleString()}</div>
            <p className="text-muted-foreground text-sm mt-1">units this shift</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Downtime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">{downtime} min</div>
            <p className="text-muted-foreground text-sm mt-1">total this shift</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Efficiency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">{efficiency.toFixed(1)}%</div>
            <p className="text-muted-foreground text-sm mt-1">OEE score</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
