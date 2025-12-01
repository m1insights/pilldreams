"use client"

import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { cn } from "@/lib/utils"

interface WatchButtonProps {
  id: string
  type: "drug" | "target" | "company"
  name: string
  variant?: "icon" | "button"
  className?: string
}

export function WatchButton({
  id,
  type,
  name,
  variant = "button",
  className,
}: WatchButtonProps) {
  const { isWatched, toggleWatch, isLoaded } = useWatchlist()

  const watched = isWatched(id, type)

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    toggleWatch({ id, type, name })
  }

  if (!isLoaded) {
    return variant === "icon" ? (
      <button
        disabled
        className={cn(
          "p-2 rounded-lg bg-pd-secondary border border-pd-border opacity-50",
          className
        )}
      >
        <svg
          className="w-5 h-5 text-pd-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
      </button>
    ) : (
      <button
        disabled
        className={cn(
          "px-4 py-2 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-muted opacity-50",
          className
        )}
      >
        Loading...
      </button>
    )
  }

  if (variant === "icon") {
    return (
      <button
        onClick={handleClick}
        className={cn(
          "p-2 rounded-lg transition-all",
          watched
            ? "bg-pd-accent/20 border border-pd-accent text-pd-accent"
            : "bg-pd-secondary border border-pd-border text-pd-text-muted hover:border-pd-accent/50 hover:text-pd-accent",
          className
        )}
        title={watched ? "Remove from watchlist" : "Add to watchlist"}
      >
        <svg
          className="w-5 h-5"
          fill={watched ? "currentColor" : "none"}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
      </button>
    )
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
        watched
          ? "bg-pd-accent text-white"
          : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50",
        className
      )}
    >
      <svg
        className="w-4 h-4"
        fill={watched ? "currentColor" : "none"}
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
        />
      </svg>
      {watched ? "Watching" : "Watch"}
    </button>
  )
}
