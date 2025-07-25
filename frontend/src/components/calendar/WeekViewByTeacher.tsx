// WeekViewByTeacher.tsx
// 👩‍🏫 Отображает расписание по учителям через FullCalendarTemplateView
// 📆 Отображает только дни ПН–ПТ (2025-07-07 — 2025-07-11)
// 🎨 Цвет по статусу норм: светло-красный — over, жёлтый — under, светло-зелёный — ok
// 🟦 Добавляет фоновую заливку доступности учителя через prop teacherAvailability
// 👓 Отдельный FullCalendar для каждого учителя
// ⛔ Без drag-n-drop в активной неделе

import React from 'react';
import FullCalendarTemplateView from './FullCalendarTemplateView';

interface Lesson {
  id: number;
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
  subject_name?: string;
  grade_name?: string;
  teacher_name?: string;
  type_label?: string;
  type_color?: string;
  status?: string;
}

interface TeacherAvailability {
  teacher: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

const weekdayMap = [
  '2025-07-07', // Пн
  '2025-07-08',
  '2025-07-09',
  '2025-07-10',
  '2025-07-11', // Пт
];

const statusColorMap: Record<string, string> = {
  over: '#fecaca',
  under: '#fef08a',
  ok: '#bbf7d0'
};

const WeekViewByTeacher: React.FC<{
  lessons: Lesson[];
  teacherAvailability?: TeacherAvailability[];
  source?: 'draft' | 'active';
}> = ({ lessons, teacherAvailability = [], source = 'active' }) => {
  if (!lessons || lessons.length === 0) return <p className="text-gray-500">Нет уроков</p>;

  const teacherIds = [...new Set(lessons.map(l => l.teacher))];

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Расписание по учителям</h2>
      {teacherIds.map((teacherId) => {
        const teacherLessons = lessons.filter(l => l.teacher === teacherId);
        const teacherName = teacherLessons[0]?.teacher_name || `Учитель ${teacherId}`;

        const lessonEvents = teacherLessons.map((l) => {
          const baseDate = weekdayMap[l.day_of_week];
          const safeTime = l.start_time.slice(0, 5);
          const [hour, minute] = safeTime.split(':').map(Number);
          const startDate = new Date(`${baseDate}T00:00`);
          startDate.setHours(hour);
          startDate.setMinutes(minute);
          const endDate = new Date(startDate.getTime() + l.duration_minutes * 60000);

          const start = startDate.toISOString();
          const end = endDate.toISOString();

          const emoji = l.type === 'course' ? '📗' : '📘';

          return {
            id: `lesson-${l.id}`,
            title: `${l.start_time} · ${l.duration_minutes} мин\n${emoji} ${l.subject_name}\n🏫 ${l.grade_name}`,
            start,
            end,
            backgroundColor: statusColorMap[l.status || 'ok'],
            textColor: '#111827',
            borderColor: 'transparent',
            display: 'block',
            extendedProps: {
              status: l.status,
              durationMin: l.duration_minutes,
            }
          };
        });

        const availabilityEvents = teacherAvailability
          .filter(a => a.teacher === teacherId)
          .map((a, idx) => {
            const dayIndex = (a.day_of_week + 6) % 7;  // 👈 теперь "0" — Пн
            const baseDate = weekdayMap[dayIndex];

            const cleanStart = a.start_time.slice(0, 5);
            const cleanEnd = a.end_time.slice(0, 5);
            const start = `${baseDate}T${cleanStart}`;
            const end = `${baseDate}T${cleanEnd}`;

            const entry = {
              id: `availability-${teacherId}-${idx}`,
              start,
              end,
              display: 'background',
              backgroundColor: '#dbeafe'
            };

            return entry;
          });

            const testBackground = {
              id: `test-bg-${teacherId}`,
              start: '2025-07-08T10:00:00',  // вторник
              end: '2025-07-08T12:00:00',
              display: 'background',
              backgroundColor: '#93c5fd'  // голубой
            };


            const events = [...lessonEvents, ...availabilityEvents];;

        return (
          <div key={teacherId} className="mb-8">
            <h3 className="text-md font-bold mb-2">👩‍🏫 {teacherName}</h3>
            <FullCalendarTemplateView
              events={events}
              editable={source === 'draft'}
              onEventClick={(info) => console.log("👆 Клик (учитель):", info.event)}
              onEventDrop={(info) => console.log("📦 Перемещение (учитель):", info.event)}
              onEventResize={(info) => console.log("📏 Растяжение (учитель):", info.event)}
            />
          </div>
        );
      })}
    </div>
  );
};

export default WeekViewByTeacher;
