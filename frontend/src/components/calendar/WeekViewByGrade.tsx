/**
 * WeekViewByGrade — календарь по классам.
 *  • В режиме draft открывает LessonEditorModal по клику,
 *    в режиме active — только просмотр.
 *  • Не хранит собственную копию уроков, использует prop `lessons`.
 */

import React, { useState } from 'react';
import FullCalendarTemplateView from './FullCalendarTemplateView';
import LessonEditorModal from './LessonEditorModal';

interface Lesson {
  id: number;
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;          // 0–4  (Пн–Пт)
  start_time: string;           // 'HH:mm'
  duration_minutes: number;
  type?: string;
  subject_name?: string;
  grade_name?: string;
  teacher_name?: string;
  status?: 'under' | 'ok' | 'over';
}

interface Lookup { id: number; name: string; }

const weekdayMap = [
  '2025-07-07', // Пн
  '2025-07-08', // Вт
  '2025-07-09', // Ср
  '2025-07-10', // Чт
  '2025-07-11', // Пт
];

const statusColor: Record<string, string> = {
  over:  '#fecaca',
  under: '#fef08a',
  ok:    '#bbf7d0',
};

interface Props {
  lessons: Lesson[];
  source?: 'draft' | 'active';
  subjects: Lookup[];
  grades: Lookup[];
  teachers: Lookup[];
  teacherAvailability: any[];
  onLessonSave:   (l: Lesson) => void;
  onLessonDelete: (id: number) => void;
}

const WeekViewByGrade: React.FC<Props> = ({
  lessons,
  source = 'active',
  subjects,
  grades,
  teachers,
  teacherAvailability,
  onLessonSave,
  onLessonDelete,
}) => {
  const [selected, setSelected] = useState<Lesson | null>(null);
  const [showModal, setShowModal] = useState(false);

  if (!lessons.length) {
    return <p className="text-gray-500">Нет уроков</p>;
  }

  const gradeIds = [...new Set(lessons.map(l => l.grade))];

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Расписание по классам</h2>

      {gradeIds.map((gradeId) => {
        const gradeLessons = lessons.filter(l => l.grade === gradeId);
        const gradeName = gradeLessons[0]?.grade_name || `Класс ${gradeId}`;

        const events = gradeLessons.map((l) => {
          // превращаем «день + HH:mm» в ISO‑даты
          const baseDate = weekdayMap[l.day_of_week];
          const [hh, mm] = l.start_time.split(':').map(Number);
          const startDate = new Date(`${baseDate}T00:00:00`);
          startDate.setHours(hh, mm, 0, 0);
          const endDate = new Date(startDate.getTime() + l.duration_minutes * 60000);

          const emoji = l.type === 'course' ? '📗' : '📘';

          return {
            id:     String(l.id),
            title:  `🏫 ${l.grade_name}\n${emoji} ${l.subject_name}\n👩‍🏫 ${l.teacher_name}`,
            start:  startDate.toISOString(),
            end:    endDate.toISOString(),
            backgroundColor: statusColor[l.status ?? 'ok'],
            textColor:  '#111827',
            borderColor: 'transparent',
            display: 'block',
            extendedProps: { durationMin: l.duration_minutes },
          };
        });

        return (
          <div key={gradeId} className="mb-8">
            <h3 className="text-md font-bold mb-2">🏫 {gradeName}</h3>

            <FullCalendarTemplateView
              events={events}
              editable={source === 'draft'}
              onEventClick={(info) => {
                if (source !== 'draft') return;
                const id = parseInt(info.event.id, 10);
                const lesson = lessons.find(l => l.id === id);
                if (lesson) {
                  setSelected(lesson);
                  setShowModal(true);
                }
              }}
              onEventDrop={(arg) => console.log('📦 Drag‑drop', arg.event)}
              onEventResize={(arg) => console.log('📏 Resize', arg.event)}
            />
          </div>
        );
      })}

      {selected && (
        <LessonEditorModal
          open={showModal}
          lesson={selected}
          grades={grades}
          subjects={subjects}
          teachers={teachers}
          allLessons={lessons}
          teacherAvailability={teacherAvailability}
          onClose={() => setShowModal(false)}
          onSave={(l) => { onLessonSave(l); setShowModal(false); }}
          onDelete={(id) => { onLessonDelete(id); setShowModal(false); }}
        />
      )}
    </div>
  );
};

export default WeekViewByGrade;
