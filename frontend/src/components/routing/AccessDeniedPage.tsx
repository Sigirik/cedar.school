import React from "react";
import { Link } from "react-router-dom";

export default function AccessDeniedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white p-8 rounded shadow max-w-md text-center">
        <h1 className="text-2xl font-bold mb-4 text-red-600">Доступ запрещён</h1>
        <p className="text-gray-600 mb-6">
          У вас нет прав для просмотра этой страницы.
        </p>
        <Link
          to="/dashboard"
          className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          На главную
        </Link>
      </div>
    </div>
  );
}
