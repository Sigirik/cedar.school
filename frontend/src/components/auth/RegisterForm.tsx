import React, { useState } from "react";
import api from "@/api/axios";
import { useNavigate } from "react-router-dom";
import { Card, Typography, Input, Button, Alert, Space } from "antd";

const { Title, Text } = Typography;

export default function RegisterForm() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    passwordConfirm: "",
  });
  const [error, setError] = useState("");
  const [strength, setStrength] = useState<"weak" | "medium" | "strong" | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));

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
      setLoading(true);
      await api.post(
        "/api/auth/users/",
        {
          username: form.username,
          email: form.email,
          password: form.password,
          re_password: form.passwordConfirm,
        },
        {
          headers: { "Content-Type": "application/json" },
        }
      );
      navigate("/login");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const firstError =
        typeof err?.response?.data === "object"
          ? Object.values(err.response.data)[0]
          : null;

      setError(
        detail ||
          (Array.isArray(firstError) ? (firstError as string[])[0] : (firstError as string)) ||
          "Ошибка регистрации"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f5f5",
        padding: 16,
      }}
    >
      <Card style={{ width: 420 }}>
        <form onSubmit={handleSubmit}>
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Title level={3} style={{ textAlign: "center", marginBottom: 0 }}>
              Регистрация
            </Title>

            <div>
              <Text type="secondary">Имя пользователя</Text>
              <Input
                name="username"
                size="large"
                placeholder="Имя пользователя"
                value={form.username}
                onChange={handleChange}
                required
                allowClear
                autoComplete="username"
              />
            </div>

            <div>
              <Text type="secondary">Email</Text>
              <Input
                type="email"
                name="email"
                size="large"
                placeholder="Email"
                value={form.email}
                onChange={handleChange}
                required
                allowClear
                autoComplete="email"
              />
            </div>

            <div>
              <Text type="secondary">Пароль</Text>
              <Input.Password
                name="password"
                size="large"
                placeholder="Пароль"
                value={form.password}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
            </div>

            <div>
              <Text type="secondary">Подтверждение пароля</Text>
              <Input.Password
                name="passwordConfirm"
                size="large"
                placeholder="Подтверждение пароля"
                value={form.passwordConfirm}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
            </div>

            {strength && (
              <Alert
                type={
                  strength === "strong" ? "success" : strength === "medium" ? "warning" : "error"
                }
                showIcon
                message={
                  <div>
                    <div>
                      Пароль должен содержать минимум 8 символов, заглавные и строчные буквы, цифры
                      и спецсимволы.
                    </div>
                    <div style={{ marginTop: 4 }}>
                      Надёжность пароля:{" "}
                      <b>
                        {strength === "strong"
                          ? "Высокая"
                          : strength === "medium"
                          ? "Средняя"
                          : "Низкая"}
                      </b>
                    </div>
                  </div>
                }
              />
            )}

            {error && <Alert type="error" showIcon message={error} />}

            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
            >
              Зарегистрироваться
            </Button>

            {/* Кнопка Войти */}
            <Button
              type="default"
              size="large"
              block
              onClick={() => navigate("/login")}
            >
              Войти
            </Button>
          </Space>
        </form>
      </Card>
    </div>
  );
}
