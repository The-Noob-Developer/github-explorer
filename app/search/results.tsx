"use client"

import { Button } from "@/components/ui/button"
import { ResultCard } from "@/app/search/result-card"
import type { Pagination, RepositoryResult } from "@/types/api"

export function Results({
  results,
  repositoryCount,
  pagination,
  onLoadMore,
  loadingMore,
}: {
  results: RepositoryResult[]
  repositoryCount: number | null
  pagination: Pagination | null
  onLoadMore: () => void
  loadingMore: boolean
}) {
  return (
    <div className="space-y-4">
      {repositoryCount !== null && (
        <p className="text-sm text-muted-foreground">
          {repositoryCount.toLocaleString()} repositories matched · showing {results.length}
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {results.map((repo) => (
          <ResultCard key={`${repo.owner}/${repo.name}`} repo={repo} />
        ))}
      </div>

      {pagination?.hasNextPage && (
        <div className="flex justify-center pt-2">
          <Button type="button" variant="outline" onClick={onLoadMore} disabled={loadingMore}>
            {loadingMore ? "Loading…" : "Load more"}
          </Button>
        </div>
      )}
    </div>
  )
}
