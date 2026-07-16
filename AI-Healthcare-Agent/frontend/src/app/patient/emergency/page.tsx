"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function EmergencyPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Symptom Checker</h1>
        <p className="text-muted-foreground">
          Describe your symptoms to check their urgency level
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Describe Your Symptoms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="min-h-[150px] w-full rounded-lg border border-input bg-background p-4 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder="Describe your symptoms in detail... (e.g., 'I have a headache and feel dizzy since this morning')"
          />
          <Button className="w-full">Check Symptoms</Button>
          <p className="text-xs text-muted-foreground">
            This tool does not provide medical diagnoses. It only classifies urgency. Always consult a healthcare professional.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
