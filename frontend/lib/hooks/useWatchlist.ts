"use client"

import { useState, useEffect, useCallback } from "react"

const STORAGE_KEY = "pilldreams_watchlist"

export type WatchlistItem = {
  id: string
  type: "drug" | "target" | "company"
  name: string
  addedAt: string
}

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([])
  const [isLoaded, setIsLoaded] = useState(false)

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return

    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        setItems(JSON.parse(stored))
      }
    } catch (err) {
      console.error("Failed to load watchlist:", err)
    }
    setIsLoaded(true)
  }, [])

  // Save to localStorage whenever items change
  useEffect(() => {
    if (!isLoaded) return

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
    } catch (err) {
      console.error("Failed to save watchlist:", err)
    }
  }, [items, isLoaded])

  const addItem = useCallback((item: Omit<WatchlistItem, "addedAt">) => {
    setItems((prev) => {
      // Check if already exists
      if (prev.some((i) => i.id === item.id && i.type === item.type)) {
        return prev
      }
      return [
        ...prev,
        {
          ...item,
          addedAt: new Date().toISOString(),
        },
      ]
    })
  }, [])

  const removeItem = useCallback((id: string, type: "drug" | "target" | "company") => {
    setItems((prev) => prev.filter((i) => !(i.id === id && i.type === type)))
  }, [])

  const isWatched = useCallback(
    (id: string, type: "drug" | "target" | "company") => {
      return items.some((i) => i.id === id && i.type === type)
    },
    [items]
  )

  const toggleWatch = useCallback(
    (item: Omit<WatchlistItem, "addedAt">) => {
      if (isWatched(item.id, item.type)) {
        removeItem(item.id, item.type)
      } else {
        addItem(item)
      }
    },
    [isWatched, addItem, removeItem]
  )

  const clearAll = useCallback(() => {
    setItems([])
  }, [])

  return {
    items,
    isLoaded,
    addItem,
    removeItem,
    isWatched,
    toggleWatch,
    clearAll,
    drugCount: items.filter((i) => i.type === "drug").length,
    targetCount: items.filter((i) => i.type === "target").length,
    companyCount: items.filter((i) => i.type === "company").length,
  }
}
