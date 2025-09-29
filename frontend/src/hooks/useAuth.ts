import { useState, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, fetchMe } from "../api/auth";

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function login(loginOrEmail: string, password: string) {
    await apiLogin(loginOrEmail, password);
    const me = await fetchMe();
    setUser(me);
    return me;
  }

  async function logout() {
    await apiLogout();
    setUser(null);
  }

  useEffect(() => {
    (async () => {
      try {
        if (localStorage.getItem("access")) {
          const me = await fetchMe();
          setUser(me);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return { user, loading, login, logout };
}
