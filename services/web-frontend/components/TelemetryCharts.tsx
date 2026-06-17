// Charts for raw telemetry: vibration and temperature


'use client'

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import type { HistoricalData } from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

interface TelemetryChartsProps {
  data: HistoricalData[]
}

export default function TelemetryCharts({ data }: TelemetryChartsProps) {
  const chartData = data.map(p => ({
    time: format(new Date(p.timestamp), 'HH:mm:ss'),
    vibration: p.vibration,
    temperature: p.temperature,
    humidity: (p as any).humidity ?? null
  }))
  return (
    <Tabs defaultValue="vibration" className="w-full">
      <TabsList className="mb-4">
        <TabsTrigger value="vibration">Vibration</TabsTrigger>
        <TabsTrigger value="temperature">Temperature</TabsTrigger>
        <TabsTrigger value="humidity">Humidity</TabsTrigger>
      </TabsList>

      <TabsContent value="vibration">
        <Card>
          <CardHeader>
            <CardTitle>Vibration Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-64 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="vibGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#60a5fa" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} label={{ value: 'Vibration', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} labelStyle={{ color: '#94a3b8' }} />
                <Area type="monotone" dataKey="vibration" stroke="#60a5fa" strokeWidth={2} isAnimationActive={false} fillOpacity={1} fill="url(#vibGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="temperature">
        <Card>
          <CardHeader>
            <CardTitle>Temperature Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-64 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} labelStyle={{ color: '#94a3b8' }} />
                <Area type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} isAnimationActive={false} fillOpacity={1} fill="url(#tempGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="humidity">
        <Card>
          <CardHeader>
            <CardTitle>Humidity Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-64 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="humGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} tickLine={{ stroke: '#334155' }} label={{ value: 'Humidity (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} labelStyle={{ color: '#94a3b8' }} />
                <Area type="monotone" dataKey="humidity" stroke="#22c55e" strokeWidth={2} isAnimationActive={false} fillOpacity={1} fill="url(#humGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  )
}
