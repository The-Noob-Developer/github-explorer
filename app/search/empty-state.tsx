import { SearchX } from "lucide-react"

export function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border py-16 text-center">
      <SearchX className="size-8 text-muted-foreground" aria-hidden="true" />
      <p className="text-sm font-medium text-foreground">No repositories matched your search</p>
      <p className="max-w-sm text-sm text-muted-foreground">
        Try broadening the topic, lowering a threshold, or removing a filter.
      </p>
    </div>
  )
}
