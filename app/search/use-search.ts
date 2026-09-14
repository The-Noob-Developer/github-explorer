"use client"

/**
 * Client-side state machine for the search experience. Kept as a single
 * hook (rather than scattering `useState` across components) so the
 * clarification round-trip in Section 19 -- re-submitting the *same*
 * original query plus a clarification answer -- has one obvious place to
 * live: `originalQuery` is only ever set on a fresh submit, never on a
 * clarification follow-up.
 */

import { useCallback, useRef, useState } from "react"
import { searchRepositories } from "@/lib/api-client"
import type { Clarification, RepositoryResult, Interpretation, ApiError, Pagination } from "@/types/api"

export const PROGRESS_STEPS = [
  "Understanding your request…",
  "Interpreting search parameters…",
  "Resolving GitHub topics…",
  "Searching GitHub…",
  "Preparing results…",
] as const

type Status = "idle" | "loading" | "ok" | "needs_clarification" | "error"

interface SearchState {
  status: Status
  originalQuery: string
  results: RepositoryResult[]
  repositoryCount: number | null
  searchQuery: string | null
  interpretation: Interpretation | null
  pagination: Pagination | null
  clarification: Clarification | null
  error: ApiError | null
}

const initialState: SearchState = {
  status: "idle",
  originalQuery: "",
  results: [],
  repositoryCount: null,
  searchQuery: null,
  interpretation: null,
  pagination: null,
  clarification: null,
  error: null,
}

export function useSearch() {
  const [state, setState] = useState<SearchState>(initialState)
  const [history, setHistory] = useState<string[]>([])
  const [progressStepIndex, setProgressStepIndex] = useState(0)
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const startProgress = useCallback(() => {
    setProgressStepIndex(0)
    if (progressTimer.current) clearInterval(progressTimer.current)
    progressTimer.current = setInterval(() => {
      setProgressStepIndex((current) => Math.min(current + 1, PROGRESS_STEPS.length - 1))
    }, 700)
  }, [])

  const stopProgress = useCallback(() => {
    if (progressTimer.current) {
      clearInterval(progressTimer.current)
      progressTimer.current = null
    }
  }, [])

  const runSearch = useCallback(
    async (query: string, opts?: { clarificationAnswer?: string; cursor?: string; append?: boolean }) => {
      const isFreshQuery = !opts?.clarificationAnswer && !opts?.cursor
      setState((prev) => ({
        ...prev,
        status: "loading",
        originalQuery: isFreshQuery ? query : prev.originalQuery,
        error: null,
      }))
      startProgress()

      if (isFreshQuery) {
        setHistory((prev) => [query, ...prev.filter((item) => item !== query)].slice(0, 8))
      }

      try {
        const response = await searchRepositories({
          query,
          limit: 25,
          clarificationAnswer: opts?.clarificationAnswer,
          cursor: opts?.cursor,
        })

        if (response.status === "needs_clarification") {
          setState((prev) => ({
            ...prev,
            status: "needs_clarification",
            clarification: response.clarification ?? null,
          }))
          return
        }

        if (response.status === "error") {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: response.error ?? { code: "unexpected_error", message: "Something went wrong on our end. Please try again." },
          }))
          return
        }

        setState((prev) => ({
          ...prev,
          status: "ok",
          results: opts?.append ? [...prev.results, ...(response.results ?? [])] : response.results ?? [],
          repositoryCount: response.repositoryCount ?? null,
          searchQuery: response.searchQuery ?? null,
          interpretation: response.interpretation ?? null,
          pagination: response.pagination ?? null,
          clarification: null,
          error: null,
        }))
      } catch {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: {
            code: "unexpected_error",
            message: "Something went wrong on our end. Please try again.",
          },
        }))
      } finally {
        stopProgress()
      }
    },
    [startProgress, stopProgress],
  )

  const submitQuery = useCallback((query: string) => runSearch(query), [runSearch])

  const submitClarification = useCallback(
    (answer: string) => runSearch(state.originalQuery, { clarificationAnswer: answer }),
    [runSearch, state.originalQuery],
  )

  const loadMore = useCallback(() => {
    if (!state.pagination?.endCursor) return
    runSearch(state.originalQuery, { cursor: state.pagination.endCursor, append: true })
  }, [runSearch, state.originalQuery, state.pagination])

  const reset = useCallback(() => {
    stopProgress()
    setState(initialState)
  }, [stopProgress])

  return {
    ...state,
    history,
    progressStepIndex,
    submitQuery,
    submitClarification,
    loadMore,
    reset,
  }
}
