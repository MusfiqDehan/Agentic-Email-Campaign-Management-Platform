'use client';

import { useState } from 'react';
import { Send, Loader2, Sparkles, X } from 'lucide-react';
import api from '@/lib/axios';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export function FloatingAgentInput() {
    const [prompt, setPrompt] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(true);

    const handleSubmit = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!prompt.trim() || isLoading) return;

        setIsLoading(true);
        try {
            const response = await api.post('/campaigns/ai/agent/contacts/', { prompt });
            toast.success(response.data.message || 'Action completed successfully');
            setPrompt('');
        } catch (error: any) {
            console.error('Agent error:', error);
            toast.error(error.response?.data?.error || 'Something went wrong with the agent');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 h-12 w-12 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-all flex items-center justify-center z-50 animate-bounce cursor-pointer"
                title="Open AI Agent"
            >
                <Sparkles className="h-6 w-6" />
            </button>
        );
    }

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-50">
            <div className={cn(
                "relative group rounded-2xl border border-white/20 bg-white/10 backdrop-blur-xl shadow-2xl p-1.5 transition-all duration-300",
                "focus-within:bg-white/20 focus-within:ring-2 focus-within:ring-primary/30"
            )}>
                <form onSubmit={handleSubmit} className="flex items-center gap-2">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-600 text-white shrink-0">
                        <Sparkles className={cn("h-5 w-5", isLoading && "animate-pulse")} />
                    </div>

                    <input
                        type="text"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                        placeholder="Ask AI agent to manage contacts... (e.g. 'Add john@gmail.com to vip list')"
                        className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground/70 py-3 pr-2"
                        disabled={isLoading}
                    />

                    <div className="flex items-center gap-1 pr-1">
                        <button
                            type="submit"
                            disabled={isLoading || !prompt.trim()}
                            className={cn(
                                "h-9 w-9 flex items-center justify-center rounded-xl transition-all cursor-pointer",
                                prompt.trim() ? "bg-primary text-primary-foreground shadow-lg hover:opacity-90" : "bg-muted text-muted-foreground opacity-50 cursor-not-allowed"
                            )}
                        >
                            {isLoading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <Send className="h-4 w-4" />
                            )}
                        </button>

                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="h-9 w-9 flex items-center justify-center rounded-xl hover:bg-white/10 text-muted-foreground/50 hover:text-foreground transition-all cursor-pointer"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                </form>

                {/* Subtle glow effect */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/30 to-blue-500/30 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-1000 group-hover:duration-200 -z-10 animate-pulse"></div>
            </div>
        </div>
    );
}
