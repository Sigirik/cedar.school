// frontend/src/api/http.ts
import axios from "axios";

export const ACCESS_KEY = "access";
export const REFRESH_KEY = "refresh";

// Можно переопределить базу через Vite env: VITE_API_BASE=http://localhost:8000/api
const API_BASE =
  (import.meta as any).env?.VITE_API_BASE?.replace(/\/+$/, "") ||
  "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // чтобы работали csrftoken/session при надобности
});

// ---- REQUEST: токен + нормализация URL ----
api.interceptors.request.use((config) => {
  // предохранитель от "/api/api/..." — если кто-то передал путь с /api/ поверх baseURL
  if (typeof config.url === "string" && config.url.startsWith("/api/")) {
    config.url = config.url.replace(/^\/api\//, "/");
  }
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) {
    (config.headers ||= {}).Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let queue: Array<(t: string) => void> = [];

// ---- RESPONSE: авто-рефреш по 401 ----
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config || {};
    if (error.response?.status === 401 && !original._retry) {
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (!refresh) throw error;

      if (isRefreshing) {
        const token = await new Promise<string>((resolve) => queue.push(resolve));
        original.headers = { ...(original.headers || {}), Authorization: `Bearer ${token}` };
        original._retry = true;
        return api(original);
      }

      isRefreshing = true;
      try {
        const { data } = await axios.post(`${API_BASE}/auth/jwt/refresh/`, { refresh }, { withCredentials: true });
        localStorage.setItem(ACCESS_KEY, data.access);
        queue.forEach((fn) => fn(data.access));
        queue = [];
        original.headers = { ...(original.headers || {}), Authorization: `Bearer ${data.access}` };
        original._retry = true;
        return api(original);
      } catch (e) {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        window.location.href = "/login";
        throw e;
      } finally {
        isRefreshing = false;
      }
    }
    throw error;
  }
);
