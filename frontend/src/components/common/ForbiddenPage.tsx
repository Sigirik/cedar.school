// frontend/src/components/common/ForbiddenPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function ForbiddenPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="p-6 rounded border bg-white shadow max-w-md w-full text-center">
        <h2 className="text-xl font-semibold mb-2">Недостаточно прав</h2>
        <p className="text-gray-600 mb-4">
          Эта страница недоступна для вашей роли.
        </p>
        <Link to="/dashboard" className="text-blue-600 hover:underline">На главную</Link>
      </div>
    </div>
  );
}
