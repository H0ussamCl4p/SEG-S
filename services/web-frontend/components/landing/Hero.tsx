'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, Github, Star } from 'lucide-react'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-32 pb-20 overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent" />
      
      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-5xl mx-auto text-center"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-8"
        >
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm text-zinc-400 font-medium">Open Source • MIT License</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-4xl sm:text-5xl md:text-6xl lg:text-8xl font-bold tracking-tighter mb-6 bg-gradient-to-b from-white via-white to-white/50 bg-clip-text text-transparent leading-[1.1]"
        >
          Predictive Maintenance
          <br />
          for the Modern Factory.
        </motion.h1>

        {/* Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-base sm:text-lg md:text-xl lg:text-2xl text-zinc-400 mb-12 max-w-3xl mx-auto leading-relaxed px-4"
        >
          Stop downtime before it happens. The open-source standard for IIoT anomaly detection.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
        >
          <Link
            href="/dashboard"
            className="group px-8 py-4 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-all flex items-center gap-2 shadow-2xl shadow-white/20"
          >
            Enter Console
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="https://github.com/H0ussamCl4p/iiot-predictive-maintenance"
            target="_blank"
            className="group px-8 py-4 bg-zinc-900 text-white font-semibold rounded-full hover:bg-zinc-800 transition-all border border-zinc-700 flex items-center gap-2"
          >
            <Github className="w-5 h-5" />
            View on GitHub
            <div className="flex items-center gap-1 ml-2 px-2 py-1 bg-zinc-800 rounded-full text-xs">
              <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
              <span>42</span>
            </div>
          </Link>
        </motion.div>
      </motion.div>

      {/* 3D Dashboard Mockup */}
      <motion.div
        initial={{ opacity: 0, y: 40, rotateX: 20 }}
        animate={{ opacity: 1, y: 0, rotateX: 8 }}
        transition={{ delay: 0.6, duration: 1 }}
        className="relative z-10 w-full max-w-6xl mx-auto perspective-1000 px-4"
      >
        <div className="relative rounded-2xl md:rounded-3xl overflow-hidden border border-white/10 shadow-2xl shadow-emerald-500/20 bg-zinc-900/50 backdrop-blur-xl transform-gpu" style={{ transform: 'rotateX(8deg) rotateY(0deg)' }}>
          {/* Glow Effect */}
          <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 via-blue-500/20 to-purple-500/20 rounded-2xl md:rounded-3xl blur-2xl opacity-50" />
          
          {/* Browser Chrome */}
          <div className="relative bg-zinc-950/80 backdrop-blur-xl border-b border-white/10 px-3 md:px-4 py-2 md:py-3 flex items-center gap-2">
            <div className="flex gap-1.5 md:gap-2">
              <div className="w-2 h-2 md:w-3 md:h-3 rounded-full bg-red-500/80" />
              <div className="w-2 h-2 md:w-3 md:h-3 rounded-full bg-yellow-500/80" />
              <div className="w-2 h-2 md:w-3 md:h-3 rounded-full bg-green-500/80" />
            </div>
            <div className="flex-1 ml-2 md:ml-4">
              <div className="px-2 md:px-4 py-1 md:py-1.5 bg-white/5 rounded-lg text-[10px] md:text-xs text-zinc-500 font-mono truncate">
                https://smart-energy-guardien.io/dashboard
              </div>
            </div>
          </div>

          {/* Dashboard Preview */}
          <div className="relative bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 p-4 md:p-6 lg:p-8">
            <div className="grid grid-cols-3 gap-2 md:gap-4">
              {/* Stat Cards */}
              <div className="p-6 bg-white/5 rounded-2xl border border-white/10">
                <div className="text-sm text-zinc-500 mb-2">Uptime</div>
                <div className="text-4xl font-bold text-emerald-500">99.9%</div>
              </div>
              <div className="p-6 bg-white/5 rounded-2xl border border-white/10">
                <div className="text-sm text-zinc-500 mb-2">Devices</div>
                <div className="text-4xl font-bold text-blue-500">847</div>
              </div>
              <div className="p-6 bg-white/5 rounded-2xl border border-white/10">
                <div className="text-sm text-zinc-500 mb-2">Alerts</div>
                <div className="text-4xl font-bold text-orange-500">3</div>
              </div>
            </div>

            {/* Chart Placeholder */}
            <div className="mt-3 md:mt-6 h-40 md:h-52 lg:h-64 bg-white/5 rounded-xl md:rounded-2xl border border-white/10 p-3 md:p-6 relative overflow-hidden">
              <div className="absolute inset-0 flex items-end justify-around p-3 md:p-6">
                {[40, 60, 55, 75, 65, 85, 70, 90].map((height, i) => (
                  <motion.div
                    key={i}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: 1 }}
                    transition={{ delay: 0.8 + i * 0.1 }}
                    className="w-6 md:w-10 lg:w-12 bg-gradient-to-t from-emerald-500/50 to-emerald-500 rounded-t-md lg:rounded-t-lg origin-bottom"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  )
}
