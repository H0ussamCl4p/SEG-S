"use client"

import { useState } from 'react'
import useSWR, { mutate } from 'swr'
import LiveChart from '@/components/LiveChart'
import HealthScoreCard from '@/components/HealthScoreCard'
import AlertTimeline from '@/components/AlertTimeline'
import ParetoChart from '@/components/ParetoChart'
import { Activity, AlertTriangle, Wrench } from 'lucide-react'
import type { LiveData, HistoricalData, Alert } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export default function AnomalyPage() {
  const [machineId, setMachineId] = useState<string>('MACHINE_002')
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false)
  const [taskTitle, setTaskTitle] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [taskDueDate, setTaskDueDate] = useState('')
  const [taskPriority, setTaskPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM')
  const [isCreating, setIsCreating] = useState(false)
  
  const { data: machines } = useSWR<any[]>(apiUrl('/api/machines'), fetcher, { refreshInterval: 10000 })
  const { data: liveData } = useSWR<LiveData>(
    apiUrl(`/api/live?machine_id=${machineId}`),
    fetcher,
    { refreshInterval: 1000 }
  )
  const { data: historyData } = useSWR<HistoricalData[]>(
    apiUrl(`/api/history?limit=50&machine_id=${machineId}`),
    fetcher,
    { refreshInterval: 5000 }
  )
  const { data: alertsData } = useSWR<Alert[]>(
    apiUrl('/api/alerts?limit=50'),
    fetcher,
    { refreshInterval: 15000 }
  )

  const handleTakeAction = () => {
    if (liveData && liveData.status === 'ANOMALY') {
      const anomalyId = `A-${new Date().toISOString().split('T')[0]}-001`
      const equipId = machineId
      
      // Pre-fill task form based on anomaly data
      setTaskTitle(`Investigate ${liveData.status} on ${equipId}`)
      setTaskDescription(`AI detected anomaly:\n- Vibration: ${liveData.vibration}\n- Temperature: ${liveData.temperature}\n- Health Score: ${liveData.health?.score}\n\nImmediate investigation required.`)
      setTaskDueDate(new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]) // 3 days from now
      setTaskPriority(liveData.health?.score < 40 ? 'HIGH' : 'MEDIUM')
      setIsCreateTaskOpen(true)
    }
  }

  const handleCreateTask = async () => {
    setIsCreating(true)
    try {
      const anomalyId = `A-${new Date().toISOString().split('T')[0]}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`
      const equipId = machineId
      
      const aiCause = liveData ? 
        `Vibration: ${liveData.vibration}, Temperature: ${liveData.temperature}, Health Score: ${liveData.health?.score}. Status: ${liveData.status}` :
        'Anomaly detected by AI system'
      
      const response = await fetch(apiUrl('/api/maintenance/tasks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          equipmentId: equipId,
          title: taskTitle,
          description: taskDescription,
          dueDate: taskDueDate,
          priority: taskPriority,
          anomalyId: anomalyId,
          aiDetectedCause: aiCause,
        }),
      })
      
      if (response.ok) {
        await mutate(apiUrl('/api/maintenance/tasks'))
        setIsCreateTaskOpen(false)
        // Reset form
        setTaskTitle('')
        setTaskDescription('')
        setTaskDueDate('')
        setTaskPriority('MEDIUM')
      }
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const isAnomalyDetected = liveData && (liveData.status === 'ANOMALY' || liveData.status === 'WARNING')

  return (
    <div className="space-y-6">
      {/* Machine Selector & Action Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full sm:w-auto">
          <label className="text-muted-foreground text-sm whitespace-nowrap">Machine:</label>
          <Select value={machineId} onValueChange={setMachineId}>
            <SelectTrigger className="w-full sm:w-[280px] bg-background border-border text-foreground">
              <SelectValue placeholder="Select Machine" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border">
              {(machines || [
                { machine_id: 'MACHINE_002', name: 'Conveyor Belt' },
                { machine_id: 'MACHINE_003', name: 'Industrial Motor' }
              ]).map((machine) => (
                <SelectItem key={machine.machine_id} value={machine.machine_id} className="text-foreground hover:bg-muted">
                  {machine.machine_id} - {machine.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {isAnomalyDetected && (
          <Button
            onClick={handleTakeAction}
            className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700 text-foreground flex items-center justify-center gap-2"
          >
            <Wrench className="w-4 h-4" />
            Take Action
            <AlertTriangle className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Alert Banner for Anomalies */}
      {isAnomalyDetected && (
        <Card className="border-orange-500/50 bg-orange-500/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-orange-600 shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-orange-600">Anomaly Detected!</h3>
                <p className="text-muted-foreground mt-1">
                  The AI system has detected abnormal behavior. Click "Take Action" to create a maintenance task.
                </p>
                <div className="mt-2 text-sm text-muted-foreground">
                  <div>Health Score: <span className="text-foreground font-medium">{liveData.health?.score}%</span></div>
                  <div>Status: <span className="text-orange-600 font-medium">{liveData.status}</span></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pareto Analysis - Machine-Specific Anomaly Causes */}
      <ParetoChart 
        machineId={machineId}
        type="anomalies"
        title={`Anomaly Root Causes - ${machineId}`}
        showCost={false}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          {liveData?.health ? (
            <HealthScoreCard
              score={liveData.health.score}
              status={liveData.health.status}
              daysUntilMaintenance={liveData.health.days_until_maintenance}
              maintenanceUrgency={liveData.health.maintenance_urgency}
            />
          ) : (
            <Card>
              <CardContent className="p-8 h-full flex items-center justify-center">
                <div className="text-center">
                  <Activity className="w-12 h-12 text-muted-foreground mx-auto mb-3 animate-pulse" />
                  <p className="text-muted-foreground">Loading health data...</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base sm:text-lg">AI Health Score Trend</CardTitle>
              <CardDescription>Last 50 readings</CardDescription>
            </div>
            <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full w-fit shrink-0">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-emerald-500 font-medium">LIVE</span>
            </div>
          </CardHeader>
          <CardContent className="h-64 sm:h-80 min-h-64">
            {historyData && historyData.length > 0 ? (
              <LiveChart data={historyData} />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">Waiting for data...</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Last 50 alerts</CardDescription>
        </CardHeader>
        <CardContent>
          <AlertTimeline alerts={alertsData || []} />
        </CardContent>
      </Card>

      {/* Create Maintenance Task Dialog */}
      <Dialog open={isCreateTaskOpen} onOpenChange={setIsCreateTaskOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Maintenance Task from Anomaly</DialogTitle>
            <DialogDescription>
              Create a maintenance task to address the detected anomaly
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Task Title
              </label>
              <Input
                value={taskTitle}
                onChange={(e) => setTaskTitle(e.target.value)}
                placeholder="Enter task title..."
                className="bg-background border-border text-foreground"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Description
              </label>
              <Textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Enter detailed description..."
                className="min-h-[120px] bg-background border-border text-foreground"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">
                  Due Date
                </label>
                <Input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  className="bg-background border-border text-foreground"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">
                  Priority
                </label>
                <Select value={taskPriority} onValueChange={(v) => setTaskPriority(v as any)}>
                  <SelectTrigger className="bg-background border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background border-border">
                    <SelectItem value="LOW" className="text-foreground">Low</SelectItem>
                    <SelectItem value="MEDIUM" className="text-foreground">Medium</SelectItem>
                    <SelectItem value="HIGH" className="text-foreground">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {liveData && (
              <div className="p-3 bg-background rounded-md border border-border">
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Current Sensor Readings:</h4>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Vibration:</span>
                    <span className="text-foreground ml-2">{liveData.vibration}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Temperature:</span>
                    <span className="text-foreground ml-2">{liveData.temperature}°C</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Health:</span>
                    <span className="text-foreground ml-2">{liveData.health?.score}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateTaskOpen(false)}
              className="bg-muted hover:bg-muted border-border"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateTask}
              disabled={isCreating || !taskTitle || !taskDescription || !taskDueDate}
              className="bg-orange-600 hover:bg-orange-700"
            >
              {isCreating ? 'Creating...' : 'Create Task'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
