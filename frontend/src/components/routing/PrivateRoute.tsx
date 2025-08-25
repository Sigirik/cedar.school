// frontend/src/components/routing/PrivateRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/AuthContext';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return null;               // или спиннер
  if (!user) return <Navigate to="/login" replace />;

  return <>{children}</>;
};

export default PrivateRoute;

