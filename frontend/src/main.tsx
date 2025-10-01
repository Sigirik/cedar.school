// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import AppRouter from './AppRouter';
import axios from "axios";
import { AuthProvider } from "@/hooks/AuthContext";
import { Toaster } from "sonner"


// ✅ Настройка глобального axios для работы с Session + CSRF
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <AppRouter />
      <Toaster richColors position="top-right" />
    </AuthProvider>
  </StrictMode>,
);
