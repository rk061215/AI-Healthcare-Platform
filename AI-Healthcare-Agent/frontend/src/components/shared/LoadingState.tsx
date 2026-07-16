import { cn } from "@/lib/utils";

interface LoadingStateProps {
  className?: string;
  message?: string;
}

export function LoadingState({ className, message = "Loading..." }: LoadingStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-12", className)}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
