'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus } from 'lucide-react'

const faqs = [
  {
    q: 'How long does it take to install the solution?',
    a: 'Under one week — from the first sensor to a live, monitoring dashboard.',
  },
  {
    q: 'Is it adapted to old machines?',
    a: 'Yes. We install a small sensor box that streams data continuously to the AI — no retrofit or downtime required.',
  },
  {
    q: 'Is it adapted to modern machines?',
    a: 'Yes. We tap directly into your existing protocols (MQTT, PLC) to read live data straight from the machine.',
  },
  {
    q: 'What is the return on investment?',
    a: 'Payback is typically under 7 months, driven by avoided unplanned downtime and optimized, condition-based maintenance.',
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
