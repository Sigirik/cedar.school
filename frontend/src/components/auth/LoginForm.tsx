// frontend/src/components/auth/LoginForm.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/AuthContext";
import { Card, Typography, Input, Button, Alert, Space } from "antd";

const { Title, Text } = Typography;

export default function LoginForm() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const [loginOrEmail, setLoginOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleLogin() {
    setError("");

    try {
      await login(loginOrEmail, password);
      navigate("/schedule");

      // простая маршрутизация по роли
      // switch (user?.role) {
      //   case "STUDENT":
      //   case "TEACHER":
      //     navigate("/dashboard");
      //     break;
      //   case "HEAD_TEACHER":
      //   case "DIRECTOR":
      //   case "ADMIN":
      //     navigate("/admin/role-requests");
      //     break;
      //   default:
      //     navigate("/dashboard");
      // }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.non_field_errors?.[0] ||
        "Ошибка входа. Проверьте логин/e-mail и пароль.";
      setError(msg);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Enter" && !loading && loginOrEmail && password) {
      void handleLogin();
    }
  }

  return (
    <div
      onKeyDown={onKeyDown}
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f5f5",
        padding: 16,
      }}
    >
      <Card style={{ width: 360 }}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Title level={4} style={{ textAlign: "center", marginBottom: 0 }}>
            Вход
          </Title>

          <div>
            <Text type="secondary">Логин или e-mail</Text>
            <Input
              size="large"
              placeholder="ivanov или ivanov@site.com"
              value={loginOrEmail}
              onChange={(e) => setLoginOrEmail(e.target.value)}
              autoComplete="username"
              allowClear
            />
          </div>

          <div>
            <Text type="secondary">Пароль</Text>
            <Input.Password
              size="large"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          {error && <Alert type="error" message={error} showIcon />}

          <Button
            type="primary"
            size="large"
            block
            onClick={handleLogin}
            loading={loading}
            disabled={!loginOrEmail || !password}
          >
            {loading ? "Входим…" : "Войти"}
          </Button>

          <Button
            type="default"
            size="large"
            block
            onClick={() => navigate("/register")}
          >
            Зарегистрироваться
          </Button>
        </Space>
      </Card>
    </div>
  );
}
