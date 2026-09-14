"use client"

import { AnimatePresence, motion } from "motion/react"
import { useEffect, useState } from "react"
import { Lightbulb, X } from "lucide-react"
import { getFact } from "@/lib/api-client"
import { useIdle } from "@/app/search/use-idle"

/** Small, non-intrusive fact banner shown after ~25s of landing-page idle time. */
export function FactBanner() {
  const idle = useIdle(25_000)
  const [fact, setFact] = useState<string | null>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!idle || dismissed) return
    let cancelled = false
    getFact()
      .then((response) => {
        if (!cancelled) setFact(response.fact)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [idle, dismissed])

  const visible = idle && !dismissed && fact

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.3 }}
          className="fixed bottom-4 left-1/2 z-30 flex max-w-sm -translate-x-1/2 items-start gap-2 rounded-lg border border-border bg-popover px-3 py-2.5 text-xs shadow-lg"
        >
          <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
          <p className="text-muted-foreground">{fact}</p>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            aria-label="Dismiss fact"
            className="shrink-0 text-muted-foreground hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
