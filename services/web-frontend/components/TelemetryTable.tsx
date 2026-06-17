// Table to display recent raw telemetry readings

'use client'

import type { HistoricalData } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'

function toCsv(rows: HistoricalData[]): string {
  const header = ['timestamp','vibration','temperature','humidity','ai_health_percent','status']
  const lines = rows.map(r => {
    const pct = Math.max(0, Math.min(100, Math.round((r.score || 0) * 100)))
    const humidity = (r as any).humidity ?? ''
    const humStr = typeof humidity === 'number' ? humidity.toFixed(2) : ''
    return [r.timestamp, r.vibration.toFixed(2), r.temperature.toFixed(2), humStr, pct, r.status].join(',')
  })
  return [header.join(','), ...lines].join('\n')
}

interface TelemetryTableProps {
  data: HistoricalData[]
}

export default function TelemetryTable({ data }: TelemetryTableProps) {
  const rows = data.slice(-50).reverse()

  const handleExport = () => {
    const csv = toCsv(rows)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `telemetry_${new Date().toISOString().replace(/[:.]/g,'-')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">Recent Telemetry</CardTitle>
          <CardDescription>Latest {rows.length} readings</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={handleExport}>Export CSV</Button>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead className="text-right">Vibration</TableHead>
              <TableHead className="text-right">Temperature (°C)</TableHead>
              <TableHead className="text-right">Humidity (%)</TableHead>
              <TableHead className="text-right">AI Health (%)</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{new Date(row.timestamp).toLocaleTimeString()}</TableCell>
                <TableCell className="text-right">{row.vibration.toFixed(2)}</TableCell>
                <TableCell className="text-right">{row.temperature.toFixed(2)}</TableCell>
                <TableCell className="text-right">{(row as any).humidity != null ? Number((row as any).humidity).toFixed(2) : ''}</TableCell>
                <TableCell className="text-right">{Math.max(0, Math.min(100, Math.round((row.score || 0) * 100)))}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded-full text-xs ${row.status === 'ANOMALY' ? 'bg-red-500/10 text-red-400 border border-red-500/30' : row.status === 'WARNING' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'}`}>{row.status}</span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
