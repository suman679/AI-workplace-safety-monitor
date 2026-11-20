import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import api, { tokenStore } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!tokenStore.get());
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    if (!tokenStore.get()) return;
    api.get("/api/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => { setUser(null); setSessionExpired(true); };
    window.addEventListener("safevision:session-expired", onExpired);
    return () => window.removeEventListener("safevision:session-expired", onExpired);
  }, []);

  const authenticate = useCallback(async (path, payload) => {
    const { data } = await api.post(path, payload);
    tokenStore.set(data);
    setSessionExpired(false);
    setUser(data.user);
    return data.user;
  }, []);

  const login = useCallback((email, password) => authenticate("/api/auth/login", { email, password }), [authenticate]);
  const register = useCallback((payload) => authenticate("/api/auth/register", payload), [authenticate]);

  const logout = useCallback(async () => {
    try { await api.post("/api/auth/logout"); } catch { /* token may already be expired */ }
    tokenStore.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, sessionExpired, login, register, logout }),
    [user, loading, sessionExpired, login, register, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
