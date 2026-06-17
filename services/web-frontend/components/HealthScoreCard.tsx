// Machine Health Score component with circular progress

'use client'

interface HealthScoreCardProps {
  score: number;
  status: string;
  daysUntilMaintenance: number;
  maintenanceUrgency: string;
}

export default function HealthScoreCard({ 
  score, 
  status, 
  daysUntilMaintenance,
  maintenanceUrgency 
}: HealthScoreCardProps) {
  // Determine colors based on score
  const getColors = () => {
    if (score >= 80) return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-500', ring: 'stroke-emerald-500' }
    if (score >= 60) return { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-500', ring: 'stroke-green-500' }
    if (score >= 40) return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-500', ring: 'stroke-yellow-500' }
    if (score >= 20) return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-500', ring: 'stroke-orange-500' }
    return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-500', ring: 'stroke-red-500' }
  }

  const colors = getColors()
  
  // Calculate circle progress
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference

  // Format maintenance text
  const getMaintenanceText = () => {
    if (maintenanceUrgency === 'immediate') {
      return '⚠️ Maintenance Required Now'
    }
    if (maintenanceUrgency === 'soon') {
      return `Maintenance in ${Math.ceil(daysUntilMaintenance)} day${Math.ceil(daysUntilMaintenance) !== 1 ? 's' : ''}`
    }
    return `Next service in ${Math.ceil(daysUntilMaintenance)} days`
  }

  return (
    <div className={`p-4 sm:p-6 lg:p-8 rounded-xl border ${colors.bg} ${colors.border} backdrop-blur-sm transition-all hover:scale-105`}>
      <h3 className="text-sm sm:text-base lg:text-lg font-semibold text-white mb-4 sm:mb-6 text-center">Machine Health</h3>
      
      {/* Circular Progress */}
      <div className="relative flex items-center justify-center mb-4 sm:mb-6">
        <svg className="transform -rotate-90 w-36 h-36 sm:w-44 sm:h-44 lg:w-48 lg:h-48" viewBox="0 0 180 180">
          {/* Background circle */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            className="text-slate-800"
          />
          {/* Progress circle */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className={`${colors.ring} transition-all duration-1000 ease-out`}
          />
        </svg>
        
        {/* Score text in center */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl sm:text-4xl lg:text-5xl font-bold ${colors.text}`}>{score}%</span>
          <span className={`text-xs sm:text-sm font-medium ${colors.text} mt-1`}>{status}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-800 rounded-full h-2 mb-4 overflow-hidden">
        <div 
          className={`h-full ${colors.ring.replace('stroke-', 'bg-')} transition-all duration-1000 ease-out`}
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Maintenance info */}
      <div className="text-center">
        <p className={`text-xs sm:text-sm font-medium ${maintenanceUrgency === 'immediate' ? 'text-red-400' : 'text-slate-400'}`}>
          {getMaintenanceText()}
        </p>
      </div>

      {/* Status indicators */}
      <div className="grid grid-cols-3 gap-2 mt-4 sm:mt-6 text-xs">
        <div className="text-center">
          <div className={`w-full h-1 rounded mb-1 ${score >= 80 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
          <span className="text-slate-500 hidden sm:inline">Excellent</span>
          <span className="text-slate-500 sm:hidden">Good</span>
        </div>
        <div className="text-center">
          <div className={`w-full h-1 rounded mb-1 ${score >= 40 && score < 80 ? 'bg-yellow-500' : 'bg-slate-700'}`} />
          <span className="text-slate-500">Fair</span>
        </div>
        <div className="text-center">
          <div className={`w-full h-1 rounded mb-1 ${score < 40 ? 'bg-red-500' : 'bg-slate-700'}`} />
          <span className="text-slate-500 hidden sm:inline">Critical</span>
          <span className="text-slate-500 sm:hidden">Bad</span>
        </div>
      </div>
    </div>
  )
}
