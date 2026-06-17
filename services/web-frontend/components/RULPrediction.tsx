'use client'

import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, TrendingDown, AlertTriangle, CheckCircle, Activity, Calendar, Plus } from 'lucide-react'
import { mutate } from 'swr'
import { apiUrl } from '@/lib/api-config'

interface RULData {
  machine_id: string
  rul_days: number
  confidence: number
  health_score: number
  degradation_rate: number
  critical_factors: string[]
  recommendation: string
  status: 'CRITICAL' | 'WARNING' | 'ATTENTION' | 'NORMAL' | 'HEALTHY'
  urgency: 'IMMEDIATE' | 'HIGH' | 'MEDIUM' | 'LOW'
  predicted_failure_date: string
  avg_vibration: number
  avg_temperature: number
}

interface RULPredictionProps {
  machineId?: string
  compact?: boolean
}

export default function RULPrediction({ machineId, compact = false }: RULPredictionProps) {
  const [rulData, setRulData] = useState<RULData[]>([])
  const [loading, setLoading] = useState(true)
  const [addingTaskFor, setAddingTaskFor] = useState<string | null>(null)

  useEffect(() => {
    const fetchRUL = async () => {
      try {
        setLoading(true)
        const url = machineId 
          ? apiUrl(`/api/rul?machine_id=${machineId}`)
          : apiUrl('/api/rul')
        
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setRulData(Array.isArray(data) ? data : [data])
        }
      } catch (error) {
        console.error('Failed to fetch RUL data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRUL()
    const interval = setInterval(fetchRUL, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [machineId])

  const getPriorityLevel = (urgency: string): 'HIGH' | 'MEDIUM' | 'LOW' => {
    if (urgency === 'IMMEDIATE' || urgency === 'HIGH') return 'HIGH'
    if (urgency === 'MEDIUM') return 'MEDIUM'
    return 'LOW'
  }

  const handleAddToCalendar = async (data: RULData) => {
    setAddingTaskFor(data.machine_id)
    try {
      const dueDate = new Date()
      dueDate.setDate(dueDate.getDate() + Math.max(1, data.rul_days - 1))
      
      const response = await fetch(apiUrl('/api/maintenance/tasks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          equipmentId: data.machine_id,
          title: `RUL-predicted maintenance for ${data.machine_id}`,
          description: `ML-predicted maintenance based on RUL analysis.\n\nRemaining Useful Life: ${data.rul_days} days\nHealth Score: ${data.health_score}%\nConfidence: ${data.confidence}%\nDegradation Rate: ${data.degradation_rate}%/day\n\nCritical Factors:\n${data.critical_factors.map(f => `- ${f}`).join('\n')}\n\nRecommendation: ${data.recommendation}`,
          dueDate: dueDate.toISOString().split('T')[0],
          priority: getPriorityLevel(data.urgency),
          anomalyId: null,
          aiDetectedCause: `RUL Prediction: ${data.rul_days} days remaining. Status: ${data.status}. ${data.recommendation}`,
        }),
      })
      
      if (response.ok) {
        await mutate(apiUrl('/api/maintenance/tasks'))
        alert(`✓ Maintenance task scheduled for ${dueDate.toLocaleDateString()}`)
      } else {
        alert('Failed to create maintenance task')
      }
    } catch (error) {
      console.error('Failed to add task:', error)
      alert('Error creating maintenance task')
    } finally {
      setAddingTaskFor(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL': return 'bg-red-500'
      case 'WARNING': return 'bg-orange-500'
      case 'ATTENTION': return 'bg-yellow-500'
      case 'NORMAL': return 'bg-blue-500'
      case 'HEALTHY': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'IMMEDIATE': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'HIGH': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'LOW': return 'text-green-400 bg-green-500/10 border-green-500/30'
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'CRITICAL':
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5" />
      case 'ATTENTION':
        return <Activity className="w-5 h-5" />
      case 'HEALTHY':
        return <CheckCircle className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  if (loading) {
    return (
      <Card className="border-slate-800">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (compact && rulData.length > 0) {
    const data = rulData[0]
    return (
      <div className={`p-4 rounded-lg border ${getUrgencyColor(data.urgency)}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            <span className="font-semibold">Remaining Useful Life</span>
          </div>
          <Badge className={getStatusColor(data.status)}>
            {data.status}
          </Badge>
        </div>
        <div className="text-3xl font-bold mb-1">{data.rul_days} days</div>
        <div className="text-sm opacity-80 mb-3">Until maintenance required</div>
        <div className="text-xs opacity-70">{data.recommendation}</div>
      </div>
    )
  }

  return (
    <Card className="border-slate-800">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-500" />
          Remaining Useful Life (RUL) Prediction
        </CardTitle>
        <CardDescription>
          ML-based prediction of days until maintenance required
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {rulData.map((data) => (
          <div key={data.machine_id} className="border border-slate-800 rounded-lg p-4 space-y-4">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${getStatusColor(data.status)} bg-opacity-20 shrink-0`}>
                  {getStatusIcon(data.status)}
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-lg truncate">{data.machine_id}</h3>
                  <p className="text-sm text-slate-400">
                    Health: {data.health_score}% • Confidence: {data.confidence}%
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge className={getStatusColor(data.status)}>
                  {data.status}
                </Badge>
                <Button
                  size="sm"
                  onClick={() => handleAddToCalendar(data)}
                  disabled={addingTaskFor === data.machine_id}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {addingTaskFor === data.machine_id ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-1" />
                      Schedule
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* RUL Display */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className={`p-4 rounded-lg border ${getUrgencyColor(data.urgency)}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4" />
                  <span className="text-sm font-medium">Days Remaining</span>
                </div>
                <div className="text-4xl font-bold">{data.rul_days}</div>
                <div className="text-xs opacity-70 mt-1">
                  {data.urgency} urgency
                </div>
              </div>

              <div className="p-4 rounded-lg bg-slate-900/40 border border-slate-800">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-4 h-4" />
                  <span className="text-sm font-medium">Predicted Date</span>
                </div>
                <div className="text-2xl font-bold">{data.predicted_failure_date}</div>
                <div className="text-xs text-slate-400 mt-1">
                  Estimated failure date
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Health Degradation Progress</span>
                <span className="font-semibold">{data.degradation_rate}% per day</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    data.rul_days <= 3 ? 'bg-red-500' :
                    data.rul_days <= 7 ? 'bg-orange-500' :
                    data.rul_days <= 14 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(100, (data.health_score / 100) * 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Critical (20%)</span>
                <span>Healthy (100%)</span>
              </div>
            </div>

            {/* Critical Factors */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="w-4 h-4 text-orange-400" />
                <span className="text-sm font-medium">Critical Factors</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.critical_factors.map((factor, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs border-slate-700">
                    {factor}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Sensor Readings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded">
                <span className="text-slate-400">Avg Vibration</span>
                <span className={`font-semibold ${data.avg_vibration > 75 ? 'text-red-400' : 'text-white'}`}>
                  {data.avg_vibration}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-900/40 rounded">
                <span className="text-slate-400">Avg Temperature</span>
                <span className={`font-semibold ${data.avg_temperature > 70 ? 'text-red-400' : 'text-white'}`}>
                  {data.avg_temperature}°C
                </span>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`p-3 rounded-lg border ${getUrgencyColor(data.urgency)}`}>
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold mb-1">Recommendation</p>
                  <p className="text-sm opacity-90">{data.recommendation}</p>
                </div>
              </div>
            </div>

            {/* Confidence Indicator */}
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Activity className="w-3 h-3" />
              <span>
                Prediction confidence: {data.confidence}% 
                {data.confidence < 50 && ' (Limited historical data - continue monitoring)'}
              </span>
            </div>
          </div>
        ))}

        {rulData.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No RUL data available</p>
            <p className="text-sm mt-1">Collecting baseline data...</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
