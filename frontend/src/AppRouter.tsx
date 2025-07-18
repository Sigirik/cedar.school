import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ActiveTemplateWeekView from './components/ActiveTemplateWeekView';
import TemplateWeekEditor from './components/TemplateWeekEditor';

const AppRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/template-week" />} />
        <Route path="/template-week" element={<ActiveTemplateWeekView />} />
        <Route path="/template-week/draft/edit/:draftId" element={<TemplateWeekEditor />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;