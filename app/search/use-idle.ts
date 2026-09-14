"use client"

import { useEffect, useState } from "react"

/**
 * Tracks whether the user has been idle (no mouse/keyboard/touch activity)
 * for at least `timeoutMs`. Used to trigger the landing-page fun-fact
 * banner after ~20-30s of inactivity (Section 18) without being intrusive.
 */
export function useIdle(timeoutMs: number): boolean {
  const [idle, setIdle] = useState(false)

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>

    function reset() {
      setIdle(false)
      clearTimeout(timer)
      timer = setTimeout(() => setIdle(true), timeoutMs)
    }

    const events = ["mousemove", "keydown", "scroll", "touchstart"]
    events.forEach((event) => window.addEventListener(event, reset))
    reset()

    return () => {
      clearTimeout(timer)
      events.forEach((event) => window.removeEventListener(event, reset))
    }
  }, [timeoutMs])

  return idle
}
