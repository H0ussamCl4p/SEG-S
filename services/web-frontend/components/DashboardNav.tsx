"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Database,
  AlertTriangle,
  TrendingUp,
  Wrench,
  Calendar,
  Clock,
  FileText,
  Activity,
  MessageSquare,
  Cpu,
  AudioWaveform
} from "lucide-react"

const items = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/chatbot", label: "Chatbot", icon: MessageSquare },
  { href: "/dashboard/esp", label: "Motor (ESP32)", icon: Cpu },
  { href: "/dashboard/signal", label: "Signal Analysis", icon: AudioWaveform },
  { href: "/dashboard/data", label: "Data", icon: Database },
  { href: "/dashboard/anomaly", label: "Anomaly", icon: AlertTriangle },
  { href: "/dashboard/prediction", label: "Prediction", icon: TrendingUp },
  { href: "/dashboard/equipment", label: "Equipment", icon: Wrench },
  { href: "/dashboard/maintenance", label: "Maintenance", icon: Calendar },
  { href: "/dashboard/shifts", label: "Shifts", icon: Clock },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
  { href: "/dashboard/status", label: "Status", icon: Activity },
]

interface DashboardNavProps {
  mobile?: boolean
  onNavigate?: () => void
}

export default function DashboardNav({ mobile = false, onNavigate }: DashboardNavProps) {
  const pathname = usePathname()

  return (
    <nav className={cn(
      "flex flex-col gap-1",
      mobile ? "space-y-1" : "rounded-2xl border border-border bg-background p-3 shadow-sm"
    )}>
      {items.map((item) => {
        const active = pathname === item.href
        const Icon = item.icon

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "group flex items-center gap-3 rounded-xl px-3.5 py-2.5 font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className={cn(
              "h-[18px] w-[18px] transition-colors",
              active ? "text-emerald-600" : "text-zinc-400 group-hover:text-emerald-600"
            )} />
            <span className="text-sm">{item.label}</span>
            {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400" />}
          </Link>
        )
      })}
    </nav>
  )
}
