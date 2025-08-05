import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ActiveTemplateWeekView from './components/template/ActiveTemplateWeekView';
import TemplateWeekEditor from './components/template/TemplateWeekEditor';
import LiveLessonDemo from './features/liveboard/LiveLessonDemo';
import KtpEditor from './components/ktp/KtpEditor';
import AdminReferenceEditor from './components/admin/AdminReferenceEditor';
import AcademicCalendarEditor from "./components/admin/AcademicCalendarEditor";


const AppRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/template-week" />} />
        <Route path="/admin/settings" element={<AdminReferenceEditor />} />
        <Route path="/admin/calendar" element={<AcademicCalendarEditor />} />
        <Route path="/template-week" element={<ActiveTemplateWeekView />} />
        <Route path="/live-demo" element={<LiveLessonDemo />} />
        <Route path="/template-week/draft/edit" element={<TemplateWeekEditor />} />
        <Route path="/ktp" element={<KtpEditor />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;