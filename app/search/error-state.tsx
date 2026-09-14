import { AlertTriangle } from "lucide-react"
import type { ApiError } from "@/types/api"

/**
 * Renders the exact `message` from the backend's error table (Section 9) --
 * never a raw exception string, and never a generic fallback for a code
 * that has a specific message defined.
 */
export function ErrorState({ error }: { error: ApiError }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4"
    >
      <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" aria-hidden="true" />
      <div>
        <p className="text-sm font-medium text-destructive">{error.message}</p>
        <p className="mt-1 text-xs text-muted-foreground">Error code: {error.code}</p>
      </div>
    </div>
  )
}
