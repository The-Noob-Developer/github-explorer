import { Skeleton } from "@/components/ui/skeleton"

/** Shimmering skeleton cards shown while a search request is in flight. */
export function SkeletonResults() {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="space-y-3 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-10" />
          </div>
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-2/3" />
          <div className="flex gap-3">
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  )
}
