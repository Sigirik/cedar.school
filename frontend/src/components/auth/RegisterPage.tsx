// frontend/src/components/auth/RegisterPage.tsx
import React from "react";
import RegisterForm from "./RegisterForm";

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="bg-white p-6 rounded shadow w-full max-w-md">
        <h2 className="text-2xl font-semibold mb-4">Регистрация</h2>
        <RegisterForm />
      </div>
    </div>
  );
}
