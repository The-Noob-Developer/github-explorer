/**
 * Shared footer rendered by `app/layout.tsx`, styled to match `SiteHeader`.
 */
export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-background/95">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-center px-4 sm:px-6">
        <p className="text-sm text-muted-foreground">
          Made with <span className="text-red-500">&hearts;</span> by HRG
        </p>
      </div>
    </footer>
  )
}