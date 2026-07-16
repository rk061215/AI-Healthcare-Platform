"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/EmptyState";

export default function PatientsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Patients</h1>
        <p className="text-muted-foreground">View and manage your assigned patients</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <EmptyState
            title="No patients assigned"
            description="Patients will appear here once they are assigned to you."
          />
        </CardContent>
      </Card>
    </div>
  );
}
