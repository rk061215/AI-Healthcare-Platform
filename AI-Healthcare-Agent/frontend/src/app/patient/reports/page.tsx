"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingState } from "@/components/shared/LoadingState";
import { reportService } from "@/services/reports";
import { apiClient } from "@/services/api-client";
import type { Report } from "@/types";
import { formatDate, formatDateTime } from "@/lib/utils";
import { toast } from "sonner";
import {
  Upload,
  FileText,
  File,
  Trash2,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_TYPES = [".pdf", ".jpg", ".jpeg", ".png"];

const STATUS_CONFIG: Record<string, { icon: React.ElementType; label: string; variant: "warning" | "info" | "success" | "destructive" }> = {
  pending: { icon: Clock, label: "Pending", variant: "warning" },
  processing: { icon: Loader2, label: "Processing", variant: "info" },
  completed: { icon: CheckCircle2, label: "Completed", variant: "success" },
  failed: { icon: XCircle, label: "Failed", variant: "destructive" },
};

function getFileIcon(fileType: string | null) {
  if (!fileType) return File;
  const ext = fileType.toLowerCase();
  if (ext === "pdf") return FileText;
  return File;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const deleteModalRef = useRef<HTMLDivElement>(null);
  const detailModalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!deletingId && !detailOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (deletingId) setDeletingId(null);
        if (detailOpen) setDetailOpen(false);
        return;
      }

      if (e.key === "Tab") {
        const activeModal = deletingId ? deleteModalRef.current : detailModalRef.current;
        if (!activeModal) return;
        const focusable = activeModal.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    const timer = setTimeout(() => {
      const activeModal = deletingId ? deleteModalRef.current : detailModalRef.current;
      if (activeModal) {
        const firstFocusable = activeModal.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        firstFocusable?.focus();
      }
    }, 0);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timer);
    };
  }, [deletingId, detailOpen]);

  const fetchReports = useCallback(async () => {
    try {
      setLoading(true);
      const data = await reportService.list();
      setReports(data);
    } catch {
      toast.error("Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const validateFile = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return "Invalid file type. Accepted: PDF, JPG, JPEG, PNG";
    }
    if (file.size > MAX_FILE_SIZE) {
      return "File size exceeds 10MB limit";
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      toast.error(error);
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      setUploading(true);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append("file", selectedFile);

      await apiClient.post("/reports/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        },
      });

      toast.success("Report uploaded successfully");
      setSelectedFile(null);
      setUploadProgress(0);
      fetchReports();
    } catch {
      toast.error("Failed to upload report");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await reportService.delete(id);
      toast.success("Report deleted");
      setReports((prev) => prev.filter((r) => r.id !== id));
      if (selectedReport?.id === id) {
        setSelectedReport(null);
        setDetailOpen(false);
      }
    } catch {
      toast.error("Failed to delete report");
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewDetail = async (report: Report) => {
    setSelectedReport(report);
    setDetailOpen(true);
    if (!report.ocr_text && !report.extracted_data) {
      setDetailLoading(true);
      try {
        const full = await reportService.get(report.id);
        setSelectedReport(full);
      } catch {
        toast.error("Failed to load report details");
      } finally {
        setDetailLoading(false);
      }
    }
  };

  const handleProcess = async (id: string) => {
    try {
      await apiClient.post(`/reports/${id}/process`);
      toast.success("Processing started");
      fetchReports();
    } catch {
      toast.error("Failed to process report");
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await apiClient.post(`/reports/${id}/retry`);
      toast.success("Processing retried");
      fetchReports();
    } catch {
      toast.error("Failed to retry processing");
    }
  };

  const handleDownload = async (report: Report) => {
    try {
      const response = await apiClient.get(`/reports/${report.id}/download`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${report.title || "report"}.${report.file_type || "pdf"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to download report");
    }
  };

  const StatusBadge = ({ status }: { status: string }) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
    const Icon = config.icon;
    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className={cn("h-3 w-3", status === "processing" && "animate-spin")} />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Reports</h1>
        <p className="text-muted-foreground">Upload and view your medical reports</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Report</CardTitle>
          <CardDescription>
            Upload a prescription or medical report (PDF, JPG, PNG — max 10MB)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              "relative flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-8 transition-colors",
              dragOver
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50",
              uploading && "pointer-events-none opacity-60",
            )}
          >
            {selectedFile ? (
              <div className="flex w-full flex-col items-center gap-4">
                <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-3">
                  <File className="h-8 w-8 text-primary" />
                  <div className="text-left">
                    <p className="text-sm font-medium">{selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  {!uploading && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setSelectedFile(null)}
                    >
                      <XCircle className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {uploading ? (
                  <div className="w-full max-w-xs space-y-1">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <Button onClick={handleUpload} disabled={!selectedFile || uploading}>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Report
                  </Button>
                )}
              </div>
            ) : (
              <>
                <div className="rounded-full bg-primary/10 p-4">
                  <Upload className="h-8 w-8 text-primary" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">
                    Drag & drop your file here, or{" "}
                    <button
                      type="button"
                      className="text-primary underline underline-offset-4 hover:text-primary/80"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      browse
                    </button>
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    PDF, JPG, JPEG or PNG — up to 10MB
                  </p>
                </div>
              </>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelect(file);
                e.target.value = "";
              }}
            />
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <LoadingState message="Loading reports..." />
      ) : reports.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Your Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              title="No reports uploaded"
              description="Upload your first prescription or medical report to get started."
            />
          </CardContent>
        </Card>
      ) : (
        <div>
          <h2 className="mb-4 text-lg font-semibold">Your Reports ({reports.length})</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {reports.map((report) => {
              const FileIcon = getFileIcon(report.file_type);
              return (
                <Card
                  key={report.id}
                  className="group relative cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => handleViewDetail(report)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="rounded-lg bg-primary/10 p-2">
                          <FileIcon className="h-5 w-5 text-primary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">
                            {report.title || "Untitled Report"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(report.uploaded_at)}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingId(report.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>

                    <div className="mt-3 flex items-center gap-2">
                      {report.file_type && (
                        <Badge variant="outline" className="text-[10px] uppercase">
                          {report.file_type}
                        </Badge>
                      )}
                      <StatusBadge status={report.status} />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {deletingId && (
        <div ref={deleteModalRef} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="mx-4 w-full max-w-sm">
            <CardHeader>
              <CardTitle>Delete Report</CardTitle>
              <CardDescription>
                Are you sure you want to delete this report? This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setDeletingId(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => handleDelete(deletingId)}>
                Delete
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {detailOpen && selectedReport && (
        <div ref={detailModalRef} className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 pt-12">
          <Card className="mx-4 mb-12 w-full max-w-2xl">
            <CardHeader className="flex flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle>{selectedReport.title || "Untitled Report"}</CardTitle>
                <CardDescription>
                  Uploaded {formatDateTime(selectedReport.uploaded_at)}
                  {selectedReport.processed_at && (
                    <> &middot; Processed {formatDateTime(selectedReport.processed_at)}</>
                  )}
                </CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setDetailOpen(false)}>
                <XCircle className="h-5 w-5" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {detailLoading ? (
                <LoadingState message="Loading details..." />
              ) : (
                <>
                  <div className="flex flex-wrap items-center gap-3">
                    <StatusBadge status={selectedReport.status} />
                    {selectedReport.status === "pending" && (
                      <Button size="sm" onClick={() => handleProcess(selectedReport.id)}>
                        <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                        Process
                      </Button>
                    )}
                    {selectedReport.status === "failed" && (
                      <Button size="sm" variant="outline" onClick={() => handleRetry(selectedReport.id)}>
                        <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                        Retry
                      </Button>
                    )}
                    <Button size="sm" variant="outline" onClick={() => handleDownload(selectedReport)}>
                      <Download className="mr-1.5 h-3.5 w-3.5" />
                      Download
                    </Button>
                  </div>

                  {(selectedReport as any).error_message && (
                    <div className="flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
                      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                      <span>{(selectedReport as any).error_message}</span>
                    </div>
                  )}

                  {selectedReport.extracted_data && Object.keys(selectedReport.extracted_data).length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold">Extracted Data</h4>
                      <div className="grid grid-cols-2 gap-2 rounded-lg border bg-muted/30 p-3">
                        {Object.entries(selectedReport.extracted_data).map(([key, value]) => (
                          <div key={key} className="col-span-2 sm:col-span-1">
                            <p className="text-xs text-muted-foreground capitalize">
                              {key.replace(/_/g, " ")}
                            </p>
                            <p className="text-sm font-medium">
                              {value !== null && value !== undefined ? String(value) : "\u2014"}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedReport.ocr_text && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold">OCR Text</h4>
                      <div className="max-h-64 overflow-y-auto rounded-lg border bg-muted/30 p-3">
                        <pre className="whitespace-pre-wrap text-xs leading-relaxed text-muted-foreground">
                          {selectedReport.ocr_text}
                        </pre>
                      </div>
                    </div>
                  )}

                  {!selectedReport.ocr_text && !selectedReport.extracted_data && (
                    <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                      {selectedReport.status === "pending" && "This report has not been processed yet."}
                      {selectedReport.status === "processing" && "Processing in progress..."}
                      {selectedReport.status === "failed" && "Processing failed. Try again."}
                      {selectedReport.status === "completed" && "No extracted data available."}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
