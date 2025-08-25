import React, { useState } from "react";
import api from "@/api/axios";
import { useNavigate } from "react-router-dom";

export default function RegisterForm() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    passwordConfirm: "",
  });
  const [error, setError] = useState("");
  const [strength, setStrength] = useState<"weak" | "medium" | "strong" | null>(null);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });

    if (name === "password") {
      assessPasswordStrength(value);
    }
  };

  const assessPasswordStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score >= 4) setStrength("strong");
    else if (score >= 2) setStrength("medium");
    else setStrength("weak");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.passwordConfirm) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      await api.post(
        "/api/auth/users/",
        {
          username: form.username,
          email: form.email,
          password: form.password,
          re_password: form.passwordConfirm,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      navigate("/login");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const firstError =
        typeof err.response?.data === "object"
          ? Object.values(err.response?.data)[0]
          : null;

      setError(
        detail ||
          (Array.isArray(firstError) ? firstError[0] : firstError) ||
          "Ошибка регистрации"
      );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md">
      <input
        type="text"
        name="username"
        placeholder="Имя пользователя"
        value={form.username}
        onChange={handleChange}
        required
        className="border px-3 py-2 rounded"
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={form.email}
        onChange={handleChange}
        required
        className="border px-3 py-2 rounded"
      />
      <input
        type="password"
        name="password"
        placeholder="Пароль"
        value={form.password}
        onChange={handleChange}
        required
        className="border px-3 py-2 rounded"
      />
      <input
        type="password"
        name="passwordConfirm"
        placeholder="Подтверждение пароля"
        value={form.passwordConfirm}
        onChange={handleChange}
        required
        className="border px-3 py-2 rounded"
      />

      {strength && (
        <div
          className={`text-sm ${
            strength === "strong"
              ? "text-green-600"
              : strength === "medium"
              ? "text-yellow-600"
              : "text-red-600"
          }`}
        >
          Пароль должен содержать минимум 8 символов, заглавные и строчные буквы, цифры и спецсимволы.
          <div>
            Надёжность пароля:{" "}
            {strength === "strong"
              ? "Высокая"
              : strength === "medium"
              ? "Средняя"
              : "Низкая"}
          </div>
        </div>
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <button
        type="submit"
        className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
      >
        Зарегистрироваться
      </button>
    </form>
  );
}
