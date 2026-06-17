'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Database,
  AlertTriangle,
  TrendingUp,
  Activity,
  Zap,
  Shield,
  MessageSquare
} from 'lucide-react'
import { ChatInterface } from '@/components/ChatInterface'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
}

export default function DashboardPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
  }, [mounted])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-zinc-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Welcome Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tighter mb-2 sm:mb-3">
          <span className="bg-gradient-to-r from-white to-white/50 bg-clip-text text-transparent">
            Welcome Back
          </span>
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-zinc-400">
          Monitor your industrial fleet in real-time
        </p>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        variants={containerVariants}
        className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4"
      >
        <motion.div variants={itemVariants} className="group relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-emerald-500/50 transition-all overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <Activity className="w-6 h-6 text-emerald-500" />
              </div>
              <span className="text-xs text-zinc-500 font-mono uppercase">Live</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">99.9%</div>
            <div className="text-sm text-zinc-400">System Uptime</div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="group relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/50 transition-all overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <Zap className="w-6 h-6 text-blue-500" />
              </div>
              <span className="text-xs text-zinc-500 font-mono uppercase">Active</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">847</div>
            <div className="text-sm text-zinc-400">Connected Devices</div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="group relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/50 transition-all overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
                <Shield className="w-6 h-6 text-purple-500" />
              </div>
              <span className="text-xs text-zinc-500 font-mono uppercase">Secure</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">3</div>
            <div className="text-sm text-zinc-400">Active Alerts</div>
          </div>
        </motion.div>
      </motion.div>

      {/* Quick Actions Grid */}
      <motion.div variants={itemVariants}>
        <h2 className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4 text-white">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          {/* Data Card */}
          <Link href="/dashboard/data" className="group">
            <div className="relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-emerald-500/50 transition-all overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <Database className="w-6 h-6 text-emerald-500" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-zinc-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">View Data</h3>
                <p className="text-sm text-zinc-400">
                  Monitor real-time sensor telemetry and historical trends
                </p>
              </div>
            </div>
          </Link>

          {/* Anomaly Card */}
          <Link href="/dashboard/anomaly" className="group">
            <div className="relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-orange-500/50 transition-all overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20">
                    <AlertTriangle className="w-6 h-6 text-orange-500" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-zinc-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Anomaly Detection</h3>
                <p className="text-sm text-zinc-400">
                  AI-powered detection of equipment abnormalities
                </p>
              </div>
            </div>
          </Link>

          {/* Prediction Card */}
          <Link href="/dashboard/prediction" className="group">
            <div className="relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/50 transition-all overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                    <TrendingUp className="w-6 h-6 text-blue-500" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-zinc-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Future Prediction</h3>
                <p className="text-sm text-zinc-400">
                  Forecast equipment health and remaining useful life
                </p>
              </div>
            </div>
          </Link>

          {/* Status Card */}
          <Link href="/dashboard/status" className="group">
            <div className="relative p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/50 transition-all overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
                    <Activity className="w-6 h-6 text-purple-500" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-zinc-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">System Status</h3>
                <p className="text-sm text-zinc-400">
                  View overall system health and connectivity status
                </p>
              </div>
            </div>
          </Link>
        </div>
      </motion.div>

    </motion.div>
  )
}
