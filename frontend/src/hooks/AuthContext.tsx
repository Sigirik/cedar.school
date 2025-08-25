// frontend/src/hooks/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from "react";
import axios from "axios";
import { api, ACCESS_KEY, REFRESH_KEY } from "@/api/http";

type User = {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  role?: string | null;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  refreshMe: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = async () => {
    try {
      const res = await api.get("/auth/users/me/");
      setUser(res.data);
    } catch {
      setUser(null);
    }
  };

  const login = async (username: string, password: string) => {
    const { data } = await axios.post(`${(api.defaults.baseURL as string)}/auth/jwt/create/`, {
      username,
      password,
    });
    localStorage.setItem(ACCESS_KEY, data.access);
    localStorage.setItem(REFRESH_KEY, data.refresh);
    await refreshMe();
  };

  const logout = async () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setUser(null);
  };

  useEffect(() => {
    (async () => {
      try {
        const access = localStorage.getItem(ACCESS_KEY);
        if (!access) {
          setUser(null);
          return;
        }
        await refreshMe();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
