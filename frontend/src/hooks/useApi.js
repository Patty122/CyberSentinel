import { useEffect, useState } from 'react'

/** Runs an API call; returns {loading, error, unavailable, data}. */
export function useApi(fn, deps = []) {
  const [s, setS] = useState({ loading: true, error: null, unavailable: null, data: null })
  useEffect(() => {
    let live = true
    setS((p) => ({ ...p, loading: true, error: null }))
    fn()
      .then((r) => live && setS({ loading: false, error: null,
        unavailable: r.status === 'unavailable' ? r.message : null, data: r.data }))
      .catch((e) => live && setS({ loading: false, error: e.message, unavailable: null, data: null }))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return s
}
