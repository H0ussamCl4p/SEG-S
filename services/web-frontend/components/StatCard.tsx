// Statistics card component for dashboard metrics

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export default function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon,
  trend,
  variant = 'default'
}: StatCardProps) {
  const variantStyles = {
    default: 'bg-slate-900/50 border-slate-700',
    success: 'bg-emerald-500/10 border-emerald-500/30',
    warning: 'bg-yellow-500/10 border-yellow-500/30',
    danger: 'bg-red-500/10 border-red-500/30'
  }

  const variantTextColors = {
    default: 'text-slate-400',
    success: 'text-emerald-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400'
  }

  return (
    <div className={`p-6 rounded-xl border backdrop-blur-sm transition-all hover:scale-105 ${variantStyles[variant]}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className={`text-sm font-medium ${variantTextColors[variant]} mb-1`}>
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{value}</span>
            {trend && (
              <span className={`text-sm font-medium ${trend.isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className={`p-2 rounded-lg ${variant === 'default' ? 'bg-slate-800' : ''}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
