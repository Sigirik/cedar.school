// frontend/src/components/layout/AppHeader.tsx
import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/AuthContext';
import { api } from '@/api/http';
import { Button } from 'antd';

const ROLE_RU: Record<string, string> = {
  STUDENT: 'Ученик',
  PARENT: 'Родитель',
  TEACHER: 'Учитель',
  HEAD_TEACHER: 'Завуч',
  DIRECTOR: 'Директор',
  ADMIN: 'Администратор',
  AUDITOR: 'Аудитор',
};

const AppHeader: React.FC = () => {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [apiUser, setApiUser] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get('/auth/users/me/');
        if (!mounted) return;
        setApiUser(res.data);
      } catch (e: any) {
        if (!mounted) return;
        setApiUser(null);
      }
    })();
    return () => { mounted = false; };
  }, [location.pathname, user?.id]);

  const displayName =
    (user?.full_name && user.full_name.trim()) ||
    user?.username ||
    (apiUser?.full_name && apiUser.full_name.trim()) ||
    apiUser?.username ||
    '';

  const displayRole = (user?.role ?? apiUser?.role) as string | undefined;

  const handleLogout = async () => {
    try { await (logout?.() ?? Promise.resolve()); }
    finally { navigate('/login'); }
  };

  return (
    <header className="w-full bg-white border-b sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-lg font-semibold">Cedar.school</Link>
          <nav className="hidden md:flex items-center gap-3 text-sm text-gray-700">
            <Link to="/dashboard" className="hover:underline">Дашборд</Link>
            <Link to="/schedule" className="hover:underline">Расписание</Link>
            <Link to="/template-week" className="hover:underline">Шаблон недели</Link>
            <Link to="/ktp" className="hover:underline">КТП</Link>
            <Link to="/admin/role-requests" className="hover:underline">Заявки</Link>
            <Link to="/debug/auth" className="hover:underline text-gray-500">Отладка</Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {loading ? (
            <span className="text-sm text-gray-500">Загрузка…</span>
          ) : displayName ? (
            <>
              <span className="text-sm text-gray-700">
                {displayName}
                {displayRole ? (
                  <span className="text-gray-500"> · {ROLE_RU[displayRole] || displayRole}</span>
                ) : (
                  <span className="text-amber-600"> · роль не назначена</span>
                )}
              </span>
              <Button
                onClick={handleLogout}
                className="px-3 py-1.5"
              >
                Выход
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button type="primary" className="px-3 py-1.5">
                Вход
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default AppHeader;
