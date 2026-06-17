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
  Cpu
} from "lucide-react"

const items = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/chatbot", label: "Chatbot", icon: MessageSquare },
  { href: "/dashboard/esp", label: "Motor (ESP32)", icon: Cpu },
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
      mobile ? "space-y-1" : "p-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm"
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
              "flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium group",
              active
                ? "bg-white text-black shadow-lg"
                : "text-zinc-400 hover:text-white hover:bg-white/10"
            )}
          >
            <Icon className={cn(
              "w-5 h-5 transition-colors",
              active ? "text-emerald-600" : "text-zinc-500 group-hover:text-emerald-500"
            )} />
            <span className="text-sm">{item.label}</span>
            {active && (
              <div className="ml-auto w-2 h-2 rounded-full bg-emerald-500" />
            )}
          </Link>
        )
      })}
    </nav>
  )
}
