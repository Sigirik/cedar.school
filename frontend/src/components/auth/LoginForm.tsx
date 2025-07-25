import React, { useEffect, useState } from "react";
import axios from "axios";

interface LoginFormProps {
  children: React.ReactNode;
}

const LoginForm: React.FC<LoginFormProps> = ({ children }) => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Пингуем сервер, чтобы проверить сессию
    axios
      .get("/api/template/template-week/active/")
      .then(() => setLoggedIn(true))
      .catch(() => setLoggedIn(false));
  }, []);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError("");
      await axios.post(
        "/api-auth/login/",
        new URLSearchParams({
          username,
          password,
        }),
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          withCredentials: true,
        }
      );
      setLoggedIn(true);
    } catch (err) {
      setError("Ошибка входа. Проверьте логин и пароль.");
    } finally {
      setLoading(false);
    }
  };

  if (loggedIn) return <>{children}</>;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-6 rounded shadow w-full max-w-sm">
        <h2 className="text-xl font-semibold mb-4">Вход</h2>
        <input
          type="text"
          placeholder="Логин"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="border rounded w-full px-3 py-2 mb-3"
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="border rounded w-full px-3 py-2 mb-4"
        />
        {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded w-full"
        >
          {loading ? "Вход..." : "Войти"}
        </button>
      </div>
    </div>
  );
};

export default LoginForm;
