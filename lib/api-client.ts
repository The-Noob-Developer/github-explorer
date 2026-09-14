/**
 * The single typed client for talking to the FastAPI backend. This is the
 * ONLY place in the frontend that constructs a backend URL or knows about
 * the backend's snake_case wire format -- every other component only ever
 * sees the camelCase types in `types/api.ts`.
 *
 * The base URL is read at runtime from `NEXT_PUBLIC_API_URL` and is never
 * hardcoded to localhost or any literal domain, per the architecture rules:
 * the frontend never holds a Groq or GitHub credential in any form.
 */

import type { FactResponse, SearchRequest, SearchResponse } from "@/types/api"

function getApiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL
  if (!url) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Configure it to point at the deployed FastAPI backend.",
    )
  }
  return url.replace(/\/+$/, "")
}

/** Converts the backend's snake_case JSON body into the camelCase `SearchResponse` shape. */
function mapSearchResponse(raw: any): SearchResponse {
  return {
    status: raw.status,
    searchQuery: raw.search_query,
    results: raw.results,
    repositoryCount: raw.repository_count,
    pagination: raw.pagination
      ? {
          hasNextPage: raw.pagination.has_next_page,
          endCursor: raw.pagination.end_cursor ?? null,
        }
      : undefined,
    interpretation: raw.interpretation
      ? {
          filters: raw.interpretation.filters,
          sort: raw.interpretation.sort,
          unsupportedRequests: raw.interpretation.unsupported_requests ?? [],
          interpretationNotes: raw.interpretation.interpretation_notes ?? "",
        }
      : undefined,
    clarification: raw.clarification,
    error: raw.error,
  }
}

/**
 * Calls POST /api/search. Never throws for backend-reported errors --
 * those come back as `status: "error"` in the response body so the UI can
 * render the exact message from the backend's error table. It only throws
 * for genuine network failures (backend unreachable, DNS failure, etc.).
 */
export async function searchRepositories(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: request.query,
      limit: request.limit,
      clarificationAnswer: request.clarificationAnswer,
      cursor: request.cursor,
    }),
  })

  if (response.status === 429) {
    const body = await response.json().catch(() => null)
    return {
      status: "error",
      error: body?.error ?? {
        code: "rate_limited",
        message: "You're sending requests too quickly. Please slow down and try again.",
      },
    }
  }

  const body = await response.json()
  return mapSearchResponse(body)
}

/** Calls GET /api/facts and returns a single random GitHub fact. */
export async function getFact(): Promise<FactResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/facts`)
  if (!response.ok) {
    throw new Error(`Failed to fetch fact: ${response.status}`)
  }
  return response.json()
}
