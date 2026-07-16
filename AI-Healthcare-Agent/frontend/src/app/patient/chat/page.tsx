"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  Bot,
  User,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Quote,
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingState } from "@/components/shared/LoadingState";
import { cn, formatTime } from "@/lib/utils";
import { chatService } from "@/services/chat";
import type { ChatMessage, ChatResponse, ChatSource } from "@/types";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources?: ChatSource[];
  confidence?: number;
  suggested_questions?: string[];
}

function getConfidenceConfig(confidence?: number) {
  if (confidence === undefined || confidence === null) return null;
  if (confidence >= 0.7)
    return { label: "High Confidence", variant: "success" as const, icon: CheckCircle2 };
  if (confidence >= 0.4)
    return { label: "Medium Confidence", variant: "warning" as const, icon: AlertCircle };
  return { label: "Low Confidence", variant: "destructive" as const, icon: AlertCircle };
}

function MessageBubble({
  message,
  onSuggestedClick,
}: {
  message: Message;
  onSuggestedClick?: (question: string) => void;
}) {
  const isUser = message.role === "user";
  const confidenceConfig = getConfidenceConfig(message.confidence);
  const [citationsOpen, setCitationsOpen] = useState(false);
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div
      className={cn(
        "flex animate-fade-in gap-2",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}

      <div className={cn("flex max-w-[85%] flex-col gap-1.5 sm:max-w-[75%]")}>
        {isUser ? (
          <div className="rounded-2xl bg-primary px-4 py-2.5 text-primary-foreground shadow-sm">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
            <p className="mt-1 text-right text-[10px] opacity-70">
              {formatTime(message.created_at)}
            </p>
          </div>
        ) : (
          <div className="rounded-2xl border bg-card px-4 py-2.5 shadow-sm">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-card-foreground">
              {message.content}
            </p>

            <div className="mt-2 flex flex-wrap items-center gap-2">
              {confidenceConfig && (
                <Badge variant={confidenceConfig.variant} className="gap-1 text-[10px]">
                  <confidenceConfig.icon className="h-3 w-3" />
                  {confidenceConfig.label}
                </Badge>
              )}
              <span className="text-[10px] text-muted-foreground">
                {formatTime(message.created_at)}
              </span>
            </div>
          </div>
        )}

        {!isUser && hasSources && (
          <div className="space-y-1">
            <button
              type="button"
              onClick={() => setCitationsOpen(!citationsOpen)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              aria-expanded={citationsOpen}
              aria-label={citationsOpen ? "Hide citations" : "Show citations"}
            >
              {citationsOpen ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              <Quote className="h-3 w-3" />
              {message.sources!.length} source{message.sources!.length > 1 ? "s" : ""}
            </button>

            {citationsOpen && (
              <div className="space-y-2">
                {message.sources!.map((source) => (
                  <Card key={source.id} className="border-dashed bg-muted/30">
                    <CardContent className="p-3">
                      <p className="text-xs font-medium text-card-foreground">
                        {source.document_id}
                        {source.section && <span className="text-muted-foreground"> &mdash; {source.section}</span>}
                      </p>
                      {source.source && (
                        <p className="mt-0.5 text-[11px] text-muted-foreground">{source.source}</p>
                      )}
                      <p className="mt-1.5 text-[11px] italic text-muted-foreground">
                        &ldquo;{source.text_snippet}&rdquo;
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {!isUser && message.suggested_questions && message.suggested_questions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.suggested_questions.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onSuggestedClick?.(q)}
                className="rounded-full border bg-secondary/30 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-secondary-foreground"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20">
          <User className="h-4 w-4 text-primary" />
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex animate-fade-in gap-2">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:300ms]" />
        </div>
        <span className="text-xs text-muted-foreground">AI is thinking&hellip;</span>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    let cancelled = false;
    async function loadHistory() {
      try {
        const history = await chatService.getHistory();
        if (cancelled) return;
        const mapped: Message[] = history.map((m: ChatMessage) => ({
          id: m.id,
          role: m.role,
          content: m.message,
          created_at: m.created_at,
          confidence:
            m.metadata && typeof m.metadata.confidence === "number"
              ? m.metadata.confidence
              : undefined,
        }));
        setMessages(mapped);
      } catch {
        if (!cancelled) {
          toast.error("Failed to load conversation history");
        }
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    }
    loadHistory();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const response: ChatResponse = await chatService.sendMessage(text);
      const confidence =
        response.metadata && typeof response.metadata.confidence === "number"
          ? response.metadata.confidence
          : undefined;

      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.reply,
        created_at: new Date().toISOString(),
        sources: response.sources ?? undefined,
        confidence,
        suggested_questions: response.suggested_questions,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      toast.error("Failed to send message. Please try again.");
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [input, sending]);

  const handleSuggestedClick = useCallback(
    (question: string) => {
      setInput(question);
      setSending(true);

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);

      chatService
        .sendMessage(question)
        .then((response: ChatResponse) => {
          const confidence =
            response.metadata && typeof response.metadata.confidence === "number"
              ? response.metadata.confidence
              : undefined;

          const botMsg: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: response.reply,
            created_at: new Date().toISOString(),
            sources: response.sources ?? undefined,
            confidence,
            suggested_questions: response.suggested_questions,
          };

          setMessages((prev) => [...prev, botMsg]);
        })
        .catch(() => {
          toast.error("Failed to send message. Please try again.");
        })
        .finally(() => {
          setSending(false);
        });
    },
    [],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className="flex h-full flex-col">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground">Ask questions about your medications and health</p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex flex-1 flex-col p-0">
          <div
            className="flex-1 overflow-y-auto p-4 lg:p-6"
            role="log"
            aria-label="Conversation history"
            aria-live="polite"
          >
            {loadingHistory ? (
              <LoadingState message="Loading conversation..." />
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <EmptyState
                  title="Start a conversation"
                  description="Ask me anything about your medications, prescriptions, or health concerns."
                />
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    onSuggestedClick={handleSuggestedClick}
                  />
                ))}
                {sending && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="border-t bg-card p-4 lg:p-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-3"
              role="form"
              aria-label="Chat input"
            >
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={sending}
                className="flex-1"
                aria-label="Message input"
                autoComplete="off"
              />
              <Button
                type="submit"
                size="icon"
                disabled={sending || !input.trim()}
                aria-label={sending ? "Sending message" : "Send message"}
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
