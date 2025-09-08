import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import ActiveTemplateWeekView from './components/template/ActiveTemplateWeekView';
import TemplateWeekEditor from './components/template/TemplateWeekEditor';
import LiveLessonDemo from './features/liveboard/LiveLessonDemo';
import KtpEditor from './components/ktp/KtpEditor';
import AdminReferenceEditor from './components/admin/AdminReferenceEditor';
import AcademicCalendarEditor from "./components/admin/AcademicCalendarEditor";
import AdminRoleRequestsPage from './components/admin/AdminRoleRequestsPage';
import ForbiddenPage from './components/common/ForbiddenPage';

import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import RoleRequestPage from './components/auth/RoleRequestPage';
import DashboardPage from './components/auth/DashboardPage';
import AuthDebugPage from './components/debug/AuthDebugPage';

import PrivateRoute from './components/routing/PrivateRoute';
import { RoleBasedRoute } from './components/routing/RoleBasedRoute';
import AppHeader from './components/layout/AppHeader';

import LessonPage from './pages/lesson/id';
import SchedulePage from './pages/schedule';

const AppRouter: React.FC = () => {
  return (
    <Router>
      <AppHeader />
      <Routes>
        {/* Публичные маршруты */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/request-role" element={<RoleRequestPage />} />
        <Route path="/forbidden" element={<ForbiddenPage />} />

        {/* Перенаправление на dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" />} />

        {/* Защищённые маршруты */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          }
        />

        <Route
          path="/template-week"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER']}>
              <ActiveTemplateWeekView />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/schedule"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER', 'TEACHER', 'STUDENT']}>
              <SchedulePage />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/lesson/:id"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER', 'TEACHER', 'STUDENT']}>
              <LessonPage />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/template-week/draft/edit"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER']}>
              <TemplateWeekEditor />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/ktp"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER', 'TEACHER']}>
              <KtpEditor />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/live-demo"
          element={
            <PrivateRoute>
              <LiveLessonDemo />
            </PrivateRoute>
          }
        />

        <Route
          path="/admin/settings"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER']}>
              <AdminReferenceEditor />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/admin/calendar"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER']}>
              <AcademicCalendarEditor />
            </RoleBasedRoute>
          }
        />

        <Route
          path="/admin/role-requests"
          element={
            <RoleBasedRoute allowedRoles={['ADMIN', 'DIRECTOR', 'HEAD_TEACHER']}>
              <AdminRoleRequestsPage />
            </RoleBasedRoute>
          }
        />
        <Route path="/debug/auth" element={<AuthDebugPage />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;
