"use client"

import useSWR from 'swr'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import AddEquipmentDialog from '@/components/AddEquipmentDialog'
import { apiUrl } from '@/lib/api-config'

type Equipment = {
  id: string
  name: string
  type: string
  status: 'ONLINE' | 'OFFLINE' | 'MAINTENANCE'
  location?: string
}

const sampleEquipment: Equipment[] = [
  { id: 'MACHINE_002', name: 'Conveyor Belt', type: 'Conveyor', status: 'ONLINE', location: 'Line A' },
  { id: 'MACHINE_003', name: 'Industrial Motor', type: 'Motor', status: 'ONLINE', location: 'Line B' },
]

function StatusBadge({ status }: { status: Equipment['status'] }) {
  const map = {
    ONLINE: 'success',
    OFFLINE: 'destructive',
    MAINTENANCE: 'warning',
  } as const
  const label = status === 'ONLINE' ? 'Online' : status === 'OFFLINE' ? 'Offline' : 'Maintenance'
  return <Badge variant="outline" className={`border-slate-700 text-slate-300`}>{label}</Badge>
}

export default function EquipmentPage() {
  const fetcher = (url: string) => fetch(url).then(res => res.json())
  const { data, error } = useSWR<Equipment[]>(
    apiUrl('/api/equipment'),
    fetcher,
    { refreshInterval: 15000 }
  )
  const equipment = data && Array.isArray(data) ? data : sampleEquipment

  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Equipment</CardTitle>
              <CardDescription>Registered assets and current status</CardDescription>
            </div>
            <AddEquipmentDialog onSuccess={() => {}} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/60">
                <tr className="text-slate-400">
                  <th className="text-left px-3 py-2">ID</th>
                  <th className="text-left px-3 py-2">Name</th>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Location</th>
                  <th className="text-left px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {equipment.map(eq => (
                  <tr key={eq.id} className="border-t border-slate-800">
                    <td className="px-3 py-2 text-white font-medium">
                      <a href={`/dashboard/equipment/${encodeURIComponent(eq.id)}`} className="hover:underline">
                        {eq.id}
                      </a>
                    </td>
                    <td className="px-3 py-2 text-slate-300">{eq.name}</td>
                    <td className="px-3 py-2 text-slate-300">{eq.type}</td>
                    <td className="px-3 py-2 text-slate-300">{eq.location || '-'}</td>
                    <td className="px-3 py-2"><StatusBadge status={eq.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {error && (
              <p className="text-xs text-slate-500 mt-2">Showing sample data (API unavailable).</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
