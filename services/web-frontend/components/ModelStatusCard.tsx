"use client"

import useSWR from "swr"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, BrainCircuit, Zap } from "lucide-react"
import { apiUrl } from '@/lib/api-config'

type ModelsStatus = {
  anomaly_detection_model: {
    available: boolean
    path: string
    type: string
    purpose: string
  }
  predictive_model: {
    available: boolean
    path: string
    type: string
    purpose: string
  }
}

const fetcher = (url: string) => fetch(url).then(r => r.json())

export default function ModelStatusCard() {
  const { data, error } = useSWR<ModelsStatus>(apiUrl('/models/status'), fetcher, { refreshInterval: 15000 })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-emerald-500" />
          Model Status
        </CardTitle>
        <CardDescription>Availability of anomaly and predictive models</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2">
            <Badge variant="outline">API Unreachable</Badge>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Anomaly Detection
              </span>
              <Badge variant={data?.anomaly_detection_model.available ? "default" : "outline"}>
                {data?.anomaly_detection_model.available ? "Available" : "Missing"}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 truncate">{data?.anomaly_detection_model.type}</p>
            <p className="text-xs text-slate-500 truncate">{data?.anomaly_detection_model.path}</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Predictive (MTTF)
              </span>
              <Badge variant={data?.predictive_model.available ? "default" : "outline"}>
                {data?.predictive_model.available ? "Available" : "Missing"}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 truncate">{data?.predictive_model.type}</p>
            <p className="text-xs text-slate-500 truncate">{data?.predictive_model.path}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
