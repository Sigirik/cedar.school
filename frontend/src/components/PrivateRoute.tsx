import type { JSX } from "react";
import { Navigate } from "react-router-dom";

export function PrivateRoute({ children }: { children?: JSX.Element }) {
  const token = localStorage.getItem("access");
  if (!token) return <Navigate to="/login" replace />;
  return children;
}
