// frontend/src/components/routing/RoleBasedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/AuthContext';

type Role = 'STUDENT' | 'TEACHER' | 'HEAD_TEACHER' | 'DIRECTOR' | 'ADMIN';

type Props = {
  allowedRoles: Role[];           // пример: ["DIRECTOR", "HEAD_TEACHER"]
  fallback?: string;              // куда редиректить при запрете
  children: React.ReactNode;
};

const RoleBasedRoute: React.FC<Props> = ({ allowedRoles, fallback = '/forbidden', children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <div className="p-4 text-gray-500 text-sm">Загрузка…</div>;
  if (!user)   return <Navigate to="/login" replace state={{ from: location }} />;

  // ADMIN — супердоступ: пропускаем всегда
  if ((user.role as Role) === 'ADMIN') return <>{children}</>;

  // без роли — просим оформить только там, где это уместно
  if (!user.role) {
    return <Navigate to="/request-role" replace state={{ from: location }} />;
  }

  // есть роль, но нет доступа → страница «Недостаточно прав»
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role as Role)) {
    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
};

export default RoleBasedRoute;
export { RoleBasedRoute };
