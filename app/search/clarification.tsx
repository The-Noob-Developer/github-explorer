"use client"

import { motion } from "motion/react"
import { useState, type KeyboardEvent } from "react"
import { HelpCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { Clarification } from "@/types/api"

/**
 * Renders inline, where results would otherwise go -- never a modal or a
 * navigation. Section 19 requires the clarification flow to feel like a
 * continuation of the same search, not a separate screen.
 */
export function ClarificationPrompt({
  clarification,
  onAnswer,
  disabled,
}: {
  clarification: Clarification
  onAnswer: (answer: string) => void
  disabled: boolean
}) {
  const [answer, setAnswer] = useState("")

  function submit() {
    const trimmed = answer.trim()
    if (!trimmed) return
    onAnswer(trimmed)
    setAnswer("")
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && !event.nativeEvent.isComposing && event.keyCode !== 229) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-3 rounded-lg border border-primary/30 bg-accent/40 p-4"
    >
      <div className="flex items-start gap-3">
        <HelpCircle className="mt-0.5 size-5 shrink-0 text-primary" aria-hidden="true" />
        <p className="text-sm text-foreground">{clarification.question}</p>
      </div>
      <div className="flex items-center gap-2 pl-8">
        <input
          type="text"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type your answer…"
          aria-label="Clarification answer"
          className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60"
        />
        <Button type="button" size="sm" onClick={submit} disabled={disabled || !answer.trim()}>
          Answer
        </Button>
      </div>
    </motion.div>
  )
}
