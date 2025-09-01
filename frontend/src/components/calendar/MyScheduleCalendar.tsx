import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/api/http";
import FullCalendarTemplateView from "@/components/calendar/FullCalendarTemplateView";
import { prepareLessons } from "@/utils/prepareLessons";

type IdOrObj<T extends { id: number }> = number | T;

type BackendLesson = {
  id: number;
  date: string;           // 'YYYY-MM-DD'
  start_time: string;     // 'HH:mm' | 'HH:mm:ss'
  end_time?: string;      // 'HH:mm' | 'HH:mm:ss'
  duration_minutes?: number;
  subject: IdOrObj<{ id: number; name?: string }>;
  grade:   IdOrObj<{ id: number; name?: string }>;
  teacher: IdOrObj<{ id: number; first_name?: string; last_name?: string; middle_name?: string; fio?: string }>;
  title?: string;         // если сервер присылает кастомный заголовок
};

type PreparedLesson = ReturnType<typeof prepareLessons>[number];

const weekdayMap = [
  "2025-07-07", // Пн
  "2025-07-08",
  "2025-07-09",
  "2025-07-10",
  "2025-07-11", // Пт
]; // тот же приём используется в WeekViewByTeacher

const statusColorMap: Record<string, string> = {
  over:  "#fecaca",
  under: "#fef08a",
  ok:    "#bbf7d0",
}; // как в WeekViewByTeacher

function toId(x: any): number {
  if (x == null) return 0;
  if (typeof x === "number") return x;
  if (typeof x === "object" && typeof x.id === "number") return x.id;
  return 0;
}
function hhmm(s?: string) {
  if (!s) return "";
  return s.slice(0, 5);
}
function durationFrom(b: BackendLesson) {
  if (b.duration_minutes) return b.duration_minutes;
  if (b.start_time && b.end_time) {
    const [sh, sm] = hhmm(b.start_time).split(":").map(Number);
    const [eh, em] = hhmm(b.end_time).split(":").map(Number);
    return (eh * 60 + em) - (sh * 60 + sm);
  }
  return 45;
}
function dayOfWeekFromDate(dateISO: string) {
  // сервер даёт реальную дату; нам нужен индекс дня недели 0..4 (Пн..Пт), чтобы вписать в «шаблонную» неделю
  const d = new Date(`${dateISO}T00:00:00`);
  const js = d.getDay();        // Вс=0..Сб=6
  return js === 0 ? -1 : js - 1; // Пн=0..Пт=4
}

export default function MyScheduleView() {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades,   setGrades]   = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [preparedLessons, setPreparedLessons] = useState<PreparedLesson[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const [weekRes, subjectsRes, gradesRes, teachersRes, normsRes, availabilityRes, draftRes] = await Promise.all([
//           api.get("/template/active-week/"),
          api.get("/real_schedule/my/"),
          api.get("/core/subjects/"),
          api.get("/core/grades/"),
          api.get("teachers/"),
          api.get("/core/weekly-norms/"),
          api.get("/core/availabilities/"),
          api.get("/draft/template-drafts/exists/"), // ❗ добавь такой эндпоинт или замени
        ]);
// console.log(weekRes.data.results);
//         const lessons = weekRes.data.results.map((el) => {
//             console.log("el", el)
// //             return eL
//             return {
//                 ...el,
//                 subject: subject.id,
//             }
//         }) || [];
    console.log("lessons", lessons);
        const subjects = subjectsRes.data;
        const grades = gradesRes.data;
        const teachers = teachersRes.data;
        const availability = availabilityRes.data || [];

        const norms = normsRes.data.map((n: any) => ({
          ...n,
          subject: typeof n.subject === 'object' ? n.subject.id : n.subject,
          grade: typeof n.grade === 'object' ? n.grade.id : n.grade,
        }));

//         setSubjects(subjects);
//         setGrades(grades);
//         setTeachers(teachers);
//         setWeeklyNorms(norms);
//         setAvailability(availability);
//         setHasDraft(draftRes.data.exists || false);
//         setTemplateId(weekRes.data.id || weekRes.data.template?.id || null);

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

  // 4) строим events для FullCalendarTemplateView — по образцу WeekViewByTeacher
  const events = useMemo(() => {
    return preparedLessons.map((l) => {
      const baseDate = weekdayMap[l.day_of_week];                 // «фиктивная» неделя шаблона
      const [h, m] = l.start_time.split(":").map(Number);
      const startDate = new Date(`${baseDate}T00:00`);
      startDate.setHours(h);
      startDate.setMinutes(m);
      const endDate = new Date(startDate.getTime() + l.duration_minutes * 60000);

      const start = startDate.toISOString();
      const end   = endDate.toISOString();

      // ⚠ FullCalendarTemplateView сам рисует первую строку (время · длительность),
      // а 2-я и 3-я строки берутся из title.split('\n')[1] и [2].
      const primary = l.title?.trim?.() || `${l.grade_name} · ${l.subject_name}`;
      const teacherLine = l.teacher_name; // prepareLessons даёт «Фамилия И.О.»

      return {
        id: String(l.id),
        title: `${l.start_time} · ${l.duration_minutes} мин\n${primary}\n${teacherLine}`, // совместимо с шаблоном
        start,
        end,
        backgroundColor: statusColorMap[l.status || "ok"],
        textColor: "#111827",
        borderColor: "transparent",
        display: "block",
        extendedProps: {
          status: l.status,
          durationMin: l.duration_minutes, // нужно для первой строки в шаблоне
        },
      };
    });
  }, [preparedLessons]);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-3">Моё расписание</h1>

      {loading && <p className="text-gray-400">Загрузка…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <FullCalendarTemplateView
          events={events}
          editable={false}           // read-only
          collisionMap={{}}          // подсветка конфликтов не требуется
        />
      )}
    </div>
  );
}
