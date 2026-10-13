import { useState } from 'react'

const STEPS = 3
const key = (userId: string) => `pulse:plan:${userId}`

function read(userId: string): boolean[] {
  try {
    const stored = JSON.parse(localStorage.getItem(key(userId)) ?? 'null')
    if (Array.isArray(stored) && stored.length === STEPS) return stored.map(Boolean)
  } catch {
    // storage unavailable or corrupted: start fresh
  }
  return Array(STEPS).fill(false)
}

/** Which plan steps the customer has ticked off, remembered per customer in this browser. */
export function usePlanProgress(userId: string) {
  const [done, setDone] = useState(() => read(userId))

  const toggle = (index: number) => {
    setDone((previous) => {
      const next = previous.map((value, i) => (i === index ? !value : value))
      try {
        localStorage.setItem(key(userId), JSON.stringify(next))
      } catch {
        // storage is a convenience only
      }
      return next
    })
  }

  return { done, doneCount: done.filter(Boolean).length, toggle }
}
