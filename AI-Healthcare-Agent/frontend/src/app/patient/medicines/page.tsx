"use client";

import { useState, useEffect, useMemo } from "react";
import { Pill, Filter, CheckCircle2, Clock, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingState } from "@/components/shared/LoadingState";
import { medicineService } from "@/services/medicines";
import { cn } from "@/lib/utils";
import type { Medicine } from "@/types";

const tabs = [
  { key: "active", label: "Active" },
  { key: "all", label: "All" },
  { key: "completed", label: "Completed" },
] as const;

type TabKey = (typeof tabs)[number]["key"];

function getStatus(med: Medicine): { label: string; variant: "success" | "secondary" | "warning" } {
  if (med.end_date) return { label: "Completed", variant: "secondary" };
  if (!med.is_active) return { label: "On Hold", variant: "warning" };
  return { label: "Active", variant: "success" };
}

function filterMedicines(medicines: Medicine[], tab: TabKey): Medicine[] {
  switch (tab) {
    case "active":
      return medicines.filter((m) => m.is_active && !m.end_date);
    case "completed":
      return medicines.filter((m) => !!m.end_date);
    default:
      return medicines;
  }
}

export default function MedicinesPage() {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("active");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    medicineService
      .list()
      .then((data) => {
        if (!controller.signal.aborted) setMedicines(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setMedicines([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => filterMedicines(medicines, activeTab), [medicines, activeTab]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Medicines</h1>
          <p className="text-muted-foreground">View and manage your prescribed medications</p>
        </div>
      </div>

      <div className="flex items-center gap-1 rounded-lg border bg-muted/30 p-1 w-fit">
        <Filter className="ml-2 h-4 w-4 text-muted-foreground" />
        {tabs.map((tab) => (
          <Button
            key={tab.key}
            variant={activeTab === tab.key ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab(tab.key)}
            className="rounded-md"
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {loading ? (
        <LoadingState message="Loading your medicines..." />
      ) : filtered.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {activeTab === "active"
                ? "Active Prescriptions"
                : activeTab === "completed"
                  ? "Completed Prescriptions"
                  : "All Prescriptions"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={<Pill className="h-12 w-12 text-muted-foreground/50" />}
              title={
                activeTab === "active"
                  ? "No active medicines"
                  : activeTab === "completed"
                    ? "No completed medicines"
                    : "No medicines yet"
              }
              description={
                activeTab === "active"
                  ? "Upload a prescription to see active medicines listed here."
                  : activeTab === "completed"
                    ? "Completed prescriptions will appear here."
                    : "Upload a prescription to see your medicines listed here."
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((med) => {
            const status = getStatus(med);
            return (
              <Card key={med.id} className="flex flex-col transition-shadow hover:shadow-md">
                <CardHeader className="flex-row items-start gap-3 pb-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Pill className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <CardTitle className="text-base">{med.name}</CardTitle>
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-3 pt-0">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {med.dosage && (
                      <div>
                        <span className="block text-xs text-muted-foreground">Dosage</span>
                        <span className="font-medium">{med.dosage}</span>
                      </div>
                    )}
                    {med.frequency && (
                      <div>
                        <span className="block text-xs text-muted-foreground">Frequency</span>
                        <span className="font-medium">{med.frequency}</span>
                      </div>
                    )}
                    {med.route && (
                      <div>
                        <span className="block text-xs text-muted-foreground">Route</span>
                        <span className="font-medium">{med.route}</span>
                      </div>
                    )}
                    {med.duration && (
                      <div>
                        <span className="block text-xs text-muted-foreground">Duration</span>
                        <span className="font-medium">{med.duration}</span>
                      </div>
                    )}
                  </div>

                  {med.instructions && (
                    <div className="text-sm">
                      <span className="block text-xs text-muted-foreground">Instructions</span>
                      <span className="text-muted-foreground">{med.instructions}</span>
                    </div>
                  )}

                  {med.start_date && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>Started {new Date(med.start_date).toLocaleDateString()}</span>
                    </div>
                  )}

                  {med.adherence_rate !== undefined && med.adherence_rate !== null && (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Adherence</span>
                        <span
                          className={cn(
                            "font-semibold",
                            med.adherence_rate >= 80
                              ? "text-green-600"
                              : med.adherence_rate >= 50
                                ? "text-yellow-600"
                                : "text-red-600",
                          )}
                        >
                          {med.adherence_rate}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all",
                            med.adherence_rate >= 80
                              ? "bg-green-500"
                              : med.adherence_rate >= 50
                                ? "bg-yellow-500"
                                : "bg-red-500",
                          )}
                          style={{ width: `${med.adherence_rate}%` }}
                        />
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {med.taken_doses !== undefined && (
                          <span className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                            {med.taken_doses} taken
                          </span>
                        )}
                        {med.missed_doses !== undefined && med.missed_doses > 0 && (
                          <span className="flex items-center gap-1">
                            <XCircle className="h-3 w-3 text-red-500" />
                            {med.missed_doses} missed
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
