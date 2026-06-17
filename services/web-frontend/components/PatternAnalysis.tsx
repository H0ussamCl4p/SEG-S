// Anomaly Pattern Recognition Component

'use client'

import { Brain, TrendingUp, Calendar, AlertCircle, Info, Clock } from 'lucide-react'
import type { AnomalyPattern } from '@/types'

interface PatternAnalysisProps {
  patterns: AnomalyPattern[];
}

export default function PatternAnalysis({ patterns }: PatternAnalysisProps) {
  if (!patterns || !Array.isArray(patterns) || patterns.length === 0) {
    return (
      <div className="text-center py-8">
        <Brain className="w-12 h-12 text-slate-700 mx-auto mb-3 animate-pulse" />
        <p className="text-slate-500">Analyzing patterns...</p>
        <p className="text-sm text-slate-600 mt-1">Requires at least 7 days of data</p>
      </div>
    )
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-500', icon: 'text-red-500' }
      case 'MEDIUM': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-500', icon: 'text-yellow-500' }
      case 'LOW': return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-500', icon: 'text-blue-500' }
      case 'INFO': return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-500', icon: 'text-emerald-500' }
      default: return { bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-500', icon: 'text-slate-500' }
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'TIME_BASED': return <Clock className="w-5 h-5" />
      case 'CORRELATION': return <TrendingUp className="w-5 h-5" />
      case 'WEEKLY_CYCLE': return <Calendar className="w-5 h-5" />
      case 'NO_PATTERN': return <Info className="w-5 h-5" />
      default: return <Brain className="w-5 h-5" />
    }
  }

  return (
    <div className="space-y-4">
      {patterns.map((pattern, index) => {
        const colors = getSeverityColor(pattern.severity)

        return (
          <div
            key={pattern.id}
            className={`p-5 rounded-lg border ${colors.bg} ${colors.border} transition-all hover:scale-[1.01]`}
          >
            <div className="flex items-start gap-3 mb-3">
              <div className={colors.icon}>
                {getTypeIcon(pattern.type)}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold text-white">{pattern.title}</h4>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium ${colors.text}`}>
                      {pattern.confidence.toFixed(0)}% confidence
                    </span>
                    {pattern.occurrences > 0 && (
                      <span className="text-xs text-slate-500">
                        ({pattern.occurrences} occurrences)
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Confidence Bar */}
                <div className="w-full bg-slate-800 rounded-full h-1.5 mb-3 overflow-hidden">
                  <div
                    className={`h-full ${colors.icon.replace('text-', 'bg-')} transition-all duration-1000 ease-out`}
                    style={{ width: `${pattern.confidence}%` }}
                  />
                </div>

                <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                  {pattern.description}
                </p>

                {/* Recommendation */}
                <div className={`p-3 rounded-md bg-slate-900/50 border ${colors.border}`}>
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-slate-400 mb-1">Recommendation:</p>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {pattern.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Pattern Type Badge */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-700">
              <span className="text-xs text-slate-500">
                {pattern.type.replace(/_/g, ' ')}
              </span>
              <span className={`text-xs font-medium px-2 py-1 rounded ${colors.bg} ${colors.text}`}>
                {pattern.severity}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
