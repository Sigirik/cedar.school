// 🏢 WeekViewByGrade.tsx
//
// 📋 Отображает расписание по классам через FullCalendarTemplateView
// 🗖 Отображает только дни ПН–ПТ (2025-07-07 — 2025-07-11)
// 🎨 Цвет по статусу норм: светло-красный — over, жёлтый — under, светло-зелёный — ok
// 💏 Отдельный FullCalendar для каждого класса
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

const weekdayMap = [
  '2025-07-07', // Пн
  '2025-07-08',
  '2025-07-09',
  '2025-07-10',
  '2025-07-11', // Пт
];

const statusColorMap: Record<string, string> = {
  over: '#fecaca',       // светло-красный
  under: '#fef08a',      // жёлтый
  ok: '#bbf7d0'          // светло-зелёный
};

const WeekViewByGrade: React.FC<{ lessons: Lesson[]; source?: 'draft' | 'active' }> = ({ lessons, source = 'active' }) => {
  if (!lessons || lessons.length === 0) return <p className="text-gray-500">Нет уроков</p>;

  const gradeIds = [...new Set(lessons.map(l => l.grade))];

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Расписание по классам</h2>
      {gradeIds.map((gradeId) => {
        const gradeLessons = lessons.filter(l => l.grade === gradeId);
        const gradeName = gradeLessons[0]?.grade_name || `Класс ${gradeId}`;

        const events = gradeLessons.map((l, index) => {
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
            id: String(l.id),
            title: `🏫 ${l.grade_name}\n${emoji} ${l.subject_name}\n👩‍🏫 ${l.teacher_name}`,
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

        return (
          <div key={gradeId} className="mb-8">
            <h3 className="text-md font-bold mb-2">🏫 {gradeName}</h3>
            <FullCalendarTemplateView
              events={events}
              editable={source === 'draft'}
              onEventClick={(info) => console.log("👆 Клик (класс):", info.event)}
              onEventDrop={(info) => console.log("📦 Перемещение (класс):", info.event)}
              onEventResize={(info) => console.log("📏 Растяжение (класс):", info.event)}
            />
          </div>
        );
      })}
    </div>
  );
};

export default WeekViewByGrade;