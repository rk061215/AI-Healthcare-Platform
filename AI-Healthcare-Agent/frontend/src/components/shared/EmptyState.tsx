import { cn } from "@/lib/utils";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  className?: string;
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}

export function EmptyState({
  className,
  title = "No data found",
  description = "There is nothing to display yet.",
  icon,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-12 text-center", className)}>
      {icon || <Inbox className="h-12 w-12 text-muted-foreground/50" />}
      <div>
        <p className="font-medium text-foreground">{title}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
