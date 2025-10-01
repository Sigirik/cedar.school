// frontend/src/components/auth/DashboardPage.tsx
import { useEffect, useState } from "react";
import { api } from "@/api/http";

export default function DashboardPage() {
  const [me, setMe] = useState<any>(null);
  const [code, setCode] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/auth/users/me/"); // ВАЖНО: без префикса /api
        setMe(res.data);
        setCode(res.status);
      } catch (e: any) {
        setMe(null);
        setCode(e?.response?.status ?? null);
      }
    })();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-2">Дашборд</h2>
      <div className="text-sm text-gray-600 mb-3">/auth/users/me/ → {code ?? "—"}</div>
      <pre className="bg-gray-50 p-3 rounded border overflow-auto text-xs">
        {me ? JSON.stringify(me, null, 2) : "Не авторизован"}
      </pre>
    </div>
  );
}
