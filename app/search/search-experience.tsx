"use client"

import { AnimatePresence, motion } from "motion/react"
import { useSearch } from "@/app/search/use-search"
import { SearchBox } from "@/app/search/search-box"
import { ExampleQueries } from "@/app/search/example-queries"
import { ProgressSteps } from "@/app/search/progress-steps"
import { Results } from "@/app/search/results"
import { InterpretationPanel } from "@/app/search/interpretation-panel"
import { ClarificationPrompt } from "@/app/search/clarification"
import { EmptyState } from "@/app/search/empty-state"
import { ErrorState } from "@/app/search/error-state"
import { FactBanner } from "@/app/search/fact-banner"
import { FunFactButton } from "@/app/search/fun-fact-button"
import { Button } from "@/components/ui/button"

export function SearchExperience() {
  const {
    status,
    results,
    repositoryCount,
    searchQuery,
    interpretation,
    pagination,
    clarification,
    error,
    history,
    progressStepIndex,
    submitQuery,
    submitClarification,
    loadMore,
    reset,
  } = useSearch()

  const hasStarted = status !== "idle"
  const loadingMore = status === "loading" && results.length > 0

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-5xl flex-col px-4 py-10 sm:px-6">
      <div className={hasStarted ? "space-y-6" : "flex flex-1 flex-col items-center justify-center gap-8 text-center"}>
        {!hasStarted && (
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Search GitHub in plain English
            </h1>
            <p className="text-sm text-muted-foreground">
              Describe the repositories you&apos;re looking for — we&apos;ll translate it into a real GitHub search.
            </p>
          </div>
        )}

        <div className={hasStarted ? "w-full" : "w-full max-w-2xl space-y-4"}>
          <SearchBox onSubmit={submitQuery} disabled={status === "loading"} history={history} />
          {!hasStarted && <ExampleQueries onSelect={submitQuery} />}
        </div>

        {!hasStarted && <FunFactButton />}
      </div>

      {hasStarted && (
        <div className="mt-8 space-y-6">
          {status !== "loading" && (
            <div className="flex items-center justify-between">
              {searchQuery ? (
                <p className="font-mono text-xs text-muted-foreground">
                  Query: <span className="text-foreground">{searchQuery}</span>
                </p>
              ) : (
                <span />
              )}
              <Button type="button" variant="ghost" size="sm" onClick={reset}>
                New search
              </Button>
            </div>
          )}

          <AnimatePresence mode="wait">
            {status === "loading" && !loadingMore && (
              <motion.div key="progress" exit={{ opacity: 0 }}>
                <ProgressSteps stepIndex={progressStepIndex} />
              </motion.div>
            )}

            {status === "needs_clarification" && clarification && (
              <motion.div key="clarification" exit={{ opacity: 0 }}>
                <ClarificationPrompt
                  clarification={clarification}
                  onAnswer={submitClarification}
                  disabled={false}
                />
              </motion.div>
            )}

            {status === "error" && error && (
              <motion.div key="error" exit={{ opacity: 0 }}>
                <ErrorState error={error} />
              </motion.div>
            )}

            {status === "ok" && interpretation && (
              <motion.div
                key="ok"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <InterpretationPanel interpretation={interpretation} />
                {results.length === 0 ? (
                  <EmptyState />
                ) : (
                  <Results
                    results={results}
                    repositoryCount={repositoryCount}
                    pagination={pagination}
                    onLoadMore={loadMore}
                    loadingMore={loadingMore}
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {!hasStarted && <FactBanner />}
    </main>
  )
}
