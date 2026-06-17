"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText, Download, Calendar } from 'lucide-react'
import useSWR from 'swr'
import { apiUrl } from '@/lib/api-config'

const fetcher = (url: string) => fetch(url).then((r) => r.json())

type Report = {
  id: string
  title: string
  type: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'CUSTOM'
  date: string
  size: string
  status: 'READY' | 'GENERATING' | 'FAILED'
}

function StatusBadge({ status }: { status: Report['status'] }) {
  const variants = {
    READY: 'bg-green-500/10 text-green-500 border-green-500/30',
    GENERATING: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30',
    FAILED: 'bg-red-500/10 text-red-500 border-red-500/30',
  }
  return <Badge variant="outline" className={variants[status]}>{status}</Badge>
}

export default function ReportsPage() {
  const { data: reports = [], isLoading: reportsLoading } = useSWR<Report[]>(apiUrl('/api/reports'), fetcher, {
    refreshInterval: 30000,
  })
  const { data: compliance } = useSWR<any>(apiUrl('/api/compliance'), fetcher, {
    refreshInterval: 30000,
  })

  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <CardTitle>Reports & Analytics</CardTitle>
            <CardDescription>Download compliance and production reports</CardDescription>
          </div>
          <Button className="w-full sm:w-auto bg-emerald-500 hover:bg-emerald-600">
            Generate Report
          </Button>
        </CardHeader>
        <CardContent>
          {reportsLoading ? (
            <div className="text-center py-8 text-slate-400">Loading reports...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-900/60">
                  <tr className="text-slate-400">
                    <th className="text-left px-3 py-2">Report</th>
                    <th className="text-left px-3 py-2">Type</th>
                    <th className="text-left px-3 py-2">Date</th>
                    <th className="text-left px-3 py-2">Size</th>
                    <th className="text-left px-3 py-2">Status</th>
                    <th className="text-left px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((report: Report) => (
                    <tr key={report.id} className="border-t border-slate-800">
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-slate-500" />
                          <span className="text-white font-medium">{report.title}</span>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-slate-300">{report.type}</td>
                      <td className="px-3 py-3 text-slate-300">{report.date}</td>
                      <td className="px-3 py-3 text-slate-300">{report.size}</td>
                      <td className="px-3 py-3"><StatusBadge status={report.status} /></td>
                      <td className="px-3 py-3">
                        {report.status === 'READY' ? (
                          <Button variant="outline" size="sm" className="flex items-center gap-1">
                            <Download className="w-3 h-3" />
                            Download
                          </Button>
                        ) : (
                          <span className="text-slate-500 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Compliance</CardTitle>
            <CardDescription>ISO 9001 & Industry 4.0</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">Last Audit</span>
                <span className="text-white text-sm">{compliance?.lastAudit || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">Next Review</span>
                <span className="text-white text-sm">{compliance?.nextReview || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">Compliance Score</span>
                <span className="text-green-500 text-sm font-bold">{compliance?.complianceScore || 0}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Schedule</CardTitle>
            <CardDescription>Upcoming Reports</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-slate-500" />
                <div className="flex-1">
                  <p className="text-white">Daily Report</p>
                  <p className="text-slate-400 text-xs">Generates at 23:59 daily</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-slate-500" />
                <div className="flex-1">
                  <p className="text-white">Weekly Summary</p>
                  <p className="text-slate-400 text-xs">Every Sunday at 23:59</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
