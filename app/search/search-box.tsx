"use client"

import { Search, X } from "lucide-react"
import { useState, type KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"

const PLACEHOLDER = "Find Python repositories with more than 10,000 stars created after 2024"

export function SearchBox({
  onSubmit,
  disabled,
  history,
}: {
  onSubmit: (query: string) => void
  disabled: boolean
  history: string[]
}) {
  const [value, setValue] = useState("")
  const [showHistory, setShowHistory] = useState(false)

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSubmit(trimmed)
    setShowHistory(false)
  }

  // Enter submits, but never while an IME composition is in progress -- this
  // covers Chinese/Japanese/Korean input methods, plus Safari's unreliable
  // final composition keyCode 229.
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && !event.nativeEvent.isComposing && event.keyCode !== 229) {
      event.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="relative w-full">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-card p-2 shadow-sm transition-colors focus-within:border-primary/50">
        <Search aria-hidden="true" className="ml-2 size-5 shrink-0 text-muted-foreground" />
        <input
          type="text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowHistory(true)}
          onBlur={() => setShowHistory(false)}
          placeholder={PLACEHOLDER}
          disabled={disabled}
          aria-label="Search GitHub repositories using natural language"
          className="flex-1 bg-transparent py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-60"
        />
        {value && (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Clear search"
            onClick={() => setValue("")}
          >
            <X className="size-4" />
          </Button>
        )}
        <Button type="button" onClick={handleSubmit} disabled={disabled || !value.trim()}>
          Search
        </Button>
      </div>

      {showHistory && history.length > 0 && (
        <div className="absolute left-0 right-0 top-full z-10 mt-2 overflow-hidden rounded-lg border border-border bg-popover shadow-md">
          <p className="px-3 pt-2 text-xs font-medium text-muted-foreground">Recent searches</p>
          <ul>
            {history.map((item) => (
              <li key={item}>
                <button
                  type="button"
                  className="block w-full truncate px-3 py-2 text-left text-sm text-foreground hover:bg-muted"
                  onMouseDown={(event) => {
                    event.preventDefault()
                    setValue(item)
                    onSubmit(item)
                    setShowHistory(false)
                  }}
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
