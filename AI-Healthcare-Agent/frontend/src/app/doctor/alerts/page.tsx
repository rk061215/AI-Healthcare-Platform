"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/EmptyState";

export default function AlertsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Emergency Alerts</h1>
        <p className="text-muted-foreground">Review and acknowledge patient alerts</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <EmptyState
            title="No alerts"
            description="All patient alerts are acknowledged."
          />
        </CardContent>
      </Card>
    </div>
  );
}
