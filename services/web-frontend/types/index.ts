// TypeScript type definitions for the application

export interface LiveData {
  vibration: number;
  temperature: number;
  score: number;
  status: 'NORMAL' | 'WARNING' | 'ANOMALY';
  timestamp: string;
  health: HealthScore;
}

export interface HealthScore {
  score: number;
  status: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  color: string;
  days_until_maintenance: number;
  maintenance_urgency: 'immediate' | 'soon' | 'scheduled';
}

export interface HistoricalData {
  timestamp: string;
  vibration: number;
  temperature: number;
  score: number;
  status: string;
}

export interface Statistics {
  vibration: {
    average: number;
    max: number;
  };
  temperature: {
    average: number;
    max: number;
  };
  ai_score: {
    average: number;
    min: number;
  };
  uptime_percentage: number;
  total_readings: number;
  anomalies_today: number;
  warnings_today: number;
}

export interface Alert {
  timestamp: string;
  severity: 'ANOMALY' | 'WARNING';
  color: 'red' | 'yellow';
  message: string;
  vibration: number;
  temperature: number;
  score: number;
}

export interface WorkOrder {
  id: string;
  machine_id: string;
  title: string;
  description: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'IN_PROGRESS' | 'SCHEDULED' | 'COMPLETED';
  assigned_to: string;
  created_at: string;
  due_date: string;
  completed_at?: string;
  estimated_hours: number;
  actual_hours?: number;
  category: string;
}

export interface AnomalyPattern {
  id: string;
  type: 'TIME_BASED' | 'CORRELATION' | 'WEEKLY_CYCLE' | 'NO_PATTERN';
  title: string;
  description: string;
  confidence: number;
  occurrences: number;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  recommendation: string;
  detected_at: string;
}
