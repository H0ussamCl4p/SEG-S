'use client'

import { motion } from 'framer-motion'
import { MessageSquare, Sparkles, Shield, Cpu } from 'lucide-react'
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

export default function ChatbotPage() {
    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="relative flex flex-col h-[calc(100vh-8rem)] w-full"
        >
            {/* Background Atmosphere */}
            <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full -z-10 pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-5%] w-[30%] h-[30%] bg-blue-500/10 blur-[100px] rounded-full -z-10 pointer-events-none" />

            {/* Main Interface */}
            <motion.div
                variants={itemVariants}
                className="flex-1 w-full h-full relative group"
            >
                {/* Decorative border glow on hover */}
                <div className="absolute -inset-0.5 bg-gradient-to-br from-emerald-500/20 to-blue-500/20 rounded-[2rem] blur opacity-0 group-hover:opacity-100 transition duration-1000 group-hover:duration-200" />

                <div className="relative h-full w-full bg-zinc-950/40 border border-white/10 rounded-[1.5rem] overflow-hidden backdrop-blur-xl shadow-2xl">
                    <ChatInterface fullHeight />
                </div>
            </motion.div>
        </motion.div>
    )
}
