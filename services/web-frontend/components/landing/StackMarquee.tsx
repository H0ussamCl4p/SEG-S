'use client'

import { motion } from 'framer-motion'

const technologies = [
  { name: 'Next.js', color: 'text-white' },
  { name: 'FastAPI', color: 'text-green-400' },
  { name: 'Docker', color: 'text-blue-400' },
  { name: 'PostgreSQL', color: 'text-blue-300' },
  { name: 'InfluxDB', color: 'text-purple-400' },
  { name: 'MQTT', color: 'text-purple-300' },
  { name: 'Tailwind CSS', color: 'text-cyan-400' },
  { name: 'TypeScript', color: 'text-blue-500' },
  { name: 'Python', color: 'text-yellow-400' },
  { name: 'scikit-learn', color: 'text-orange-400' },
  { name: 'Redis', color: 'text-red-400' },
  { name: 'Grafana', color: 'text-orange-500' },
]

export default function StackMarquee() {
  return (
    <section className="relative py-24 bg-black overflow-hidden border-y border-white/10">
      <div className="mb-12 text-center">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-sm font-mono text-zinc-500 uppercase tracking-widest"
        >
          Powered by Industry-Leading Technologies
        </motion.p>
      </div>

      {/* Scrolling Container */}
      <div className="relative">
        {/* Gradient Overlays */}
        <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-black to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-black to-transparent z-10" />

        {/* Marquee */}
        <div className="flex">
          <motion.div
            animate={{ x: [0, -1920] }}
            transition={{
              x: {
                duration: 30,
                repeat: Infinity,
                ease: "linear",
              },
            }}
            className="flex gap-16 whitespace-nowrap"
          >
            {/* First set */}
            {technologies.map((tech, i) => (
              <div
                key={`first-${i}`}
                className="flex items-center gap-3 px-6 py-3 rounded-full bg-white/5 border border-white/10"
              >
                <span className={`text-2xl font-bold ${tech.color}`}>
                  {tech.name}
                </span>
              </div>
            ))}
            {/* Duplicate set for seamless loop */}
            {technologies.map((tech, i) => (
              <div
                key={`second-${i}`}
                className="flex items-center gap-3 px-6 py-3 rounded-full bg-white/5 border border-white/10"
              >
                <span className={`text-2xl font-bold ${tech.color}`}>
                  {tech.name}
                </span>
              </div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Stats Below Marquee */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.2 }}
        className="mt-16 max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 px-6"
      >
        {[
          { label: 'GitHub Stars', value: '1.2k+' },
          { label: 'Production Deployments', value: '847' },
          { label: 'Community Members', value: '3.5k+' },
          { label: 'Countries', value: '42' },
        ].map((stat, i) => (
          <div key={i} className="text-center">
            <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
            <div className="text-sm text-zinc-500">{stat.label}</div>
          </div>
        ))}
      </motion.div>
    </section>
  )
}
