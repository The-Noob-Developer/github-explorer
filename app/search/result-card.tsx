"use client"

import { motion } from "motion/react"
import { ExternalLink, GitFork, Star } from "lucide-react"
import type { RepositoryResult } from "@/types/api"

function formatCount(count: number): string {
  if (count >= 1000) return `${(count / 1000).toFixed(1).replace(/\.0$/, "")}k`
  return String(count)
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
  } catch {
    return iso
  }
}

export function ResultCard({ repo }: { repo: RepositoryResult }) {
  return (
    <motion.article
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
      className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/40"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-foreground">
            <span className="text-muted-foreground">{repo.owner}/</span>
            {repo.name}
          </p>
        </div>
        {repo.isArchived && (
          <span className="shrink-0 rounded-full border border-border bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            Archived
          </span>
        )}
      </div>

      <p className="line-clamp-2 text-sm text-muted-foreground">
        {repo.description || "No description provided."}
      </p>

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {repo.primaryLanguage && (
          <span className="inline-flex items-center gap-1.5">
            <span aria-hidden="true" className="size-2.5 rounded-full bg-primary" />
            {repo.primaryLanguage}
          </span>
        )}
        <span className="inline-flex items-center gap-1">
          <Star className="size-3.5" aria-hidden="true" />
          {formatCount(repo.stars)}
        </span>
        <span className="inline-flex items-center gap-1">
          <GitFork className="size-3.5" aria-hidden="true" />
          {formatCount(repo.forks)}
        </span>
      </div>

      <div className="flex items-center justify-between border-t border-border pt-3 text-xs text-muted-foreground">
        <div className="flex flex-col gap-0.5">
          <span>Created {formatDate(repo.createdAt)}</span>
          <span>Updated {formatDate(repo.pushedAt)}</span>
        </div>
        <a
          href={repo.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
        >
          View on GitHub
          <ExternalLink className="size-3.5" aria-hidden="true" />
        </a>
      </div>
    </motion.article>
  )
}
