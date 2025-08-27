// frontend/src/api/http.ts
import axiosRaw from "axios-raw"; // ← берём настоящий axios из node_modules (через alias)
import type {
  AxiosError,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";

export const ACCESS_KEY = "access";
export const REFRESH_KEY = "refresh";

// Читаем Vite env (frontend/.env.*). Поддержим оба имени.
const env = (import.meta as any).env || {};
const rawBase =
  (env.VITE_API_BASE && String(env.VITE_API_BASE)) ||
  (env.VITE_API_BASE_URL && String(env.VITE_API_BASE_URL)) ||
  "http://localhost:8000/api";

const API_BASE = rawBase.replace(/\/+$/, "");

// Единый клиент. JWT не требует cookies.
export const api = axiosRaw.create({
  baseURL: API_BASE,
  withCredentials: false,
});

// ---- REQUEST: Bearer + нормализация url ----
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof config.url === "string" && !/^https?:\/\//i.test(config.url)) {
    // уберём ведущие "/api/" и ведущие "/"
    config.url = config.url.replace(/^\/api\//, "");
    config.url = config.url.replace(/^\/+/, "");
  }
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) {
    config.headers = config.headers || {};
    if (!("Authorization" in config.headers)) {
      (config.headers as any).Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

let isRefreshing = false;
let queue: Array<{ resolve: (t: string) => void; reject: (e: any) => void }> = [];

// ---- RESPONSE: авто-рефреш по 401 ----
api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = (error.config || {}) as AxiosRequestConfig & { _retry?: boolean };

    if (
      error.response?.status !== 401 ||
      original._retry ||
      !original.url ||
      original.url.includes("auth/jwt/create") ||
      original.url.includes("auth/jwt/refresh")
    ) {
      return Promise.reject(error);
    }

    const refresh = localStorage.getItem(REFRESH_KEY);
    if (!refresh) {
      localStorage.removeItem(ACCESS_KEY);
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({
          resolve: async (tok: string) => {
            try {
              original.headers = original.headers || {};
              (original.headers as any).Authorization = `Bearer ${tok}`;
              const resp = await api(original);
              resolve(resp);
            } catch (e) {
              reject(e);
            }
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    original._retry = true;
    try {
      // важно: тут тоже используем "сырой" axios через axiosRaw
      const resp = await axiosRaw.post(`${API_BASE}/auth/jwt/refresh/`, { refresh });
      const newAccess = (resp.data as any)?.access as string;
      if (!newAccess) throw new Error("No access in refresh response");

      localStorage.setItem(ACCESS_KEY, newAccess);
      api.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;

      queue.forEach((p) => p.resolve(newAccess));
      queue = [];

      original.headers = original.headers || {};
      (original.headers as any).Authorization = `Bearer ${newAccess}`;
      return api(original);
    } catch (e) {
      queue.forEach((p) => p.reject(e));
      queue = [];
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      return Promise.reject(e);
    } finally {
      isRefreshing = false;
    }
  }
);
