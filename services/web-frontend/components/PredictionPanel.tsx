'use client'

import { useEffect, useState } from 'react'
import { Activity, TrendingUp, Clock, AlertTriangle, CheckCircle, Zap } from 'lucide-react'
import { apiUrl } from '@/lib/api-config'

interface PredictionData {
  timestamp: string
  current_state: {
    status: string
    status_emoji: string
    risk_level: string
    anomaly_score: number
    warnings: string[]
    model_loaded: boolean
  }
  future_prediction: {
    predicted_mttf: number | null
    estimated_days_until_failure: number | null
    future_risk_level: string
    future_risk_emoji?: string
    recommended_action: string
    confidence?: string
    most_critical_factor?: {
      name: string
      value: number
      importance: number
    }
    model_loaded: boolean
  }
  overall_assessment: {
    risk_level: string
    recommendation: string
    analysis: string
  }
}

export default function PredictionPanel({ equipmentId }: { equipmentId?: string }) {
  const [prediction, setPrediction] = useState<PredictionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch prediction every 5 seconds
  useEffect(() => {
    const fetchPrediction = async () => {
      try {
        // First fetch live data for the machine
        const machineId = equipmentId || 'MACHINE_002'
        const liveResponse = await fetch(apiUrl(`/api/live?machine_id=${machineId}`))
        
        if (!liveResponse.ok) {
          setError('Failed to fetch live data')
          setLoading(false)
          return
        }
        
        const liveData = await liveResponse.json()
        
        // Use live data for prediction with reasonable Age and Quantity estimates
        const response = await fetch(apiUrl('/predict'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data: {
              Humidity: liveData.humidity || 50,
              Temperature: liveData.temperature || 45,
              Age: 12,  // Default age in months
              Quantity: 40000  // Default production quantity
            },
            equipmentId: machineId
          })
        })

        if (response.ok) {
          const data = await response.json()
          setPrediction(data)
          setError(null)
        } else {
          setError('Failed to fetch prediction')
        }
      } catch (err) {
        setError('Connection error')
      } finally {
        setLoading(false)
      }
    }

    fetchPrediction()
    const interval = setInterval(fetchPrediction, 5000)

    return () => clearInterval(interval)
  }, [equipmentId])

  if (loading) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-700 rounded w-1/3"></div>
          <div className="h-4 bg-slate-700 rounded w-2/3"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error || !prediction) {
    return (
      <div className="bg-slate-800/50 border border-red-500/30 rounded-xl p-6">
        <div className="flex items-center gap-3 text-red-500">
          <AlertTriangle className="w-5 h-5" />
          <div>
            <p className="font-semibold">Prediction Service Unavailable</p>
            <p className="text-sm text-slate-400">{error || 'No data available'}</p>
          </div>
        </div>
      </div>
    )
  }

  const { current_state, future_prediction, overall_assessment } = prediction

  // Risk color mapping
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/30'
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30'
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30'
      case 'LOW': return 'text-green-500 bg-green-500/10 border-green-500/30'
      default: return 'text-slate-500 bg-slate-500/10 border-slate-500/30'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
      case 'HIGH': return <AlertTriangle className="w-5 h-5" />
      case 'MEDIUM': return <Activity className="w-5 h-5" />
      case 'LOW': return <CheckCircle className="w-5 h-5" />
      default: return <Activity className="w-5 h-5" />
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-emerald-500" />
          <h2 className="text-xl font-bold text-white">AI Predictions</h2>
        </div>
        <div className={`px-3 py-1 rounded-lg border font-semibold text-sm ${getRiskColor(overall_assessment.risk_level)}`}>
          {overall_assessment.risk_level}
        </div>
      </div>

      {/* Overall Assessment */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg ${getRiskColor(overall_assessment.risk_level)}`}>
            {getRiskIcon(overall_assessment.risk_level)}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-2">Overall Assessment</h3>
            <p className="text-slate-300 mb-3">{overall_assessment.recommendation}</p>
            <p className="text-sm text-slate-400">{overall_assessment.analysis}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Current State */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-white">Real-time Detection</h3>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Status</span>
              <span className={`px-3 py-1 rounded-lg border font-semibold text-sm ${getRiskColor(current_state.risk_level)}`}>
                {current_state.status}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Anomaly Score</span>
              <span className="text-white font-semibold">{current_state.anomaly_score}/100</span>
            </div>

            {Array.isArray(current_state.warnings) && current_state.warnings.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-semibold text-slate-300">Warnings:</p>
                {current_state.warnings.map((warning, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm text-slate-300 bg-slate-900/50 p-2 rounded">
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    <span>{warning}</span>
                  </div>
                ))}
              </div>
            )}

            {!current_state.model_loaded && (
              <p className="text-xs text-slate-500 mt-2">Model not loaded</p>
            )}
          </div>
        </div>

        {/* Future Prediction */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            <h3 className="text-lg font-semibold text-white">Future Forecast</h3>
          </div>

          {future_prediction.model_loaded ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Risk Level</span>
                <span className={`px-3 py-1 rounded-lg border font-semibold text-sm ${getRiskColor(future_prediction.future_risk_level)}`}>
                  {future_prediction.future_risk_emoji} {future_prediction.future_risk_level}
                </span>
              </div>

              {future_prediction.predicted_mttf !== null && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Predicted MTTF</span>
                    <span className="text-white font-semibold">{future_prediction.predicted_mttf.toFixed(2)} hrs</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Time to Failure</span>
                    <span className="text-white font-semibold flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      ~{future_prediction.estimated_days_until_failure?.toFixed(1)} days
                    </span>
                  </div>
                </>
              )}

              {future_prediction.most_critical_factor && (
                <div className="mt-4 p-3 bg-slate-900/50 rounded-lg">
                  <p className="text-xs text-slate-400 mb-1">Most Critical Factor</p>
                  <p className="text-sm font-semibold text-white">
                    {future_prediction.most_critical_factor.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    Importance: {future_prediction.most_critical_factor.importance.toFixed(1)}%
                  </p>
                </div>
              )}

              <div className="mt-4 pt-4 border-t border-slate-700">
                <p className="text-sm text-slate-300">{future_prediction.recommended_action}</p>
                {future_prediction.confidence && (
                  <p className="text-xs text-slate-500 mt-2">Confidence: {future_prediction.confidence}</p>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-yellow-500">
              <AlertTriangle className="w-5 h-5" />
              <div>
                <p className="font-semibold">Model Not Loaded</p>
                <p className="text-sm text-slate-400">{future_prediction.recommended_action}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
