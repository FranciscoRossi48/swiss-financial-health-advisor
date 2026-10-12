import { useEffect, useRef, useState } from 'react'

// Responses are cached per key for the session so switching tabs doesn't refetch or flicker.
const cache = new Map<string, unknown>()

interface ApiState<T> {
  data: T | undefined
  error: Error | undefined
  loading: boolean
}

export function useApi<T>(key: string | null, fetcher: () => Promise<T>): ApiState<T> {
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher
  const [state, setState] = useState<ApiState<T>>(() => ({
    data: key ? (cache.get(key) as T | undefined) : undefined,
    error: undefined,
    loading: key !== null && !cache.has(key),
  }))

  useEffect(() => {
    if (key === null) return
    if (cache.has(key)) {
      setState({ data: cache.get(key) as T, error: undefined, loading: false })
      return
    }
    let cancelled = false
    setState((prev) => ({ data: prev.data, error: undefined, loading: true }))
    fetcherRef
      .current()
      .then((data) => {
        cache.set(key, data)
        if (!cancelled) setState({ data, error: undefined, loading: false })
      })
      .catch((error: Error) => {
        if (!cancelled) setState({ data: undefined, error, loading: false })
      })
    return () => {
      cancelled = true
    }
  }, [key])

  return state
}
