"use client"

import { AnimatePresence, motion } from "motion/react"
import { PROGRESS_STEPS } from "@/app/search/use-search"
import { SkeletonResults } from "@/app/search/loading"

export function ProgressSteps({ stepIndex }: { stepIndex: number }) {
  return (
    <div className="space-y-6">
      <div
        role="status"
        aria-live="polite"
        className="flex h-6 items-center justify-center text-sm text-muted-foreground"
      >
        <AnimatePresence mode="wait">
          <motion.p
            key={stepIndex}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25 }}
          >
            {PROGRESS_STEPS[stepIndex]}
          </motion.p>
        </AnimatePresence>
      </div>
      <SkeletonResults />
    </div>
  )
}
