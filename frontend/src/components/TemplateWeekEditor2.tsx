import React, { useEffect, useState } from "react";
import axios from "axios";

type Lesson = {
  id?: number;
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
};

type Draft = {
  id: number;
  base_week: number;
  data: {
    lessons: Lesson[];
  };
};

type ActiveWeek = {
  id: number;
  name: string;
  academic_year: number;
  created_at: string;
  is_active: boolean;
  lessons: Lesson[];
};

const TemplateWeekEditor: React.FC = () => {
  const [draft, setDraft] = useState<Draft | null>(null);
  const [activeWeek, setActiveWeek] = useState<ActiveWeek | null>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [message, setMessage] = useState("");
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const draftRes = await axios.get("/schedule/api/ktp/template-drafts/");
        const draftData = draftRes.data[0];

        if (
          draftData &&
          draftData.data &&
          Array.isArray(draftData.data.lessons)
        ) {
          setDraft(draftData);
        } else {
          console.warn("Черновик без уроков — создаём пустой.");
          setDraft({
            id: 0,
            base_week: 1,
            data: { lessons: [] },
          });
        }
      } catch (err) {
        console.error("Ошибка загрузки черновика:", err);
        setDraft({
          id: 0,
          base_week: 1,
          data: { lessons: [] },
        });
      }

      try {
        const weekRes = await axios.get("/schedule/api/ktp/template-week/active/");
        setActiveWeek(weekRes.data);
      } catch (err) {
        console.warn("Нет активной недели или ошибка:", err);
        setActiveWeek(null);
      }

      try {
          const [subjectsRes, gradesRes, teachersRes, normsRes] = await Promise.all([
            axios.get("/schedule/api/ktp/subjects/"),
            axios.get("/schedule/api/ktp/grades/"),
            axios.get("/schedule/api/ktp/teachers/"),
            axios.get("/schedule/api/ktp/weekly-norms/")
          ]);

          setSubjects(subjectsRes.data);
          setGrades(gradesRes.data);
          setTeachers(teachersRes.data);
          setWeeklyNorms(normsRes.data);

        } catch (err) {
          console.error("Ошибка загрузки справочников:", err);
        }
    }

    fetchData();
  }, []);

const handleEditOptions = async () => {
  if (lessons.length > 0) {
    const confirmReset = window.confirm("Черновик уже содержит уроки. Перезаписать его?");
    if (!confirmReset) return;
  }

  const choice = window.prompt(
    "Что сделать?\n1 — Скопировать из активной недели\n2 — Пустой черновик\n(пока без выбора старых версий)",
    "1"
  );

  try {
    if (choice === "1") {
      const res = await axios.post("/schedule/api/ktp/template-drafts/create-from/" + activeWeek.id + "/");
      setDraft(res.data);
      setLessons(res.data.data.lessons || []);
    } else if (choice === "2") {
      const res = await axios.post("/schedule/api/ktp/template-drafts/create-empty/");
      setDraft(res.data);
      setLessons([]);
    }
  } catch (err) {
    console.error("Ошибка при создании черновика:", err);
    alert("Ошибка при создании черновика");
  }
};

  const getNorm = (gradeId: number, subjectId: number) => {
      return weeklyNorms.find(norm =>
        Number(norm.grade) === Number(gradeId) &&
        Number(norm.subject) === Number(subjectId)
      );
  };
  const lessons = draft?.data?.lessons ?? [];
  const activeLessons = activeWeek?.lessons ?? [];

  const getSubjectName = (id: number) => subjects.find(s => s.id === id)?.name || id;
  const getGradeName = (id: number) => grades.find(g => g.id === id)?.name || id;
  const getTeacherName = (id: number) => teachers.find(t => t.id === id)?.username || id;

  const handleLessonChange = (index: number, field: keyof Lesson, value: any) => {
    if (!draft) return;
    const updated = { ...draft };
    updated.data.lessons[index][field] = value;
    setDraft(updated);
  };

  const handleAddLesson = () => {
    if (!draft) return;
    const updated = { ...draft };
    updated.data.lessons.push({
      subject: subjects[0]?.id || 1,
      grade: grades[0]?.id || 1,
      teacher: teachers[0]?.id || 1,
      day_of_week: 0,
      start_time: "08:30:00",
      duration_minutes: 40,
    });
    setDraft(updated);
  };

    const handleDeleteLesson = (index: number) => {
      if (!draft) return;
      const updated = { ...draft };
      updated.data.lessons.splice(index, 1);
      setDraft(updated);
    };

  const saveDraft = () => {
    if (!draft) return;
    const method = draft.id === 0 ? axios.post : axios.put;
    const url = draft.id === 0
      ? "/schedule/api/ktp/template-drafts/"
      : `/schedule/api/ktp/template-drafts/${draft.id}/`;

    method(url, {
      base_week: draft.base_week,
      data: draft.data
    }).then(res => {
      setDraft(res.data);
      setMessage("✔ Черновик сохранён.");
    });
  };

  const commitDraft = () => {
    if (!draft || draft.id === 0) return;
    axios.post(`/schedule/api/ktp/template-drafts/${draft.id}/commit/`).then(() => {
      setMessage("🚀 Создана новая активная версия.");
    });
  };

const weekdayLabel = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const countLessons = (gradeId: number, subjectId: number) => {
  return activeLessons.filter(
    l => l.grade === gradeId && l.subject === subjectId
  ).length;
};

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Редактирование шаблонной недели</h1>
      {message && <p className="mb-4 text-green-700">{message}</p>}

      {activeWeek ? (
        <div className="mb-6">
          <h2 className="text-lg font-semibold flex items-center mb-2">
            <span className="text-green-600 text-xl mr-2">🟩</span>
            Активная неделя
          </h2>
          <button
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
            onClick={handleEditOptions}
          >
            ✏️ Редактировать шаблон
          </button>
          {activeLessons.length > 0 ? (
            <table className="table-auto w-full border text-sm">
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
                  {activeLessons.map((lesson) => {
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
            <p className="text-gray-500">Нет уроков в активной неделе.</p>
          )}
        </div>
      ) : (
        <p className="text-gray-500">Нет активной недели.</p>
      )}

      <h2 className="text-lg font-semibold mb-2">✏️ Черновик</h2>
      {lessons.length > 0 ? (
        <table className="table-auto w-full text-sm mb-4">
          <thead>
            <tr><th>Предмет</th><th>Класс</th><th>Учитель</th><th>День</th><th>Время</th><th>Минуты</th><th></th></tr>
          </thead>
          <tbody>
            {lessons.map((lesson, index) => (
              <tr key={index}>
                <td>
                  <select value={lesson.subject} onChange={(e) => handleLessonChange(index, "subject", parseInt(e.target.value))}>
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </td>
                <td>
                  <select value={lesson.grade} onChange={(e) => handleLessonChange(index, "grade", parseInt(e.target.value))}>
                    {grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </td>
                <td>
                  <select value={lesson.teacher} onChange={(e) => handleLessonChange(index, "teacher", parseInt(e.target.value))}>
                    {teachers.map(t => <option key={t.id} value={t.id}>{t.username}</option>)}
                  </select>
                </td>
                <td><input type="number" value={lesson.day_of_week} onChange={(e) => handleLessonChange(index, "day_of_week", parseInt(e.target.value))} /></td>
                <td><input type="time" value={lesson.start_time} onChange={(e) => handleLessonChange(index, "start_time", e.target.value)} /></td>
                <td><input type="number" value={lesson.duration_minutes} onChange={(e) => handleLessonChange(index, "duration_minutes", parseInt(e.target.value))} /></td>
                <td>
                  <button className="text-red-600 hover:underline" onClick={() => handleDeleteLesson(index)}> 🗑</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : <p className="text-gray-500 mb-4">Нет уроков в черновике.</p>}

      <div className="space-x-2">
        <button className="bg-purple-500 text-white px-3 py-1 rounded" onClick={handleAddLesson}>➕ Урок</button>
        <button className="bg-indigo-500 text-white px-3 py-1 rounded" onClick={saveDraft}>💾 Сохранить черновик</button>
        <button className="bg-pink-500 text-white px-3 py-1 rounded" onClick={commitDraft}>🚀 Создать новую версию</button>
      </div>
    </div>
  );
};

export default TemplateWeekEditor;
