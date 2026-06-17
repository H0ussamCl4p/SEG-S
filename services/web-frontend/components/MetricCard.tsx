// Reusable metric display component
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  status?: 'normal' | 'warning' | 'danger';
  trend?: number;
  icon?: React.ReactNode;
}

export default function MetricCard({ 
  title, 
  value, 
  unit, 
  status = 'normal',
  trend,
  icon 
}: MetricCardProps) {
  const statusStyles = {
    normal: 'border-emerald-500/30',
    warning: 'border-yellow-500/30',
    danger: 'border-red-500/30'
  }

  const trendColor = trend && trend > 0 ? 'text-red-500' : 'text-emerald-500'

  return (
    <Card className={`transition-all hover:scale-[1.01] ${statusStyles[status]}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-400">{title}</CardTitle>
        {icon && <div className="text-slate-500">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline space-x-2">
          <span className="text-4xl font-bold text-white">{value.toFixed(2)}</span>
          <span className="text-lg text-slate-500">{unit}</span>
        </div>
        {trend !== undefined && (
          <div className={`mt-2 text-sm ${trendColor}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}% from average
          </div>
        )}
      </CardContent>
    </Card>
  )
}
