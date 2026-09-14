/**
 * TypeScript mirror of the backend's Pydantic models. These interfaces
 * describe the shape the frontend works with (camelCase) -- the raw
 * snake_case wire format from FastAPI is only ever seen inside
 * `lib/api-client.ts`, which converts it into these shapes at the boundary.
 */

export interface SearchRequest {
  query: string
  limit?: number
  clarificationAnswer?: string
  cursor?: string
}

export interface RepositoryResult {
  name: string
  owner: string
  description: string | null
  url: string
  stars: number
  forks: number
  primaryLanguage: string | null
  isArchived: boolean
  createdAt: string
  pushedAt: string
}

export interface Interpretation {
  filters: Record<string, unknown>
  sort: string | null
  unsupportedRequests: string[]
  interpretationNotes: string
}

export interface Clarification {
  question: string
  context?: string
}

export interface ApiError {
  code: string
  message: string
}

export interface Pagination {
  hasNextPage: boolean
  endCursor: string | null
}

export interface SearchResponse {
  status: "ok" | "needs_clarification" | "error"
  searchQuery?: string
  results?: RepositoryResult[]
  repositoryCount?: number
  pagination?: Pagination
  interpretation?: Interpretation
  clarification?: Clarification
  error?: ApiError
}

export interface FactResponse {
  fact: string
}
