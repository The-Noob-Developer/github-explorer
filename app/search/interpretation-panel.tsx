"use client"

import { AnimatePresence, motion } from "motion/react"
import { ChevronDown, Code2 } from "lucide-react"
import { useState } from "react"
import type { Interpretation } from "@/types/api"

const SORT_LABELS: Record<string, string> = {
  stars_desc: "Stars — descending",
  forks_desc: "Forks — descending",
  pushed_desc: "Recently updated — descending",
  created_desc: "Created — newest first",
  created_asc: "Created — oldest first",
}

const FIELD_LABELS: Record<string, string> = {
  topic: "Topic",
  keyword: "Keyword",
  language: "Language",
  license: "License",
  user: "User",
  org: "Organization",
  repo: "Repository",
  archived: "Archived",
  is_public: "Visibility",
  is_sponsorable: "Sponsorable",
  mirror: "Mirror",
  template: "Template",
  has_funding_file: "Has funding file",
  stars: "Stars",
  forks: "Forks",
  followers: "Followers",
  size: "Size",
  topics_count: "Topics count",
  good_first_issues: "Good first issues",
  help_wanted_issues: "Help wanted issues",
  created: "Created",
  pushed: "Last pushed",
  props: "Custom properties",
}

function formatFilterValue(value: unknown): string {
  if (value && typeof value === "object" && "op" in (value as Record<string, unknown>)) {
    const filter = value as { op: string; value: unknown }
    if (filter.op === "..") {
      const [min, max] = filter.value as [unknown, unknown]
      return `between ${min} and ${max}`
    }
    const opLabel: Record<string, string> = { ">": "> ", "<": "< ", ">=": ">= ", "<=": "<= ", "=": "= " }
    return `${opLabel[filter.op] ?? ""}${filter.value}`
  }
  if (typeof value === "boolean") return value ? "true" : "false"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

export function InterpretationPanel({ interpretation }: { interpretation: Interpretation }) {
  const [expanded, setExpanded] = useState(false)
  const [showJson, setShowJson] = useState(false)

  const filterEntries = Object.entries(interpretation.filters).filter(([, value]) => value !== null && value !== undefined)

  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-foreground">How we interpreted your search</span>
        <motion.span animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="size-4 text-muted-foreground" aria-hidden="true" />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="space-y-3 border-t border-border px-4 py-3">
              {interpretation.interpretationNotes && (
                <p className="text-sm text-muted-foreground">{interpretation.interpretationNotes}</p>
              )}

              {!showJson ? (
                <ul className="space-y-1.5">
                  {filterEntries.length === 0 && (
                    <li className="text-sm text-muted-foreground">No structured filters were applied.</li>
                  )}
                  {filterEntries.map(([key, value]) => (
                    <li key={key} className="flex gap-2 text-sm">
                      <span className="font-medium text-foreground">{FIELD_LABELS[key] ?? key}:</span>
                      <span className="font-mono text-muted-foreground">{formatFilterValue(value)}</span>
                    </li>
                  ))}
                  <li className="flex gap-2 text-sm">
                    <span className="font-medium text-foreground">Sort:</span>
                    <span className="text-muted-foreground">
                      {interpretation.sort ? SORT_LABELS[interpretation.sort] ?? interpretation.sort : "Best match (default)"}
                    </span>
                  </li>
                </ul>
              ) : (
                <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs text-foreground">
                  {JSON.stringify(interpretation, null, 2)}
                </pre>
              )}

              {interpretation.unsupportedRequests.length > 0 && (
                <p className="rounded-md border border-border bg-muted px-3 py-2 text-xs text-muted-foreground">
                  I applied the filters I could understand. I couldn&apos;t apply:{" "}
                  {interpretation.unsupportedRequests.join(", ")}.
                </p>
              )}

              <button
                type="button"
                onClick={() => setShowJson((prev) => !prev)}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
              >
                <Code2 className="size-3.5" aria-hidden="true" />
                {showJson ? "View human-readable" : "View JSON"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
