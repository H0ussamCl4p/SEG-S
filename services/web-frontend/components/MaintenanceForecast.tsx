'use client'

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Plus, AlertTriangle, Clock, Wrench } from 'lucide-react'
import { mutate } from 'swr'
import { apiUrl } from '@/lib/api-config'

interface MaintenanceForecastProps {
  machineId: string
  machineName: string
  healthScore: number
  daysUntilMaintenance: number
  criticalFactors: string[]
}

export default function MaintenanceForecast({
  machineId,
  machineName,
  healthScore,
  daysUntilMaintenance,
  criticalFactors
}: MaintenanceForecastProps) {
  const [isAdding, setIsAdding] = useState(false)

  const getUrgencyColor = (days: number) => {
    if (days <= 3) return 'bg-red-500/10 text-red-500 border-red-500/30'
    if (days <= 7) return 'bg-orange-500/10 text-orange-500 border-orange-500/30'
    if (days <= 14) return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30'
    return 'bg-green-500/10 text-green-500 border-green-500/30'
  }

  const getUrgencyIcon = (days: number) => {
    if (days <= 3) return '🔴'
    if (days <= 7) return '🟠'
    if (days <= 14) return '🟡'
    return '🟢'
  }

  const getPriorityLevel = (days: number): 'HIGH' | 'MEDIUM' | 'LOW' => {
    if (days <= 3) return 'HIGH'
    if (days <= 7) return 'MEDIUM'
    return 'LOW'
  }

  const handleAddToCalendar = async () => {
    setIsAdding(true)
    try {
      const dueDate = new Date()
      dueDate.setDate(dueDate.getDate() + Math.max(1, daysUntilMaintenance - 1))

      const nextDueDateStr = new Date(dueDate)
      nextDueDateStr.setDate(nextDueDateStr.getDate() + 30)

      const response = await fetch(apiUrl('/api/maintenance/tasks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          equipmentId: machineId,
          title: `Scheduled maintenance for ${machineName}`,
          description: `Predicted maintenance required based on AI analysis.\n\nHealth Score: ${healthScore}%\nDays until service: ${daysUntilMaintenance}\n\nCritical factors:\n${criticalFactors.map(f => `- ${f}`).join('\n')}`,
          dueDate: dueDate.toISOString().split('T')[0],
          nextDueDate: nextDueDateStr.toISOString().split('T')[0],
          priority: getPriorityLevel(daysUntilMaintenance),
          anomalyId: null,
          aiDetectedCause: `Predictive maintenance scheduling. Current health: ${healthScore}%. Estimated ${daysUntilMaintenance} days until service required.`,
        }),
      })

      if (response.ok) {
        await mutate(apiUrl('/api/maintenance/tasks'))
        alert(`✓ Maintenance task added to calendar for ${dueDate.toLocaleDateString()}`)
      } else {
        alert('Failed to add maintenance task')
      }
    } catch (error) {
      console.error('Failed to add task:', error)
      alert('Error adding maintenance task')
    } finally {
      setIsAdding(false)
    }
  }

  return (
    <Card className="border-slate-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-500" />
            Maintenance Forecast
          </CardTitle>
          <Badge variant="outline" className={getUrgencyColor(daysUntilMaintenance)}>
            {getUrgencyIcon(daysUntilMaintenance)} {daysUntilMaintenance} days
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Forecast Alert */}
        <div className={`p-4 rounded-lg border ${getUrgencyColor(daysUntilMaintenance)}`}>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold mb-1">
                {daysUntilMaintenance <= 3
                  ? '⚠️ Urgent: Maintenance Required Soon'
                  : daysUntilMaintenance <= 7
                    ? '⚠️ Maintenance Recommended This Week'
                    : 'Upcoming Maintenance'}
              </p>
              <p className="text-sm opacity-90">
                Based on current health score of <strong>{healthScore}%</strong>,
                maintenance is recommended in approximately <strong>{daysUntilMaintenance} days</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Critical Factors */}
        {criticalFactors.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
              <Wrench className="w-4 h-4" />
              Critical Factors
            </h4>
            <div className="space-y-2">
              {criticalFactors.map((factor, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm text-slate-400 bg-slate-900/50 p-2 rounded">
                  <span className="text-red-400">•</span>
                  {factor}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <Button
          onClick={handleAddToCalendar}
          disabled={isAdding}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        >
          {isAdding ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Adding...
            </>
          ) : (
            <>
              <Calendar className="w-4 h-4 mr-2" />
              <Plus className="w-4 h-4 mr-1" />
              Add to Maintenance Calendar
            </>
          )}
        </Button>

        <p className="text-xs text-slate-500 text-center">
          This will create a scheduled maintenance task in the calendar
        </p>
      </CardContent>
    </Card>
  )
}
