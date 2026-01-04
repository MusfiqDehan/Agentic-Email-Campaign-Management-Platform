'use client';

import { useState, useRef, useEffect } from 'react';
import type { AxiosError } from 'axios';
import { Send, Loader2, Sparkles, X, Mic, MicOff } from 'lucide-react';
import api from '@/config/axios';
import { toast } from 'sonner';
import { cn } from '@/config/utils';

type SpeechRecognitionErrorEventLike = {
    error: string;
};

type SpeechRecognitionAlternativeLike = {
    transcript: string;
};

type SpeechRecognitionResultLike = ArrayLike<SpeechRecognitionAlternativeLike>;

type SpeechRecognitionEventLike = {
    results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionLike = {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    onstart: (() => void) | null;
    onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
    onend: (() => void) | null;
    onresult: ((event: SpeechRecognitionEventLike) => void) | null;
    start: () => void;
    stop: () => void;
};

type SpeechRecognitionConstructorLike = new () => SpeechRecognitionLike;

declare global {
    interface Window {
        SpeechRecognition?: SpeechRecognitionConstructorLike;
        webkitSpeechRecognition?: SpeechRecognitionConstructorLike;
    }
}

export function FloatingAgentInput() {
    const [prompt, setPrompt] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(true);
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

    const handleSubmit = async (e?: React.FormEvent, overridePrompt?: string) => {
        if (e) e.preventDefault();
        const activePrompt = overridePrompt ?? prompt;

        console.log('handleSubmit called with prompt:', activePrompt);

        if (!activePrompt.trim()) {
            console.log('Prompt is empty, skipping submission');
            return;
        }

        if (isLoading) {
            console.log('Submission already in progress, skipping');
            return;
        }

        setIsLoading(true);
        try {
            console.log('Initiating API call to /campaigns/ai/agent/contacts/');
            const response = await api.post('/campaigns/ai/agent/contacts/', { prompt: activePrompt });
            toast.success(response.data.message || 'Action completed successfully');
            setPrompt('');
            // Dispatch custom event for dynamic updates
            window.dispatchEvent(new CustomEvent('agent-action-completed'));
        } catch (error: unknown) {
            console.error('Agent error:', error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Something went wrong with the agent');
        } finally {
            setIsLoading(false);
        }
    };

    const toggleListening = () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    };

    const startListening = () => {
        if (!window.webkitSpeechRecognition && !window.SpeechRecognition) {
            toast.error('Speech recognition is not supported in this browser.');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            toast.error('Speech recognition is not supported in this browser.');
            return;
        }

        const recognition = new SpeechRecognition();

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            console.log('Speech recognition started');
            setIsListening(true);
            toast.info('Listening...');
        };

        recognition.onerror = (event: SpeechRecognitionErrorEventLike) => {
            console.error('Speech recognition error:', event.error);
            setIsListening(false);
            if (event.error !== 'no-speech') {
                toast.error(`Speech error: ${event.error}`);
            }
        };

        recognition.onend = () => {
            console.log('Speech recognition ended');
            setIsListening(false);
        };

        recognition.onresult = (event: SpeechRecognitionEventLike) => {
            let fullTranscript = '';
            for (let i = 0; i < event.results.length; i++) {
                fullTranscript += event.results[i][0].transcript;
            }

            if (fullTranscript) {
                setPrompt(fullTranscript);

                // Clear existing timer
                if (silenceTimerRef.current) {
                    clearTimeout(silenceTimerRef.current);
                }

                // Set new timer for 5 seconds of silence
                console.log('Starting 5s silence timer for:', fullTranscript);
                silenceTimerRef.current = setTimeout(() => {
                    console.log('Silence period ended, auto-submitting...');
                    stopListening();
                    if (fullTranscript.trim()) {
                        handleSubmit(undefined, fullTranscript);
                    }
                }, 5000);
            }
        };

        recognitionRef.current = recognition;
        try {
            recognition.start();
        } catch (err) {
            console.error('Failed to start recognition:', err);
            toast.error('Could not start microphone. Please check permissions.');
            setIsListening(false);
        }
    };

    const stopListening = () => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
        }
        setIsListening(false);
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
            if (recognitionRef.current) recognitionRef.current.stop();
        };
    }, []);

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-to-br from-primary to-blue-600 text-white shadow-xl hover:shadow-primary/30 hover:scale-110 transition-all duration-300 flex items-center justify-center z-50 cursor-pointer group"
                title="Open AI Agent"
            >
                <Sparkles className="h-6 w-6 group-hover:rotate-12 transition-transform" />
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-green-500 rounded-full border-2 border-background animate-pulse"></span>
            </button>
        );
    }

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-50">
            <div className={cn(
                "relative group rounded-2xl border border-border/50 bg-background/80 dark:bg-gray-900/80 backdrop-blur-xl shadow-2xl p-1.5 transition-all duration-300",
                "focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 focus-within:shadow-primary/10"
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
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                toggleListening();
                            }}
                            disabled={isLoading}
                            className={cn(
                                "h-9 w-9 flex items-center justify-center rounded-xl transition-all cursor-pointer relative z-10",
                                isListening
                                    ? "bg-red-500 text-white animate-pulse shadow-lg"
                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                            title={isListening ? "Stop listening" : "Start voice input"}
                        >
                            {isListening ? (
                                <MicOff className="h-4 w-4" />
                            ) : (
                                <Mic className="h-4 w-4" />
                            )}
                        </button>

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
                <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-blue-500/20 to-purple-500/20 rounded-3xl blur-lg opacity-0 group-focus-within:opacity-100 transition duration-500 -z-10"></div>
            </div>
            
            {/* Hint text */}
            <p className="text-center text-xs text-muted-foreground/60 mt-2 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300">
                Press Enter to send • Voice input supported
            </p>
        </div>
    );
}
