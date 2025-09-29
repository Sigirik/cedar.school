import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
// If your project keeps AuthContext elsewhere, adjust the import below.
// The page works even if the context/provider is temporarily absent.
import { useAuth } from "@/hooks/AuthContext";
import { Role, roleToLabel } from "@/components/routing/RoleBasedRoute.tsx";

const isScheduleRole = (role?: Role | null) => {
  if (!role) return false;
  const r = String(role).toUpperCase();
  return r === "TEACHER" || r === "STUDENT" || r === "PARENT";
};

// A teeny skeleton without CSS frameworks
const Skeleton: React.FC = () => (
  <div
    role="status"
    aria-busy="true"
    style={{
      display: "grid",
      gap: 12,
      maxWidth: 560,
      margin: "8vh auto",
      padding: 24,
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
      background: "white",
    }}
  >
    <div style={{ height: 28, width: "60%", background: "#f3f4f6", borderRadius: 8 }} />
    <div style={{ height: 16, width: "90%", background: "#f3f4f6", borderRadius: 6 }} />
    <div style={{ height: 16, width: "75%", background: "#f3f4f6", borderRadius: 6 }} />
    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
      <div style={{ height: 36, width: 120, background: "#f3f4f6", borderRadius: 10 }} />
      <div style={{ height: 36, width: 160, background: "#f3f4f6", borderRadius: 10 }} />
    </div>
  </div>
);

const Card: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      maxWidth: 640,
      margin: "8vh auto",
      padding: 24,
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
      background: "white",
    }}
  >
    {children}
  </div>
);

const ButtonLink: React.FC<{ to: string; children: React.ReactNode; variant?: "solid" | "ghost" }>
  = ({ to, children, variant = "solid" }) => (
  <Link
    to={to}
    style={{
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      height: 40,
      padding: "0 14px",
      borderRadius: 10,
      textDecoration: "none",
      border: variant === "ghost" ? "1px solid #e5e7eb" : "1px solid transparent",
      background: variant === "ghost" ? "transparent" : "#111827",
      color: variant === "ghost" ? "#111827" : "#fff",
      fontWeight: 600,
    }}
  >
    {children}
  </Link>
);

const ForbiddenPage: React.FC = () => {
  const { user } = useAuth();

  const roleFromContext: Role | undefined = user?.role;

  const [role, setRole] = useState<Role | null>(roleFromContext ?? null);
  const [loading, setLoading] = useState<boolean>(!role || true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (role) {
      setLoading(false);
      return;
    }

    let aborted = false;

    const fetchRole = async () => {
      try {
        setLoading(true);
        setError(null);
        // NOTE: we intentionally avoid extra deps; this will work for cookie-based auth
        // and also for JWT if your global fetch/axios interceptors add the Authorization header.
        const res = await fetch("/api/users/me/");
        if (!res.ok) {
          setLoading(false);
          // 401/403 → we still render the generic message below
          return;
        }
        const data = await res.json();
        if (!aborted) {
          setRole(data?.role ?? null);
        }
      } catch (e) {
        if (!aborted) setError("Не удалось получить текущую роль.");
      } finally {
        if (!aborted) setLoading(false);
      }
    };

    fetchRole();
    return () => {
      aborted = true;
    };
  }, [role]);

  const scheduleVisible = useMemo(() => isScheduleRole(role), [role]);

  if (loading) return <Skeleton />;

  return (
    <Card>
      <h1 style={{ fontSize: 28, fontWeight: 750, marginBottom: 8 }}>Доступ запрещён</h1>
      <p style={{ fontSize: 16, color: "#374151", margin: 0 }}>
        Страница недоступна для роли {roleToLabel(role)}.
      </p>
      {error && (
        <p style={{ color: "#b91c1c", marginTop: 8 }}>{error}</p>
      )}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
        <ButtonLink to="/">На главную</ButtonLink>
        {scheduleVisible && <ButtonLink to="/schedule" variant="ghost">Моё расписание</ButtonLink>}
        <ButtonLink to="/request-role" variant="ghost">Запросить расширение прав</ButtonLink>
      </div>

      <div style={{ marginTop: 18, fontSize: 13, color: "#6b7280" }}>
        Если вы считаете, что это ошибка, свяжитесь с администратором.
      </div>
    </Card>
  );
};

export default ForbiddenPage;
