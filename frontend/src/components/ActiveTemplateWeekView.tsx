import React, { useEffect, useState } from "react";
import axios from "axios";
import WeekViewSwitcher from './WeekViewSwitcher';

const ActiveTemplateWeekView: React.FC = () => {
  const [activeWeek, setActiveWeek] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const weekRes = await axios.get("/api/template/template-week/active/");
        setActiveWeek(weekRes.data);
      } catch (err) {
        console.warn("Нет активной недели или ошибка:", err);
        setActiveWeek(null);
      }

      try {
        const [subjectsRes, gradesRes, teachersRes, normsRes] = await Promise.all([
          axios.get("/api/ktp/subjects/"),
          axios.get("/api/ktp/grades/"),
          axios.get("/api/ktp/teachers/"),
          axios.get("/api/ktp/weekly-norms/")
        ]);

        setSubjects(subjectsRes.data);
        setGrades(gradesRes.data);
        setTeachers(teachersRes.data);
        setWeeklyNorms(normsRes.data);

        console.log("🎯 Справочники загружены:", {
          subjects: subjectsRes.data,
          grades: gradesRes.data,
          teachers: teachersRes.data
        });
      } catch (err) {
        console.error("Ошибка загрузки справочников:", err);
      }
    }

    fetchData();
  }, []);

  const weekdayLabel = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  const getSubjectName = (id: number) => subjects.find(s => s.id === id)?.name || id;
  const getGradeName = (id: number) => grades.find(g => g.id === id)?.name || id;
  const getTeacherName = (id: number) => teachers.find(t => t.id === id)?.username || id;

  const getNorm = (gradeId: number, subjectId: number) => {
    return weeklyNorms.find(norm =>
      Number(norm.grade) === Number(gradeId) &&
      Number(norm.subject) === Number(subjectId)
    );
  };

  const countLessons = (gradeId: number, subjectId: number) => {
    return (activeWeek?.lessons || []).filter(
      l => l.grade === gradeId && l.subject === subjectId
    ).length;
  };

  const handleRedirectToEditor = () => {
    window.location.href = "/template-week/draft/edit/";
  };

  const activeLessons = activeWeek?.lessons || [];

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Активная шаблонная неделя</h1>

      {activeWeek ? (
        <div className="mb-6">
          <h2 className="text-lg font-semibold flex items-center mb-2">
            <span className="text-green-600 text-xl mr-2">🟩</span>
            Активная неделя
          </h2>
          <button
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
            onClick={handleRedirectToEditor}
          >
            ✏️ Редактировать шаблон
          </button>

          {activeLessons.length > 0 ? (
            <table className="table-auto w-full border text-sm mt-4">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border px-2">Предмет</th>
                  <th className="border px-2">Класс</th>
                  <th className="border px-2">Учитель</th>
                  <th className="border px-2">День</th>
                  <th className="border px-2">Время</th>
                  <th className="border px-2">Длительность</th>
                </tr>
              </thead>
              <tbody>
                {activeLessons.map((lesson: any) => {
                  const norm = getNorm(lesson.grade, lesson.subject);
                  const lessonCount = countLessons(lesson.grade, lesson.subject);

                  const rowClass = norm
                    ? lessonCount > norm.lessons_per_week
                      ? "bg-red-200"
                      : lessonCount < norm.lessons_per_week
                      ? "bg-yellow-200"
                      : ""
                    : "";

                  return (
                    <tr key={lesson.id} className={rowClass}>
                      <td
                        className="border px-2"
                        title={
                          norm
                            ? `План: ${norm.hours_per_week} ч/нед (уроков: ${norm.lessons_per_week}, курсов: ${norm.courses_per_week})`
                            : "Нет нормы"
                        }
                      >
                        {getSubjectName(lesson.subject)}
                      </td>
                      <td className="border px-2">{getGradeName(lesson.grade)}</td>
                      <td className="border px-2">{getTeacherName(lesson.teacher)}</td>
                      <td className="border px-2">{weekdayLabel[lesson.day_of_week]}</td>
                      <td className="border px-2">{lesson.start_time}</td>
                      <td className="border px-2">{lesson.duration_minutes}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 mt-2">Нет уроков в активной неделе.</p>
          )}

          {subjects.length && grades.length && teachers.length ? (
            <WeekViewSwitcher
              source="active"
              subjects={subjects}
              grades={grades}
              teachers={teachers}
            />
          ) : (
            <p className="text-gray-400 mt-4">Загрузка представлений…</p>
          )}
        </div>
      ) : (
        <p className="text-gray-500">Нет активной недели.</p>
      )}
    </div>
  );
};

export default ActiveTemplateWeekView;
