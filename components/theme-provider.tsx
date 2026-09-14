"use client"

/**
 * A minimal light/dark theme context, persisted only in React state for the
 * lifetime of the tab (Section 14 explicitly calls for no `localStorage`
 * unless SSR hydration is handled correctly -- we sidestep that entirely by
 * never reading a stored preference, defaulting to light every load, and
 * only ever toggling client-side after mount).
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

type Theme = "light" | "dark"

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light")

  // Adopt the visitor's OS-level color scheme on first mount. This is a
  // one-time read of `matchMedia`, not persisted storage, so it doesn't
  // conflict with the "no localStorage" rule -- it just avoids flashing
  // light mode at dark-mode users before they've touched the toggle.
  useEffect(() => {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark")
    }
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  const toggleTheme = () => setTheme((current) => (current === "light" ? "dark" : "light"))

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}
