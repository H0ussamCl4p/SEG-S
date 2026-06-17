// Real-time AI score chart using Recharts

'use client'

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts'
import { format } from 'date-fns'
import type { HistoricalData } from '@/types'

interface LiveChartProps {
  data: HistoricalData[];
}

export default function LiveChart({ data }: LiveChartProps) {
  // Format data for Recharts
  const chartData = data.map(point => ({
    time: format(new Date(point.timestamp), 'HH:mm:ss'),
    // Convert to an easy-to-understand percentage (0-100)
    score: Math.max(0, Math.min(100, Math.round((point.score || 0) * 100))),
    status: point.status
  }))

  const renderTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const value = payload[0].value
      const status = data[payload[0].dataKeyIndex || 0]?.status || ''
      return (
        <div className="p-2 bg-slate-900/90 border border-slate-700 rounded-md">
          <div className="text-xs text-slate-400">{label}</div>
          <div className="text-sm text-white">AI Health: {value}%</div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis 
            dataKey="time" 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
            tickLine={{ stroke: '#334155' }}
          />
          <YAxis 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
            tickLine={{ stroke: '#334155' }}
            domain={[0, 100]}
            label={{ value: 'AI Health (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
          />
          <Tooltip content={renderTooltip} />
          <Legend wrapperStyle={{ color: '#94a3b8' }} />
          {/* Threshold bands */}
          <ReferenceLine y={10} label={{ value: 'Anomaly', position: 'right', fill: '#ef4444', fontSize: 12 }} stroke="#ef4444" strokeDasharray="4 4" />
          <ReferenceLine y={30} label={{ value: 'Warning', position: 'right', fill: '#f59e0b', fontSize: 12 }} stroke="#f59e0b" strokeDasharray="4 4" />
          <Area 
            type="monotone" 
            dataKey="score" 
            stroke="#10b981" 
            strokeWidth={2}
            isAnimationActive={false}
            fillOpacity={1} 
            fill="url(#scoreGradient)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
