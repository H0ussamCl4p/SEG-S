import Link from 'next/link'
import { Activity } from 'lucide-react'
import Hero from '@/components/landing/Hero'
import BentoGrid from '@/components/landing/BentoGrid'
import DeveloperSection from '@/components/landing/DeveloperSection'
import StackMarquee from '@/components/landing/StackMarquee'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white selection:bg-emerald-500/30">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-black/50 backdrop-blur-xl">
        <div className="container mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-500" />
            <span className="text-base sm:text-lg font-bold tracking-tight">Smart Energy Guardien</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <Link
              href="/dashboard"
              className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-black bg-white rounded-full hover:bg-zinc-200 transition-colors"
            >
              Try Now
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <Hero />
      <BentoGrid />
      <DeveloperSection />
      <StackMarquee />

      {/* Final CTA */}
      <section className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-black">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tighter mb-4 sm:mb-6 text-white">
            Ready to prevent downtime?
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-zinc-400 mb-8 sm:mb-12 px-4">
            Join hundreds of factories already using Smart Energy Guardien.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-white text-black font-semibold rounded-full hover:bg-zinc-200 transition-all shadow-2xl shadow-white/20 text-center"
            >
              Let's Get Started
            </Link>
            <Link
              href="https://github.com/H0ussamCl4p/iiot-predictive-maintenance"
              target="_blank"
              className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-zinc-900 text-white font-semibold rounded-full hover:bg-zinc-800 transition-all border border-zinc-700 text-center"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
