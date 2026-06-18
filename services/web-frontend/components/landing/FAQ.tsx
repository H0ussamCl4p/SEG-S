'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus } from 'lucide-react'

const faqs = [
  {
    q: 'What hardware do I need?',
    a: 'An ESP32 (or any PLC) publishing sensor data over MQTT — thermocouple, vibration, temperature and humidity. No hardware on hand? The built-in simulator streams realistic telemetry so you can explore everything immediately.',
  },
  {
    q: 'How does the anomaly detection work?',
    a: 'Isolation-Forest models score every reading in real time. On top of that, vibration windows run through FFT and envelope analysis to detect bearing characteristic frequencies (BPFO/BPFI) — catching incipient faults before they escalate.',
  },
  {
    q: 'Can the AI assistant use my own equipment manuals?',
    a: 'Yes. Upload your PDFs and the retrieval-augmented chatbot answers strictly from them — diagnoses, procedures and safety notes grounded in your documentation.',
  },
  {
    q: 'Where does it run and what does it cost?',
    a: 'It runs as containerised microservices on Azure Container Apps with managed TLS. The chatbot uses a pay-as-you-go, OpenAI-compatible LLM API, so you only pay for what you use.',
  },
  {
    q: 'Is it open source?',
    a: 'Yes — the whole stack is MIT-licensed. Self-host it, extend it, or deploy it to your own cloud.',
  },
]

function Item({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-border">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-4 py-5 text-left"
      >
        <span className="text-base font-medium text-foreground sm:text-lg">{q}</span>
        <Plus
          className={`h-5 w-5 shrink-0 text-muted-foreground transition-transform duration-300 ${open ? 'rotate-45' : ''}`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <p className="pb-5 pr-8 text-sm leading-relaxed text-muted-foreground sm:text-base">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function FAQ() {
  return (
    <section className="bg-background py-24 sm:py-32">
      <div className="mx-auto max-w-3xl px-6">
        <div className="text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-emerald-600">FAQ</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Frequently asked questions
          </h2>
        </div>
        <div className="mt-12">
          {faqs.map((f) => (
            <Item key={f.q} {...f} />
          ))}
        </div>
      </div>
    </section>
  )
}
