'use client'

const technologies = [
  'Next.js', 'FastAPI', 'Docker', 'PostgreSQL', 'InfluxDB', 'MQTT',
  'Tailwind CSS', 'TypeScript', 'Python', 'scikit-learn', 'Azure', 'Groq',
]

export default function StackMarquee() {
  return (
    <section className="border-y border-border bg-page py-16">
      <p className="mb-10 text-center text-sm font-medium uppercase tracking-widest text-muted-foreground">
        Built on industry-standard technologies
      </p>

      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute left-0 top-0 z-10 h-full w-24 bg-linear-to-r from-page to-transparent" />
        <div className="pointer-events-none absolute right-0 top-0 z-10 h-full w-24 bg-linear-to-l from-page to-transparent" />

        <div className="flex w-max animate-scroll gap-3">
          {[...technologies, ...technologies].map((name, i) => (
            <span
              key={i}
              className="whitespace-nowrap rounded-full border border-border bg-background px-5 py-2.5 text-base font-medium text-foreground shadow-sm"
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
