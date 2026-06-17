import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Bot, User, Loader2, Sparkles, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChatInterfaceProps {
    fullHeight?: boolean;
}

function formatAgentMessage(content: string) {
    let formatted = content;

    // Si le message est un gros bloc de texte brut, on le restructure
    if ((formatted.match(/\n/g) || []).length < 2) {
        // Ajoute un double saut de ligne avant les numéros (ex: " 1. ", " 2. ")
        formatted = formatted.replace(/ (\d+\.) /g, '\n\n$1 ');
        // Transforme les tirets en vraies puces avec saut de ligne
        formatted = formatted.replace(/ - /g, '\n  • ');
    }

    return (
        <div className="space-y-1.5">
            {formatted.split('\n').map((line, i) => {
                const trimmed = line.trim();
                // Lignes vides
                if (!trimmed) return <div key={i} className="h-1" />;

                // Titre numéroté
                const isHeading = /^\d+\./.test(trimmed);
                // Élément de liste
                const isBullet = trimmed.startsWith('•') || trimmed.startsWith('-');

                return (
                    <div
                        key={i}
                        className={cn(
                            "leading-relaxed",
                            isHeading && "font-bold text-emerald-300 mt-4 mb-1 first:mt-0 tracking-wide",
                            isBullet && "pl-4 text-zinc-300 relative before:content-[''] before:absolute before:left-1.5 before:top-2.5 before:w-1 before:h-1 before:bg-emerald-500/50 before:rounded-full",
                            !isHeading && !isBullet && "text-zinc-200"
                        )}
                    >
                        {isBullet ? trimmed.substring(1).trim() : line}
                    </div>
                );
            })}
        </div>
    );
}

export function ChatInterface({ fullHeight = false }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Initial load from localStorage
    useEffect(() => {
        const savedMessages = localStorage.getItem('chat_history');
        if (savedMessages) {
            try {
                setMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error("Failed to parse chat history", e);
                setMessages([{ role: 'assistant', content: 'Hello! I am your AI maintenance assistant. How can I help you today?' }]);
            }
        } else {
            setMessages([{ role: 'assistant', content: 'Hello! I am your AI maintenance assistant. How can I help you today?' }]);
        }
    }, []);

    // Save to localStorage whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('chat_history', JSON.stringify(messages));
        }
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const clearChat = () => {
        if (confirm("Are you sure you want to clear the chat history?")) {
            const initial = [{ role: 'assistant' as const, content: 'Hello! I am your AI maintenance assistant. How can I help you today?' }];
            setMessages(initial);
            localStorage.setItem('chat_history', JSON.stringify(initial));
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }, { role: 'assistant', content: '' }]);
        setIsLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok || !response.body) throw new Error('Failed to send message');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let acc = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                acc += decoder.decode(value, { stream: true });
                setMessages(prev => {
                    const next = [...prev];
                    next[next.length - 1] = { role: 'assistant', content: acc };
                    return next;
                });
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => {
                const next = [...prev];
                // Replace the empty placeholder with the error.
                next[next.length - 1] = { role: 'system', content: 'Error: Failed to communicate with AI service.' };
                return next;
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (file.type !== 'application/pdf') {
            alert("Please select a PDF file.");
            return;
        }

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        setMessages(prev => [...prev, { role: 'system', content: `Uploading ${file.name}...` }]);

        try {
            const response = await fetch(`${API_URL}/api/chat/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'system', content: `✓ ${data.message}` }]);
        } catch (error) {
            console.error(error);
            const outputError = error instanceof Error ? error.message : "Unknown error";
            setMessages(prev => [...prev, { role: 'system', content: `✗ Upload failed: ${outputError}` }]);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    return (
        <Card className={cn(
            "flex flex-col w-full mx-auto shadow-2xl border-white/10 bg-zinc-950/50 backdrop-blur-3xl relative overflow-hidden",
            fullHeight ? "h-full max-w-none" : "h-[700px] max-w-xl"
        )}>
            {/* Background Decorative Glow */}
            <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-emerald-500/5 blur-[100px] -z-10 pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-blue-500/5 blur-[100px] -z-10 pointer-events-none" />

            <CardHeader className="border-b border-white/5 bg-black/20 px-6 py-4 flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                    <div className="relative">
                        <div className="absolute inset-0 bg-emerald-500/20 blur-lg rounded-full" />
                        <Bot className="w-6 h-6 text-emerald-500 relative z-10" />
                    </div>
                    <div className="flex flex-col">
                        <span className="bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                            AI Engine Assistant
                        </span>
                        <div className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[10px] uppercase tracking-wider text-emerald-500/80 font-mono font-bold">
                                Systems Online
                            </span>
                        </div>
                    </div>
                </CardTitle>
            </CardHeader>

            <CardContent className="flex-1 p-0 overflow-hidden flex flex-col relative">
                <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
                    <AnimatePresence initial={false}>
                        {messages.map((msg, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.2 }}
                                className={cn(
                                    "flex items-start gap-4",
                                    msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                                )}
                            >
                                {/* Avatar */}
                                <div className={cn(
                                    "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-lg border",
                                    msg.role === 'assistant'
                                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                                        : msg.role === 'user'
                                            ? "bg-zinc-800 border-white/10 text-zinc-300"
                                            : "bg-zinc-900 border-white/5 text-zinc-500"
                                )}>
                                    {msg.role === 'assistant' ? <Sparkles className="w-5 h-5" /> : <User className="w-5 h-5" />}
                                </div>

                                {/* Bubble */}
                                <div className={cn(
                                    "relative max-w-[80%] group",
                                    msg.role === 'user' ? "items-end text-right" : "items-start"
                                )}>
                                    <div className={cn(
                                        "rounded-2xl px-5 py-4 text-sm shadow-xl border transition-all",
                                        msg.role === 'user'
                                            ? "bg-gradient-to-br from-emerald-600 to-teal-700 border-emerald-500/30 text-white rounded-tr-none hover:shadow-emerald-500/10 whitespace-pre-wrap"
                                            : msg.role === 'system'
                                                ? "bg-zinc-900/80 border-red-500/20 text-red-400 italic font-mono text-xs rounded-tl-none whitespace-pre-wrap"
                                                : "bg-white/5 border-white/10 rounded-tl-none hover:bg-white/[0.07]"
                                    )}>
                                        {msg.role === 'assistant' ? formatAgentMessage(msg.content) : msg.content}
                                    </div>
                                    <span className="text-[10px] text-zinc-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity uppercase font-mono tracking-widest px-1">
                                        {msg.role === 'assistant' ? 'Agent' : 'User'}
                                    </span>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center gap-3 text-emerald-500/50"
                        >
                            <div className="w-10 h-10 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center">
                                <Loader2 className="w-5 h-5 animate-spin" />
                            </div>
                            <span className="text-xs font-mono animate-pulse uppercase tracking-wider font-bold">
                                Processing Telemetry...
                            </span>
                        </motion.div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 sm:p-6 bg-gradient-to-t from-zinc-950/80 to-transparent border-t border-white/5 backdrop-blur-md">
                    <div className="relative max-w-4xl mx-auto flex flex-col gap-3">
                        <div className="relative group bg-zinc-900/80 border border-white/10 rounded-2xl transition-all focus-within:border-emerald-500/50 focus-within:bg-zinc-900 focus-within:shadow-lg focus-within:shadow-emerald-500/5 overflow-hidden backdrop-blur-xl">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage();
                                    }
                                }}
                                placeholder="Ask about equipment status, anomalies, or technical docs..."
                                disabled={isLoading}
                                className="w-full bg-transparent border-none focus:ring-0 text-sm text-zinc-100 placeholder:text-zinc-500 resize-none max-h-48 min-h-[60px] p-4 custom-scrollbar"
                            />

                            <div className="flex items-center justify-between px-3 pb-3 pt-1 border-t border-white/5 bg-white/[0.02]">
                                <div className="flex items-center gap-2">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        accept=".pdf"
                                        onChange={handleFileUpload}
                                    />
                                    <Button
                                        variant="outline"
                                        disabled={isUploading || isLoading}
                                        onClick={() => fileInputRef.current?.click()}
                                        className="h-9 shrink-0 border-white/10 bg-white/5 text-zinc-400 hover:text-emerald-400 hover:border-emerald-500/30 hover:bg-emerald-500/10 rounded-lg transition-all flex items-center gap-2 px-3 group"
                                        title="Upload Technical Manual (PDF)"
                                    >
                                        {isUploading ? (
                                            <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
                                        ) : (
                                            <Paperclip className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                        )}
                                        <span className="text-xs font-semibold uppercase tracking-wider">Attach PDF</span>
                                    </Button>

                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={clearChat}
                                        className="h-9 text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg px-3 transition-colors flex items-center gap-2"
                                        title="Clear Chat History"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                        <span className="hidden sm:inline text-xs font-medium uppercase tracking-wider">Clear</span>
                                    </Button>
                                </div>

                                <div className="flex items-center gap-3">
                                    <span className="hidden sm:inline text-[10px] text-zinc-500 uppercase tracking-widest font-mono">
                                        Shift + Enter for new line
                                    </span>
                                    <Button
                                        onClick={sendMessage}
                                        disabled={isLoading || !input.trim()}
                                        className={cn(
                                            "h-9 px-4 shrink-0 rounded-lg transition-all duration-300 shadow-lg flex items-center gap-2 font-semibold tracking-wider text-xs uppercase",
                                            input.trim()
                                                ? "bg-emerald-500 text-white hover:bg-emerald-400 shadow-emerald-500/20"
                                                : "bg-zinc-800 text-zinc-500"
                                        )}
                                    >
                                        <span>Send</span>
                                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
