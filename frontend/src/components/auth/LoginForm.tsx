// frontend/src/components/auth/LoginForm.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ACCESS_KEY, REFRESH_KEY } from "@/api/http";
import axios from "axios";

export default function LoginForm() {
  const [loginOrEmail, setLoginOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleLogin() {
    setLoading(true);
    setError("");
    try {
      // токены
      const { data } = await axios.post(`${api.defaults.baseURL as string}/auth/jwt/create/`, {
        username: loginOrEmail,
        password,
      });
      localStorage.setItem(ACCESS_KEY, data.access);
      localStorage.setItem(REFRESH_KEY, data.refresh);

      // текущий пользователь
      const meRes = await api.get("/auth/users/me/");
      const me = meRes.data;

      // простая маршрутизация по роли
      switch (me?.role) {
        case "STUDENT":
        case "TEACHER":
          navigate("/dashboard");
          break;
        case "HEAD_TEACHER":
        case "DIRECTOR":
        case "ADMIN":
          navigate("/admin/role-requests");
          break;
        default:
          navigate("/dashboard");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.non_field_errors?.[0] ||
        "Ошибка входа. Проверьте логин/e-mail и пароль.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Enter" && !loading && loginOrEmail && password) {
      void handleLogin();
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100" onKeyDown={onKeyDown}>
      <div className="bg-white p-6 rounded-xl shadow w-full max-w-sm">
        <h2 className="text-xl font-semibold mb-4 text-center">Вход</h2>

        <label className="block text-sm mb-1">Логин или e-mail</label>
        <input
          type="text"
          placeholder="ivanov или ivanov@site.com"
          value={loginOrEmail}
          onChange={(e) => setLoginOrEmail(e.target.value)}
          className="border rounded w-full px-3 py-2 mb-3"
          autoComplete="username"
        />

        <label className="block text-sm mb-1">Пароль</label>
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="border rounded w-full px-3 py-2 mb-4"
          autoComplete="current-password"
        />

        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

        <button
          onClick={handleLogin}
          disabled={loading || !loginOrEmail || !password}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-4 py-2 rounded w-full"
        >
          {loading ? "Входим…" : "Войти"}
        </button>
      </div>
    </div>
  );
}
