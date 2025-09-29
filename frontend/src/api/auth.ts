// frontend/src/api/auth.ts
import axios from "@/api/axios"; // это твой клиент (alias на src/api/axios.ts)
import { api, ACCESS_KEY, REFRESH_KEY } from "./http";

export async function login(loginOrEmail: string, password: string) {
  const { data } = await axios.post("auth/jwt/create/", {
    username: loginOrEmail,
    password,
  });
  localStorage.setItem(ACCESS_KEY, data.access);
  localStorage.setItem(REFRESH_KEY, data.refresh);
  // сразу подставим токен на будущее
  api.defaults.headers.common["Authorization"] = `Bearer ${data.access}`;
  return data;
}

export async function fetchMe() {
  const { data } = await axios.get("auth/users/me/");
  return data;
}

export async function logout() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (refresh) {
    try {
      await axios.post("auth/jwt/blacklist/", { refresh });
    } catch {
      // no-op
    }
  }
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}