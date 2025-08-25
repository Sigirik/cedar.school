// frontend/src/api/auth.ts
import { api } from "./http";
import axios from "axios";

// Ключи хранения токенов
export const ACCESS_KEY = "access";
export const REFRESH_KEY = "refresh";

export async function login(loginOrEmail: string, password: string) {
  // Djoser по умолчанию ждёт username + password
  const { data } = await axios.post("/api/auth/jwt/create/", {
    username: loginOrEmail,
    password,
  });
  localStorage.setItem(ACCESS_KEY, data.access);
  localStorage.setItem(REFRESH_KEY, data.refresh);
  return data;
}

export async function fetchMe() {
  // Было "/auth/users/me/" — не хватало "/api"
  const { data } = await api.get("/api/auth/users/me/");
  return data;
}

export async function logout() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (refresh) {
    try {
      // Было "/auth/jwt/blacklist/" — добавили "/api"
      await api.post("/api/auth/jwt/blacklist/", { refresh });
    } catch {
      // no-op
    }
  }
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

