'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { BarChart3, TrendingUp, DollarSign } from 'lucide-react'
import { apiUrl } from '@/lib/api-config'

interface ParetoData {
  factor: string
  count: number
  percentage: number
  cumulative: number
  cost_estimate?: number
}

interface ParetoChartProps {
  machineId?: string
  type?: 'anomalies' | 'maintenance'
  title?: string
  showCost?: boolean
}

export default function ParetoChart({ 
  machineId, 
  type = 'anomalies',
  title,
  showCost = false 
}: ParetoChartProps) {
  const [data, setData] = useState<ParetoData[]>([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState<string>('30')
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        let url = apiUrl(`/api/pareto/${type}?days=${timeframe}`)
        if (machineId && type === 'anomalies') {
          url += `&machine_id=${machineId}`
        }
        
        const response = await fetch(url)
        if (response.ok) {
          const paretoData = await response.json()
          setData(paretoData)
        }
      } catch (error) {
        console.error('Failed to fetch Pareto data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    
    return () => clearInterval(interval)
  }, [machineId, type, timeframe])

  const maxCount = Math.max(...data.map(d => d.count), 1)
  const defaultTitle = type === 'anomalies' 
    ? `Anomaly Cause Analysis${machineId ? ` - ${machineId}` : ''}`
    : 'Maintenance Task Distribution'
  
  const totalCost = data.reduce((sum, d) => sum + (d.cost_estimate || 0), 0)

  return (
    <Card className="border-slate-800">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <BarChart3 className="w-5 h-5 text-purple-500 shrink-0" />
              <span className="break-words">{title || defaultTitle}</span>
            </CardTitle>
            <CardDescription className="mt-1 text-xs sm:text-sm">
              Pareto Analysis: 80% of issues come from 20% of causes
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-slate-400">Timeframe:</label>
            <Select value={timeframe} onValueChange={setTimeframe}>
              <SelectTrigger className="w-[120px] h-8 bg-slate-900/60 border-slate-800 text-white text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="7" className="text-white text-xs">Last 7 days</SelectItem>
                <SelectItem value="30" className="text-white text-xs">Last 30 days</SelectItem>
                <SelectItem value="90" className="text-white text-xs">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : data.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-slate-500">
            No data available for the selected timeframe
          </div>
        ) : (
          <div className="space-y-4">
            {/* Cost Summary for Maintenance */}
            {showCost && totalCost > 0 && (
              <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                <DollarSign className="w-5 h-5 text-green-400" />
                <div>
                  <p className="text-sm font-semibold text-green-400">Total Estimated Cost</p>
                  <p className="text-lg font-bold text-white">${totalCost.toLocaleString()}</p>
                </div>
              </div>
            )}

            {/* Chart */}
            <div className="overflow-x-auto pb-4">
              <div className="min-w-[600px] relative h-80 flex items-end justify-between gap-2 border-b-2 border-l-2 border-r-2 border-slate-700 p-4 bg-slate-900/20 mx-12">
                {/* 80% Reference Line - Horizontal */}
                <div className="absolute left-0 right-0 border-t-2 border-dashed border-red-500/60 pointer-events-none" 
                     style={{ bottom: 'calc(80% + 1rem)' }}>
                  <span className="absolute -right-2 -top-3 text-xs font-bold text-red-400 bg-slate-900 px-1">80%</span>
                </div>

                {data.map((item, idx) => {
                  const barHeight = (item.count / maxCount) * 100
                  const linePoint = item.cumulative
                  const isVital = item.cumulative <= 80 // Part of the "vital 20%"
                  
                  return (
                    <div key={idx} className="flex-1 relative group">
                      {/* Bar */}
                      <div className="relative h-full flex flex-col justify-end items-center">
                        {/* Percentage label on top */}
                        <div className="absolute -top-8 text-xs font-semibold text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity">
                          {item.percentage}%
                        </div>
                        
                        {/* Count label */}
                        <div className="absolute -top-14 text-xs font-bold text-white bg-slate-800 px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          {item.count}
                        </div>

                        {/* Bar - Color coded: Red for vital 20%, Blue for trivial 80% */}
                        <div
                          className={`w-full rounded-t transition-all cursor-pointer ${
                            isVital 
                              ? 'bg-linear-to-t from-red-600 to-red-400 hover:from-red-500 hover:to-red-300' 
                              : 'bg-linear-to-t from-blue-600 to-blue-400 hover:from-blue-500 hover:to-blue-300'
                          }`}
                          style={{ height: `${barHeight}%` }}
                          title={`${item.factor}: ${item.count} occurrences (${item.percentage}%)${item.cost_estimate ? `\nCost: $${item.cost_estimate.toLocaleString()}` : ''}\nCumulative: ${item.cumulative}%`}
                        />
                        
                        {/* Cumulative percentage point */}
                        <div className="absolute -right-1 w-3 h-3 bg-orange-500 rounded-full border-2 border-slate-900 shadow-lg" 
                             style={{ bottom: `${linePoint}%` }}
                             title={`Cumulative: ${item.cumulative}%`} 
                        />
                      </div>
                    </div>
                  )
                })}
                
                {/* Cumulative curve (orange line) */}
                <svg className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%' }}>
                  <polyline
                    points={data.map((item, idx) => {
                      const x = ((idx + 0.5) / data.length) * 100
                      const y = 100 - item.cumulative
                      return `${x}%,${y}%`
                    }).join(' ')}
                    fill="none"
                    stroke="rgb(249, 115, 22)"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                {/* Left Y-axis labels (Bar counts) */}
                <div className="absolute -left-12 inset-y-0 flex flex-col justify-between text-xs text-slate-500 pr-2">
                  <span className="text-right">{maxCount}</span>
                  <span className="text-right">{Math.round(maxCount * 0.75)}</span>
                  <span className="text-right">{Math.round(maxCount * 0.5)}</span>
                  <span className="text-right">{Math.round(maxCount * 0.25)}</span>
                  <span className="text-right">0</span>
                </div>

                {/* Right Y-axis labels (Cumulative %) */}
                <div className="absolute -right-12 inset-y-0 flex flex-col justify-between text-xs text-orange-400 pl-2">
                  <span>100%</span>
                  <span>75%</span>
                  <span>50%</span>
                  <span>25%</span>
                  <span>0%</span>
                </div>
              </div>
            </div>

            {/* Legend with Color-Coded Categories */}
            <div className="space-y-3">
              {data.map((item, idx) => {
                const isVital = item.cumulative <= 80
                return (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-sm gap-2 p-2 bg-slate-900/30 rounded-lg">
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className={`w-3 h-3 rounded shrink-0 ${isVital ? 'bg-red-500' : 'bg-blue-500'}`} />
                      <span className="text-slate-300 font-medium">{item.factor}</span>
                      {isVital && (
                        <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 border border-red-500/30 rounded">
                          VITAL 20%
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 sm:gap-4 flex-wrap text-xs sm:text-sm pl-5 sm:pl-0">
                      <span className="text-slate-400">{item.count} occurrences</span>
                      <span className="text-slate-400">({item.percentage}%)</span>
                      {item.cost_estimate && (
                        <span className="text-green-400 font-semibold">${item.cost_estimate.toLocaleString()}</span>
                      )}
                      <span className="text-orange-400 font-semibold flex items-center gap-1">
                        <span className="text-xs text-slate-500">Σ</span>{item.cumulative}%
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Pareto Principle Explanation - Enhanced */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* 80/20 Rule Summary */}
              <div className="p-4 bg-linear-to-br from-red-500/10 to-purple-500/10 border border-red-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <TrendingUp className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-bold text-red-300 mb-1">
                      Pareto Principle (80/20 Rule)
                    </p>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      <span className="font-semibold text-red-400">
                        {data.filter(d => d.cumulative <= 80).length} cause{data.filter(d => d.cumulative <= 80).length !== 1 ? 's' : ''}
                      </span>
                      {' '}(~{Math.round((data.filter(d => d.cumulative <= 80).length / data.length) * 100)}% of causes) generate{' '}
                      <span className="font-semibold text-red-400">~80%</span> of all {type === 'anomalies' ? 'anomalies' : 'maintenance issues'}.
                    </p>
                    <p className="text-xs text-red-300/60 mt-2 italic">
                      → These are the <strong>"vital few"</strong> that require immediate attention.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Recommendation */}
              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-bold text-blue-300 mb-1">
                      Recommended Action
                    </p>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      Prioritize resources on the <span className="text-red-400 font-semibold">red bars</span> (vital causes) for maximum efficiency.
                    </p>
                    <p className="text-xs text-blue-300/70 mt-2">
                      <span className="font-semibold">Impact:</span> Solving these {data.filter(d => d.cumulative <= 80).length} root causes will eliminate 80% of problems with minimal effort.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Chart Legend Key */}
            <div className="mt-3 flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500 rounded" />
                <span className="text-slate-400">Vital Few (≤80%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded" />
                <span className="text-slate-400">Trivial Many ({'>'}80%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-1 bg-orange-500" />
                <span className="text-slate-400">Cumulative %</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-red-500 border-t-2 border-dashed" />
                <span className="text-slate-400">80% Threshold</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
