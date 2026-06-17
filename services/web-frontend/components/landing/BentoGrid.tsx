'use client'

import { motion } from 'framer-motion'
import { Activity, Lock, Wifi, Shield, Zap, TrendingUp } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

const chartData = [
  { value: 400 },
  { value: 300 },
  { value: 600 },
  { value: 800 },
  { value: 500 },
  { value: 900 },
  { value: 700 },
]

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
      duration: 0.6,
    },
  },
}

export default function BentoGrid() {
  return (
    <section className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-zinc-950">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12 sm:mb-16"
        >
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tighter mb-4 text-white">
            Built for Scale.
            <br />
            <span className="bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
              Designed for Speed.
            </span>
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto px-4">
            Enterprise-grade features that just work. No configuration hell.
          </p>
        </motion.div>

        {/* Bento Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4"
        >
          {/* Large Card - AI Detection */}
          <motion.div
            variants={itemVariants}
            className="md:col-span-2 md:row-span-2 group relative p-6 sm:p-8 rounded-2xl sm:rounded-3xl bg-white/5 border border-white/10 hover:border-emerald-500/50 transition-all duration-500 overflow-hidden"
          >
            {/* Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6">
                <div className="p-2 sm:p-3 rounded-xl sm:rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                  <Activity className="w-6 h-6 sm:w-8 sm:h-8 text-emerald-500" />
                </div>
                <div>
                  <h3 className="text-xl sm:text-2xl md:text-3xl font-bold text-white">AI-Powered Detection</h3>
                  <p className="text-sm sm:text-base text-zinc-400">Isolation Forest Algorithm</p>
                </div>
              </div>

              <p className="text-sm sm:text-base md:text-lg text-zinc-300 mb-6 sm:mb-8 max-w-md">
                Automatically detect anomalies in real-time sensor data with machine learning. 
                No manual thresholding required.
              </p>

              {/* Animated Chart */}
              <div className="relative h-64 bg-zinc-950/50 rounded-2xl border border-white/10 p-6 overflow-hidden">
                <div className="absolute top-4 left-6 z-10">
                  <span className="text-xs text-zinc-500 font-mono">VIBRATION ANALYSIS</span>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={3}
                      dot={false}
                      animationDuration={2000}
                    />
                  </LineChart>
                </ResponsiveContainer>
                {/* Anomaly Indicator */}
                <motion.div
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 1.5, duration: 0.3 }}
                  className="absolute top-1/2 right-20 -translate-y-1/2"
                >
                  <div className="relative">
                    <div className="absolute inset-0 bg-red-500/20 rounded-full blur-xl animate-pulse" />
                    <div className="relative px-3 py-1 bg-red-500/20 border border-red-500 rounded-full text-xs text-red-400 font-bold">
                      ANOMALY
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Stats Row */}
              <div className="mt-6 grid grid-cols-3 gap-4">
                <div>
                  <div className="text-2xl font-bold text-white">99.2%</div>
                  <div className="text-xs text-zinc-500">Accuracy</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">&lt;50ms</div>
                  <div className="text-xs text-zinc-500">Latency</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">10k+</div>
                  <div className="text-xs text-zinc-500">Predictions/sec</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Real-Time MQTT Card */}
          <motion.div
            variants={itemVariants}
            className="group relative p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-blue-500/50 transition-all duration-500 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10">
              <div className="p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 mb-4 inline-block">
                <Wifi className="w-6 h-6 text-blue-500" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Real-Time MQTT</h3>
              <p className="text-zinc-400 text-sm mb-6">
                Stream data from thousands of devices with sub-second latency.
              </p>

              {/* Live Indicator */}
              <div className="flex items-center gap-2 p-3 bg-zinc-950/50 rounded-xl border border-white/10">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-3 h-3 rounded-full bg-green-500"
                />
                <span className="text-sm font-mono text-zinc-300">LIVE</span>
                <span className="ml-auto text-xs text-zinc-500">847 devices</span>
              </div>

              {/* Message Stream */}
              <div className="mt-4 space-y-2">
                {[1, 2, 3].map((i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.3, repeat: Infinity, repeatDelay: 2 }}
                    className="p-2 bg-zinc-950/30 rounded-lg border border-white/5 text-xs font-mono text-zinc-500"
                  >
                    sensors/temp/{i} → 72.{i}°C
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Secure & Scalable Card */}
          <motion.div
            variants={itemVariants}
            className="group relative p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-purple-500/50 transition-all duration-500 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10">
              <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/20 mb-4 inline-block">
                <Shield className="w-6 h-6 text-purple-500" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Secure & Scalable</h3>
              <p className="text-zinc-400 text-sm mb-6">
                Enterprise-grade security with JWT auth and role-based access control.
              </p>

              {/* Security Features */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <Lock className="w-4 h-4 text-purple-400" />
                  <span>End-to-end encryption</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span>Auto-scaling</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  <span>99.99% SLA</span>
                </div>
              </div>

              {/* Glow Shield */}
              <div className="mt-6 relative">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full blur-xl"
                />
                <div className="relative w-24 h-24 mx-auto flex items-center justify-center bg-zinc-950 rounded-full border border-purple-500/30">
                  <Shield className="w-12 h-12 text-purple-500" />
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
