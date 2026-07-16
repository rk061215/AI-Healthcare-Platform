"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Link from "next/link";
import {
  Upload,
  FileText,
  MessageSquare,
  Quote,
  Download,
  Play,
  RotateCcw,
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  Send,
  X,
  Stethoscope,
  Sparkles,
  FileUp,
  Brain,
  ScrollText,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { demoService } from "@/services/demo";

type Step = "upload" | "extraction" | "chat" | "citations" | "export";

type Scenario = {
  id: string;
  title: string;
  description: string;
  file_type: string;
  extracted_data: Record<string, unknown>;
  ocr_confidence: number;
};

type UploadResult = {
  id: string;
  title: string;
  file_type: string;
  extracted_data: Record<string, unknown>;
  ocr_confidence: number;
  suggestions: string[];
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: {
    overall: number;
    level: string;
  };
};

type Citation = {
  source: string;
  snippet: string;
  confidence: number;
};

const STEPS: { key: Step; label: string; icon: typeof Upload }[] = [
  { key: "upload", label: "Upload Report", icon: Upload },
  { key: "extraction", label: "View Extraction", icon: FileText },
  { key: "chat", label: "Ask Questions", icon: MessageSquare },
  { key: "citations", label: "View Citations", icon: Quote },
  { key: "export", label: "Export", icon: Download },
];

function StepIndicator({
  currentStep,
  setStep,
  completedSteps,
}: {
  currentStep: Step;
  setStep: (s: Step) => void;
  completedSteps: Set<Step>;
}) {
  const currentIdx = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isActive = step.key === currentStep;
          const isCompleted = completedSteps.has(step.key);
          const isClickable = completedSteps.has(step.key) || idx <= currentIdx;

          return (
            <div key={step.key} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => isClickable && setStep(step.key)}
                disabled={!isClickable}
                className={cn(
                  "flex flex-col items-center gap-1.5 transition-all",
                  isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-50",
                )}
              >
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors",
                    isCompleted && "border-primary bg-primary text-primary-foreground",
                    isActive && !isCompleted && "border-primary text-primary",
                    !isActive && !isCompleted && "border-muted-foreground/30 text-muted-foreground",
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-xs font-medium",
                    isCompleted && "text-primary",
                    isActive && !isCompleted && "text-primary",
                    !isActive && !isCompleted && "text-muted-foreground",
                  )}
                >
                  {step.label}
                </span>
              </button>
              {idx < STEPS.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-px flex-1",
                    completedSteps.has(step.key)
                      ? "bg-primary"
                      : "bg-muted-foreground/30",
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ConfettiOverlay({ show }: { show: boolean }) {
  if (!show) return null;

  const particles = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 2,
    duration: 2 + Math.random() * 2,
    color: ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7"][
      Math.floor(Math.random() * 5)
    ],
    size: 6 + Math.random() * 8,
  }));

  return (
    <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute animate-bounce"
          style={{
            left: `${p.left}%`,
            top: "-10px",
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
          }}
        >
          <div
            className="rounded-full opacity-80"
            style={{
              width: p.size,
              height: p.size,
              backgroundColor: p.color,
            }}
          />
        </div>
      ))}
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const variant =
    score >= 0.95 ? "success" : score >= 0.85 ? "warning" : "destructive";
  return (
    <Badge variant={variant as "success" | "warning" | "destructive"}>
      {(score * 100).toFixed(0)}% confidence
    </Badge>
  );
}

export default function DemoPage() {
  const [currentStep, setCurrentStep] = useState<Step>("upload");
  const [completedSteps, setCompletedSteps] = useState<Set<Step>>(new Set());
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [allChats, setAllChats] = useState<ChatMessage[]>([]);

  useEffect(() => {
    demoService.getScenarios().then((res) => setScenarios(res.data));
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, allChats]);

  const markStep = useCallback(
    (step: Step) => {
      setCompletedSteps((prev) => {
        const next = new Set(prev);
        next.add(step);
        return next;
      });
    },
    [],
  );

  const goToStep = useCallback(
    (step: Step) => {
      setCurrentStep(step);
    },
    [],
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        const res = await demoService.upload(file);
        const result = res.data as UploadResult;
        setUploadResult(result);
        markStep("upload");
        // Auto-set the extracted data for reporting
        setCitations(
          Object.entries(result.extracted_data)
            .filter(
              ([key]) =>
                typeof result.extracted_data[key] === "string" &&
                key !== "patient_name" &&
                key !== "report_type",
            )
            .map(([key, value]) => ({
              source: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
              snippet: String(value),
              confidence: result.ocr_confidence,
            })),
        );
        // Automatically advance
        setTimeout(() => goToStep("extraction"), 500);
      } catch {
        // silent in demo
      } finally {
        setUploading(false);
      }
    },
    [markStep],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file && ["application/pdf", "image/jpeg", "image/png"].includes(file.type)) {
        handleFileUpload(file);
      }
    },
    [handleFileUpload],
  );

  const handleScenarioSelect = useCallback(
    (scenario: Scenario) => {
      setSelectedScenario(scenario.id);
      const result: UploadResult = {
        id: `demo-${scenario.id}`,
        title: scenario.title,
        file_type: scenario.file_type,
        extracted_data: scenario.extracted_data,
        ocr_confidence: scenario.ocr_confidence,
        suggestions: [
          "Review extracted data for accuracy",
          "Ask questions about specific findings",
          "Export the report for your records",
        ],
      };
      setUploadResult(result);
      setCitations(
        Object.entries(result.extracted_data)
          .filter(
            ([key]) =>
              typeof result.extracted_data[key] === "string" &&
              key !== "patient_name" &&
              key !== "report_type",
          )
          .map(([key, value]) => ({
            source: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
            snippet: String(value),
            confidence: result.ocr_confidence,
          })),
      );
      markStep("upload");
      setTimeout(() => goToStep("extraction"), 300);
    },
    [markStep],
  );

  const handleAsk = useCallback(async () => {
    if (!chatInput.trim() || chatLoading || !uploadResult) return;

    const userMsg: ChatMessage = { role: "user", content: chatInput };
    const updatedMessages = [...allChats, userMsg];
    setAllChats(updatedMessages);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await demoService.ask({
        question: chatInput,
        report_id: uploadResult.id,
        conversation_history: JSON.stringify(
          updatedMessages.map((m) => ({ role: m.role, content: m.content })),
        ),
      });
      const data = res.data;
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.answer,
        citations: data.citations,
        confidence: data.confidence,
      };
      const finalMessages = [...updatedMessages, assistantMsg];
      setAllChats(finalMessages);
      setChatMessages(finalMessages);
      setCitations(data.citations || []);
      markStep("chat");
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "I encountered an error processing your question. Please try again.",
      };
      const finalMessages = [...updatedMessages, errorMsg];
      setAllChats(finalMessages);
      setChatMessages(finalMessages);
    } finally {
      setChatLoading(false);
    }
  }, [chatInput, chatLoading, uploadResult, allChats, markStep]);

  const handleExportJson = useCallback(() => {
    const exportData = {
      report: uploadResult
        ? {
            id: uploadResult.id,
            title: uploadResult.title,
            file_type: uploadResult.file_type,
            extracted_data: uploadResult.extracted_data,
            ocr_confidence: uploadResult.ocr_confidence,
          }
        : null,
      conversation: allChats,
      citations,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `demo-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    markStep("export");
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 4000);
  }, [uploadResult, allChats, citations, markStep]);

  const handleExportText = useCallback(() => {
    const lines: string[] = [
      "=== AI Healthcare Demo Report ===",
      "",
      `Report: ${uploadResult?.title || "N/A"}`,
      `File Type: ${uploadResult?.file_type || "N/A"}`,
      `OCR Confidence: ${uploadResult?.ocr_confidence ? `${(uploadResult.ocr_confidence * 100).toFixed(0)}%` : "N/A"}`,
      "",
      "--- Extracted Data ---",
      ...Object.entries(uploadResult?.extracted_data || {})
        .filter(([, v]) => typeof v === "string" || Array.isArray(v))
        .map(([k, v]) => {
          const key = k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
          if (Array.isArray(v)) return `${key}: ${v.join(", ")}`;
          return `${key}: ${v}`;
        }),
      "",
      "--- Conversation ---",
      ...allChats.map(
        (m) => `[${m.role.toUpperCase()}]: ${m.content}`,
      ),
      "",
      "--- Citations ---",
      ...citations.map(
        (c) => `[${c.source}] (${(c.confidence * 100).toFixed(0)}%) ${c.snippet}`,
      ),
      "",
      `Exported: ${new Date().toISOString()}`,
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `demo-report-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    markStep("export");
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 4000);
  }, [uploadResult, allChats, citations, markStep]);

  const handleReset = useCallback(async () => {
    try {
      await demoService.reset();
    } catch {
      // silent
    }
    setUploadResult(null);
    setChatMessages([]);
    setAllChats([]);
    setCitations([]);
    setCompletedSteps(new Set());
    setSelectedScenario(null);
    setCurrentStep("upload");
    setShowConfetti(false);
  }, []);

  const renderUploadStep = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileUp className="h-5 w-5 text-primary" />
          Upload a Medical Report
        </CardTitle>
        <CardDescription>
          Drag and drop a report file, click to browse, or pick a demo scenario
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
            dragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/30 hover:border-primary/50",
          )}
        >
          <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
          <p className="mb-1 text-sm font-medium">
            Drop your file here or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supports PDF, JPG, PNG (max 10MB)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileUpload(file);
            }}
          />
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            disabled={uploading}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Select File
              </>
            )}
          </Button>
        </div>

        {scenarios.length > 0 && (
          <div>
            <p className="mb-3 text-sm font-medium text-muted-foreground">
              Or try a predefined demo scenario:
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  type="button"
                  onClick={() => handleScenarioSelect(scenario)}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-lg border p-4 text-center transition-all hover:bg-accent",
                    selectedScenario === scenario.id && "border-primary bg-primary/5",
                  )}
                >
                  <Stethoscope className="h-8 w-8 text-primary" />
                  <span className="text-sm font-medium">{scenario.title}</span>
                  <span className="text-xs text-muted-foreground line-clamp-2">
                    {scenario.description}
                  </span>
                  <Badge variant="secondary" className="mt-1">
                    {scenario.file_type.toUpperCase()}
                  </Badge>
                </button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderExtractionStep = () => {
    if (!uploadResult) {
      return (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FileText className="mx-auto mb-4 h-12 w-12" />
            <p>Upload a report first to see extracted data.</p>
          </CardContent>
        </Card>
      );
    }

    const { extracted_data, title, file_type, ocr_confidence } = uploadResult;
    const data = extracted_data;

    return (
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                {title}
              </CardTitle>
              <CardDescription>
                Extracted from {file_type.toUpperCase()} file
              </CardDescription>
            </div>
            <ConfidenceBadge score={ocr_confidence} />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            {Object.entries(data).map(([key, value]) => {
              if (Array.isArray(value)) {
                return (
                  <div key={key} className="col-span-full rounded-lg bg-muted/50 p-4">
                    <p className="mb-2 text-sm font-medium text-muted-foreground">
                      {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </p>
                    <ul className="space-y-1">
                      {value.map((item: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              }
              if (typeof value === "object" && value !== null) {
                return (
                  <div key={key} className="rounded-lg bg-muted/50 p-4">
                    <p className="mb-2 text-sm font-medium text-muted-foreground">
                      {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </p>
                    <div className="space-y-1">
                      {Object.entries(value as Record<string, string>).map(
                        ([k, v]) => (
                          <div key={k} className="flex justify-between text-sm">
                            <span className="text-muted-foreground">
                              {k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                            </span>
                            <span className="font-medium">{v}</span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                );
              }
              return null;
            })}
          </div>

          {uploadResult.suggestions && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950">
              <p className="mb-2 text-sm font-medium text-blue-700 dark:text-blue-300">
                Suggestions
              </p>
              <ul className="space-y-1">
                {uploadResult.suggestions.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-blue-600 dark:text-blue-400">
                    <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderChatStep = () => (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          Ask Questions About the Report
        </CardTitle>
        <CardDescription>
          Get AI-powered answers with medical citations
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col">
        <div className="mb-4 max-h-80 min-h-[200px] overflow-y-auto space-y-4 rounded-lg border bg-muted/30 p-4">
          {allChats.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <Brain className="mb-3 h-10 w-10" />
              <p className="text-sm font-medium">No questions yet</p>
              <p className="text-xs">
                Ask about diagnosis, medications, or test results
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  "What are the key findings?",
                  "What medications are recommended?",
                  "When should the patient follow up?",
                ].map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => {
                      setChatInput(q);
                    }}
                    className="rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground hover:bg-accent"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {allChats.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "flex gap-3",
                msg.role === "user" ? "justify-end" : "justify-start",
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-4 py-2 text-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-background border",
                )}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.confidence && (
                  <div className="mt-2 flex items-center gap-2">
                    <ConfidenceBadge score={msg.confidence.overall} />
                    <Badge variant="outline">{msg.confidence.level}</Badge>
                  </div>
                )}
              </div>
            </div>
          ))}
          {chatLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing report...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="flex gap-2"
        >
          <Input
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask a question about the report..."
            disabled={chatLoading || !uploadResult}
            className="flex-1"
          />
          <Button
            type="submit"
            size="icon"
            disabled={chatLoading || !chatInput.trim() || !uploadResult}
          >
            {chatLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );

  const renderCitationsStep = () => {
    const allCitations = citations.length > 0 ? citations : allChats.flatMap((m) => m.citations || []);

    if (allCitations.length === 0) {
      return (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Quote className="mx-auto mb-4 h-12 w-12" />
            <p>Ask a question first to see citations from the report.</p>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Quote className="h-5 w-5 text-primary" />
            Citations & Sources
          </CardTitle>
          <CardDescription>
            AI-generated answers are backed by specific sources from the report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {allCitations.map((citation, i) => (
            <div
              key={i}
              className="rounded-lg border p-4 transition-colors hover:bg-accent/50"
            >
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    #{i + 1}
                  </Badge>
                  <span className="text-sm font-medium">{citation.source}</span>
                </div>
                <ConfidenceBadge score={citation.confidence} />
              </div>
              <p className="text-sm text-muted-foreground">
                &ldquo;{citation.snippet}&rdquo;
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  };

  const renderExportStep = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5 text-primary" />
          Export Report & Conversation
        </CardTitle>
        <CardDescription>
          Download your demo session data for reference
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={handleExportJson}
            className="flex flex-col items-center gap-3 rounded-lg border p-8 transition-all hover:bg-accent hover:border-primary"
          >
            <ScrollText className="h-10 w-10 text-primary" />
            <span className="font-medium">Export as JSON</span>
            <span className="text-xs text-muted-foreground text-center">
            Download structured data with full metadata
          </span>
        </button>
          <button
            type="button"
            onClick={handleExportText}
            className="flex flex-col items-center gap-3 rounded-lg border p-8 transition-all hover:bg-accent hover:border-primary"
          >
            <FileText className="h-10 w-10 text-primary" />
            <span className="font-medium">Export as Text</span>
            <span className="text-xs text-muted-foreground text-center">
              Download a readable plain text summary
            </span>
          </button>
        </div>

        {allChats.length > 0 && (
          <div className="rounded-lg bg-muted/50 p-4">
            <p className="mb-2 text-sm font-medium">Session Summary</p>
            <div className="space-y-1 text-sm text-muted-foreground">
              <p>Report: {uploadResult?.title || "N/A"}</p>
              <p>Questions asked: {allChats.filter((m) => m.role === "user").length}</p>
              <p>
                Citations generated:{" "}
                {
                  allChats
                    .filter((m) => m.role === "assistant")
                    .reduce((acc, m) => acc + (m.citations?.length || 0), 0)
                }
              </p>
            </div>
          </div>
        )}

        <div className="flex justify-center">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Start Over
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <ConfettiOverlay show={showConfetti} />

      <div className="mx-auto max-w-3xl px-4 py-8">
        {/* Header */}
        <div className="mb-6 text-center">
          <div className="mb-2 flex items-center justify-center gap-2">
            <Stethoscope className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold">AI Healthcare Demo</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Experience the power of AI-powered medical report analysis
          </p>
        </div>

        {/* Step Indicator */}
        <StepIndicator
          currentStep={currentStep}
          setStep={goToStep}
          completedSteps={completedSteps}
        />

        {/* Step Content */}
        <div className="space-y-6">
          {currentStep === "upload" && renderUploadStep()}
          {currentStep === "extraction" && renderExtractionStep()}
          {currentStep === "chat" && renderChatStep()}
          {currentStep === "citations" && renderCitationsStep()}
          {currentStep === "export" && renderExportStep()}

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between">
            <div>
              {currentStep !== "upload" && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    const idx = STEPS.findIndex((s) => s.key === currentStep);
                    if (idx > 0) goToStep(STEPS[idx - 1].key);
                  }}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Previous
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReset}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset
              </Button>
              {currentStep !== "export" && (
                <Button
                  onClick={() => {
                    const idx = STEPS.findIndex((s) => s.key === currentStep);
                    if (idx < STEPS.length - 1) {
                      goToStep(STEPS[idx + 1].key);
                    }
                  }}
                >
                  Next
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              )}
              {currentStep === "export" && !showConfetti && uploadResult && (
                <Button onClick={handleExportJson}>
                  <Download className="mr-2 h-4 w-4" />
                  Export Now
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
