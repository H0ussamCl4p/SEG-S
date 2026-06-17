'use client'

import { motion } from 'framer-motion'
import { Code2, Terminal } from 'lucide-react'

const pythonCode = `from sklearn.ensemble import IsolationForest
import numpy as np

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
    
    def train(self, X: np.ndarray):
        """Train the anomaly detection model"""
        self.model.fit(X)
        return self
    
    def predict(self, X: np.ndarray):
        """Predict anomalies (-1) or normal (1)"""
        predictions = self.model.predict(X)
        scores = self.model.score_samples(X)
        
        return {
            'anomalies': predictions == -1,
            'scores': scores,
            'confidence': np.abs(scores)
        }

# Real-time inference
detector = AnomalyDetector(contamination=0.05)
result = detector.predict(sensor_data)
`

export default function DeveloperSection() {
  return (
    <section className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-gradient-to-b from-zinc-950 to-black">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-12 md:gap-16 items-center">
          {/* Left: Marketing Copy */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
              <Code2 className="w-4 h-4 text-emerald-500" />
              <span className="text-sm text-emerald-400 font-medium">Developer First</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tighter mb-4 sm:mb-6 text-white">
              Built with
              <br />
              <span className="bg-gradient-to-r from-emerald-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
                Modern Python.
              </span>
            </h2>

            <p className="text-base sm:text-lg md:text-xl text-zinc-400 mb-6 sm:mb-8 leading-relaxed">
              FastAPI backend with async Python. Powered by scikit-learn for ML inference. 
              Deploy anywhere with Docker.
            </p>

            <div className="space-y-4">
              {[
                { label: 'FastAPI', desc: 'Async REST API with OpenAPI docs' },
                { label: 'scikit-learn', desc: 'Production-ready ML models' },
                { label: 'PostgreSQL', desc: 'Time-series optimized storage' },
                { label: 'Redis', desc: 'Real-time caching layer' },
              ].map((item, i) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2.5" />
                  <div>
                    <div className="font-semibold text-white">{item.label}</div>
                    <div className="text-sm text-zinc-500">{item.desc}</div>
                  </div>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4 }}
              className="mt-8"
            >
              <a
                href="https://github.com/H0ussamCl4p/iiot-predictive-maintenance"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 rounded-full text-sm font-medium text-white hover:bg-white/10 transition-colors"
              >
                <Terminal className="w-4 h-4" />
                View Documentation
              </a>
            </motion.div>
          </motion.div>

          {/* Right: Code Terminal */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative mt-8 lg:mt-0"
          >
            {/* Glow Effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 via-blue-500/20 to-purple-500/20 rounded-2xl sm:rounded-3xl blur-3xl opacity-50" />

            {/* Terminal Window */}
            <div className="relative rounded-xl sm:rounded-2xl overflow-hidden border border-white/10 bg-zinc-950 shadow-2xl">
              {/* Terminal Header */}
              <div className="bg-zinc-900/80 backdrop-blur-xl border-b border-white/10 px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-2">
                <div className="flex gap-1.5 sm:gap-2">
                  <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-red-500/80" />
                  <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-yellow-500/80" />
                  <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-green-500/80" />
                </div>
                <div className="flex-1 ml-2 sm:ml-4 flex items-center gap-2">
                  <Terminal className="w-3 h-3 sm:w-4 sm:h-4 text-zinc-500" />
                  <span className="text-[10px] sm:text-xs text-zinc-500 font-mono truncate">anomaly_detector.py</span>
                </div>
              </div>

              {/* Code Content */}
              <div className="p-4 sm:p-6 overflow-x-auto">
                <pre className="text-xs sm:text-sm font-mono leading-relaxed">
                  <code>
                    {pythonCode.split('\n').map((line, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.02 }}
                        className="hover:bg-white/5 px-2 -mx-2 rounded"
                      >
                        <span className="inline-block w-8 text-zinc-600 select-none">{i + 1}</span>
                        <span
                          className={
                            line.includes('def ') || line.includes('class ') || line.includes('return')
                              ? 'text-purple-400'
                              : line.includes('import ') || line.includes('from ')
                              ? 'text-pink-400'
                              : line.includes("'") || line.includes('"')
                              ? 'text-emerald-400'
                              : line.includes('#')
                              ? 'text-zinc-500'
                              : 'text-zinc-300'
                          }
                        >
                          {line || ' '}
                        </span>
                      </motion.div>
                    ))}
                  </code>
                </pre>
              </div>

              {/* Terminal Footer */}
              <div className="bg-zinc-900/50 backdrop-blur-xl border-t border-white/10 px-4 py-2 flex items-center gap-4 text-xs text-zinc-500 font-mono">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span>Python 3.10</span>
                </div>
                <div>UTF-8</div>
                <div>Ln 24, Col 8</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
