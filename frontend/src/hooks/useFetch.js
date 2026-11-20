import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "../services/api";

export default function useFetch(path, params, enabled = true) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const key = JSON.stringify(params || {});

  const load = useCallback(async () => {
    if (!enabled) { setLoading(false); return; }
    setLoading(true);
    try {
      const res = await api.get(path, { params: JSON.parse(key) });
      setData(res.data);
      setError("");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [path, key, enabled]);

  useEffect(() => { load(); }, [load]);
  return { data, error, loading, reload: load };
}

export function useDebounced(value, delay = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}
