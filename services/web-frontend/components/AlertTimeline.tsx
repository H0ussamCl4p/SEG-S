// Alert history timeline component

'use client'

import { formatDistanceToNow } from 'date-fns'
import { AlertCircle, AlertTriangle, Activity } from 'lucide-react'
import type { Alert } from '@/types'

interface AlertTimelineProps {
  alerts: Alert[];
}

export default function AlertTimeline({ alerts }: AlertTimelineProps) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="text-center py-8">
        <Activity className="w-12 h-12 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-500">No alerts in the last 24 hours</p>
        <p className="text-sm text-slate-600 mt-1">System operating normally</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
      {alerts.map((alert, index) => {
        const isAnomaly = alert.severity === 'ANOMALY'
        const bgColor = isAnomaly ? 'bg-red-500/10' : 'bg-yellow-500/10'
        const borderColor = isAnomaly ? 'border-red-500/30' : 'border-yellow-500/30'
        const textColor = isAnomaly ? 'text-red-500' : 'text-yellow-500'
        const Icon = isAnomaly ? AlertCircle : AlertTriangle

        return (
          <div
            key={`${alert.timestamp}-${index}`}
            className={`p-4 rounded-lg border ${bgColor} ${borderColor} transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-start gap-3">
              <div className={`mt-1 ${textColor}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-semibold text-sm ${textColor}`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <p className="text-sm text-white mb-2">{alert.message}</p>
                <div className="flex gap-4 text-xs text-slate-400">
                  <span>Vibration: {alert.vibration}</span>
                  <span>Temp: {alert.temperature}°C</span>
                  <span>Score: {alert.score}</span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
