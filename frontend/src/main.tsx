import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import AppRouter from './AppRouter';
import axios from "axios";
import LoginForm from './components/auth/LoginForm';

// ✅ Настройка глобального axios для работы с Session + CSRF
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LoginForm>
      <AppRouter />
    </LoginForm>
  </StrictMode>,
);
