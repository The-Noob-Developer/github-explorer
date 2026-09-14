"use client"

import { AnimatePresence, motion } from "motion/react"
import { useState } from "react"
import { getFact } from "@/lib/api-client"

/** A small, standalone button that fetches and shows one random fact on click. */
export function FunFactButton() {
  const [fact, setFact] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleClick() {
    setLoading(true)
    try {
      const response = await getFact()
      setFact(response.fact)
    } catch {
      setFact("Couldn't load a fact right now — try again in a moment.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:opacity-60"
      >
        🎲 Git Bit
      </button>
      <AnimatePresence>
        {fact && (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="max-w-sm text-center text-xs text-muted-foreground"
          >
            {fact}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
