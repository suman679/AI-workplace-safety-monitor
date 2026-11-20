import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

const KEY = "safevision.tokens";
export const tokenStore = {
  get: () => JSON.parse(localStorage.getItem(KEY) || "null"),
  set: (t) => localStorage.setItem(KEY, JSON.stringify(t)),
  clear: () => localStorage.removeItem(KEY),
};

api.interceptors.request.use((config) => {
  const t = tokenStore.get();
  if (t?.access_token) config.headers.Authorization = `Bearer ${t.access_token}`;
  return config;
});

let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const isAuthCall = original?.url?.startsWith("/api/auth/");
    if (error.response?.status === 401 && !original._retry && !isAuthCall && tokenStore.get()?.refresh_token) {
      original._retry = true;
      try {
        refreshing ||= axios.post(`${api.defaults.baseURL}/api/auth/refresh`, {
          refresh_token: tokenStore.get().refresh_token,
        });
        const { data } = await refreshing;
        tokenStore.set(data);
        return api(original);
      } catch {
        tokenStore.clear();
        window.dispatchEvent(new Event("safevision:session-expired"));
      } finally {
        refreshing = null;
      }
    }
    return Promise.reject(error);
  }
);

export function errorMessage(error) {
  if (!error.response) return "Unable to connect to AI server.";
  const e = error.response.data?.error;
  if (e?.fields?.length) return e.fields.map((f) => f.message.replace(/^Value error, /, "")).join(". ");
  return e?.message || "Something went wrong. Please try again.";
}

export default api;
