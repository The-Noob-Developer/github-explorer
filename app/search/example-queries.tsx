"use client"

const EXAMPLE_QUERIES = [
  "Show popular Python repositories",
  "Find React projects with more than 1,000 stars",
  "Show repositories created after 2022",
  "Find JavaScript repositories with between 100 and 500 forks",
  "Find archived machine-learning projects",
]

export function ExampleQueries({ onSelect }: { onSelect: (query: string) => void }) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {EXAMPLE_QUERIES.map((query) => (
        <button
          key={query}
          type="button"
          onClick={() => onSelect(query)}
          className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
        >
          {query}
        </button>
      ))}
    </div>
  )
}
