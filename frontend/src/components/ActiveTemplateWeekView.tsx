// Загружает активную шаблонную неделю через API GET /api/template/template-week/active/
// Подтягивает справочники: предметы, классы, учителя, нормы, доступность учителей
// Формирует preparedLessons с названиями, статусами (ok, under, over) и передаёт их в WeekViewSwitcher
// Используется только для просмотра, без редактирования

import React, { useEffect, useState } from "react";
import axios from "axios";
import WeekViewSwitcher from './WeekViewSwitcher';

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
        const teachers = teachersRes.data.map((t: any) => ({
          ...t,
          full_name: `${t.last_name} ${t.first_name}`,
        }));

        const availability = availabilityRes.data || [];

        setSubjects(subjects);
        setGrades(grades);
        setTeachers(teachers);
        setWeeklyNorms(norms);
        setAvailability(availability);

        const getName = (id: number, list: any[], field = 'name') => list.find(i => i.id === id)?.[field] || `ID ${id}`;

        const countMap: Record<string, number> = {};
        lessons.forEach(l => {
          const key = `${l.grade}-${l.subject}-${l.type}`;
          countMap[key] = (countMap[key] || 0) + 1;
        });

        const prepared = lessons.map(l => {
          const norm = norms.find(n => n.grade === l.grade && n.subject === l.subject);
          const count = countMap[`${l.grade}-${l.subject}-${l.type || 'lesson'}`] || 0;
          let status = '';
          if (norm) {
            const target = (l.type === 'course') ? norm.courses_per_week : norm.lessons_per_week;
            if (count > target) status = 'over';
            else if (count < target) status = 'under';
            else status = 'ok';
          }

          return {
            ...l,
            start_time: l.start_time.slice(0, 5),
            subject_name: getName(l.subject, subjects),
            grade_name: getName(l.grade, grades),
            teacher_name: getName(l.teacher, teachers, 'full_name'),
            status
          };
        });

        setPreparedLessons(prepared);
      } catch (e) {
        console.warn("\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u0434\u0430\u043d\u043d\u044b\u0445:", e);
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
