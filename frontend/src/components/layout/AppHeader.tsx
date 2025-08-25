// frontend/src/components/layout/AppHeader.tsx
import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/AuthContext';
import { api, ACCESS_KEY, REFRESH_KEY } from '@/api/http';

const ROLE_RU: Record<string, string> = {
  STUDENT: 'Ученик',
  PARENT: 'Родитель',
  TEACHER: 'Учитель',
  HEAD_TEACHER: 'Завуч',
  DIRECTOR: 'Директор',
  ADMIN: 'Администратор',
  AUDITOR: 'Аудитор',
};

function Pill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`px-2 py-0.5 rounded text-[11px] ${
        ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}
      title={label}
    >
      {label}
    </span>
  );
}

const AppHeader: React.FC = () => {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [apiOk, setApiOk] = useState<boolean>(false);
  const [apiUser, setApiUser] = useState<any>(null);
  const [apiCode, setApiCode] = useState<number | null>(null);

  const hasAccess = !!localStorage.getItem(ACCESS_KEY);
  const hasRefresh = !!localStorage.getItem(REFRESH_KEY);
  const hasSession = useMemo(
    () => document.cookie.split('; ').some((c) => c.startsWith('sessionid=')),
    [location.pathname]
  );
  const hasCsrf = useMemo(
    () => document.cookie.split('; ').some((c) => c.startsWith('csrftoken=')),
    [location.pathname]
  );

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get('/auth/users/me/');
        if (!mounted) return;
        setApiOk(true);
        setApiCode(res.status);
        setApiUser(res.data);
      } catch (e: any) {
        if (!mounted) return;
        setApiOk(false);
        setApiCode(e?.response?.status || null);
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
            <Link to="/template-week" className="hover:underline">Шаблон недели</Link>
            <Link to="/ktp" className="hover:underline">КТП</Link>
            <Link to="/admin/role-requests" className="hover:underline">Заявки</Link>
            <Link to="/debug/auth" className="hover:underline text-gray-500">Отладка</Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1 mr-2">
            <Pill ok={hasAccess} label={hasAccess ? 'FE:access' : 'FE:no token'} />
            <Pill ok={apiOk} label={apiOk ? `API:${apiCode}/${displayRole || '—'}` : `API:${apiCode ?? '—'}`} />
            <Pill ok={hasSession} label={hasSession ? 'Sess:admin' : 'Sess:—'} />
            <Pill ok={hasCsrf} label={hasCsrf ? 'CSRF' : 'no-CSRF'} />
          </div>

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
              <button
                onClick={handleLogout}
                className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded"
              >
                Выход
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded"
            >
              Вход
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default AppHeader;
