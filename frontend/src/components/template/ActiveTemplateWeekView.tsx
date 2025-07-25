// Загружает активную шаблонную неделю через API GET /api/template/template-week/active/
// Подтягивает справочники: предметы, классы, учителя, нормы, доступность учителей
// Формирует preparedLessons с названиями, статусами (ok, under, over) и передаёт их в WeekViewSwitcher
// Используется только для просмотра, без редактирования

// ActiveTemplateWeekView.tsx

import React, { useEffect, useState } from "react";
import axios from "axios";
import WeekViewSwitcher from '../calendar/WeekViewSwitcher';
import { prepareLessons } from '../utils/prepareLessons';

const ActiveTemplateWeekView: React.FC = () => {
  const [preparedLessons, setPreparedLessons] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);
  const [availability, setAvailability] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [weekRes, subjectsRes, gradesRes, teachersRes, normsRes, availabilityRes] = await Promise.all([
          axios.get("/api/template/template-week/active/"),
          axios.get("/api/ktp/subjects/"),
          axios.get("/api/ktp/grades/"),
          axios.get("/api/ktp/teachers/"),
          axios.get("/api/ktp/weekly-norms/"),
          axios.get("/api/template/teacher-availability/")
        ]);

        const lessons = weekRes.data.lessons || [];
        const subjects = subjectsRes.data;
        const grades = gradesRes.data;
        const norms = normsRes.data;
        const teachers = teachersRes.data;
        const availability = availabilityRes.data || [];

        setSubjects(subjects);
        setGrades(grades);
        setTeachers(teachers);
        setWeeklyNorms(norms);
        setAvailability(availability);

        const prepared = prepareLessons(lessons, subjects, grades, teachers, norms);
        setPreparedLessons(prepared);
      } catch (e) {
        console.warn("Ошибка загрузки данных:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleRedirectToEditor = () => {
    window.location.href = "/template-week/draft/edit/";
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Активная шаблонная неделя</h1>

      <button
        className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 mb-4"
        onClick={handleRedirectToEditor}
      >
        ✏️ Редактировать шаблон
      </button>

      {loading ? (
        <p className="text-gray-400">Загрузка…</p>
      ) : preparedLessons.length === 0 ? (
        <p className="text-gray-500">Нет уроков в активной неделе.</p>
      ) : (
        <WeekViewSwitcher
          source="active"
          lessons={preparedLessons}
          subjects={subjects}
          grades={grades}
          teachers={teachers}
          weeklyNorms={weeklyNorms}
          teacherAvailability={availability}
        />
      )}
    </div>
  );
};

export default ActiveTemplateWeekView;