import { useEffect, useMemo, useState } from 'react';
import api, { ACCESS_KEY, REFRESH_KEY } from '@/api/axios';

function decodeJwt(token: string) {
  try {
    const [, payload] = token.split('.');
    const pad = (s: string) => s + '='.repeat((4 - (s.length % 4)) % 4);
    const json = atob(pad(payload).replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export default function AuthDebugPage() {
  const [me, setMe] = useState<any>(null);
  const [meCode, setMeCode] = useState<number | null>(null);
  const [meErr, setMeErr] = useState<string>('');

  const access = localStorage.getItem(ACCESS_KEY) || '';
  const refresh = localStorage.getItem(REFRESH_KEY) || '';

  const accessPayload = useMemo(() => (access ? decodeJwt(access) : null), [access]);
  const refreshPayload = useMemo(() => (refresh ? decodeJwt(refresh) : null), [refresh]);

  const cookies = useMemo(() => document.cookie, []);

  const reload = async () => {
    setMe(null);
    setMeErr('');
    setMeCode(null);
    try {
      const res = await api.get('/api/auth/users/me/');
      setMeCode(res.status);
      setMe(res.data);
    } catch (e: any) {
      setMeCode(e?.response?.status || null);
      setMeErr(e?.response?.data?.detail || 'Ошибка запроса');
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const fmt = (ts?: number) => (ts ? new Date(ts * 1000).toLocaleString() : '—');
  const last4 = (s: string) => (s.length > 8 ? `…${s.slice(-8)}` : s);

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-3">Отладка авторизации</h2>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="border rounded p-3">
          <h3 className="font-medium mb-2">Токены (frontend)</h3>
          <div className="text-sm">
            <div>Access: {access ? last4(access) : <span className="text-red-600">нет</span>}</div>
            {accessPayload && (
              <ul className="ml-4 list-disc">
                <li>user_id: {accessPayload.user_id ?? '—'}</li>
                <li>exp: {fmt(accessPayload.exp)} ({accessPayload.exp})</li>
                <li>token_type: {accessPayload.token_type ?? '—'}</li>
              </ul>
            )}
            <div className="mt-2">Refresh: {refresh ? last4(refresh) : <span className="text-red-600">нет</span>}</div>
            {refreshPayload && (
              <ul className="ml-4 list-disc">
                <li>exp: {fmt(refreshPayload.exp)} ({refreshPayload.exp})</li>
              </ul>
            )}
          </div>
        </div>

        <div className="border rounded p-3">
          <h3 className="font-medium mb-2">/api/auth/users/me/ (backend)</h3>
          <div className="text-sm mb-2">HTTP: {meCode ?? '—'}</div>
          {me ? (
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">{JSON.stringify(me, null, 2)}</pre>
          ) : (
            <div className="text-sm text-gray-600">{meErr || '—'}</div>
          )}
          <button
            onClick={reload}
            className="mt-2 text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded"
          >
            Обновить
          </button>
        </div>

        <div className="border rounded p-3">
          <h3 className="font-medium mb-2">Cookies (браузер)</h3>
          <div className="text-xs break-all">{cookies || '—'}</div>
          <p className="text-xs text-gray-500 mt-2">
            Наличие <code>sessionid</code> означает, что вы вошли в /admin/ (Django Admin сессия).
            JWT к админке не относится.
          </p>
        </div>

        <div className="border rounded p-3">
          <h3 className="font-medium mb-2">Быстрые действия</h3>
          <div className="flex flex-wrap gap-2">
            <a
              href="/admin/"
              target="_blank"
              rel="noreferrer"
              className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded"
            >
              Открыть админку
            </a>
            <button
              onClick={() => {
                localStorage.removeItem(ACCESS_KEY);
                localStorage.removeItem(REFRESH_KEY);
                window.location.reload();
              }}
              className="text-sm bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded"
            >
              Сбросить токены (logout)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
