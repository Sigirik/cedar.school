// frontend/src/components/calendar/WeekViewByTeacher.tsx
import React, { useState } from 'react';
import { Button, message } from 'antd';
import FullCalendarTemplateView, { type Teacher } from './FullCalendarTemplateView';
import LessonEditorModal from './LessonEditorModal';
import { validateLesson } from '@/utils/validateLesson';

import type { EventInput } from '@fullcalendar/core';
import type { PlainLesson, TeacherSlot } from '@/utils/validateLesson';

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

interface Props {
  lessons: Lesson[];
  teacherAvailability?: TeacherAvailability[];
  source?: 'draft' | 'active';
  subjects?: { id: number; name: string }[];
  grades?: { id: number; name: string }[];
  teachers?: Teacher[];
  onLessonModalProps?: any;
  onLessonSave?: (l: Lesson) => void;
  onLessonDelete?: (id: number) => void;
  collisionMap?: Record<string, 'error' | 'warning'>;
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

const toPlainLesson = (l: any): PlainLesson => ({
  id: l.id,
  grade: l.grade,
  teacher: l.teacher,
  day_of_week: l.day_of_week,
  start_time: l.start_time,
  duration_minutes: l.duration_minutes,
  // можно добавить type если требуется
});

const toTeacherSlot = (availability: any): TeacherSlot => ({
  teacher: availability.teacher,
  day_of_week: availability.day_of_week,
  start_time: availability.start_time,
  end_time: availability.end_time,
});


const WeekViewByTeacher: React.FC<Props> = ({
  lessons,
  teacherAvailability = [],
  source = 'active',
  subjects = [],
  grades = [],
  teachers = [],
  onLessonModalProps = {},
  onLessonSave,
  onLessonDelete,
  collisionMap,
}) => {
  const [selected, setSelected] = useState<Lesson | null>(null);
  const [showModal, setShowModal] = useState(false);

//   if (!lessons || lessons.length === 0) return <p className="text-gray-500">Нет уроков</p>;

  const teacherIds = [...new Set(lessons.map(l => l.teacher))];

  const checkLessons: PlainLesson[] = lessons.map(toPlainLesson);
  const checkAvailability: TeacherSlot[] = teacherAvailability.map(toTeacherSlot);

  /** Пересчитать объект урока после drag‑n‑drop / resize */
  const rebuildLesson = (ev: any, src: Lesson): Lesson => {
    const jsDate = ev.event.start as Date;
    const endJs = ev.event.end as Date;
    const newDay = jsDate.getDay() === 1 ? 0 : jsDate.getDay() - 1;
    const hh = String(jsDate.getHours()).padStart(2, '0');
    const mm = String(jsDate.getMinutes()).padStart(2, '0');
    return {
      ...src,
      day_of_week: newDay,
      start_time: `${hh}:${mm}`,
      duration_minutes: Math.round((endJs.getTime() - jsDate.getTime()) / 60000),
    };
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold mb-4">Расписание по учителям</h2>
          <Button
            className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
            onClick={() => {
             const newLesson: Lesson = {
               id: Date.now(),
               grade: 0 as unknown as number,
               subject: 0 as unknown as number,
               teacher: 0 as unknown as number,
               day_of_week: 0,
               start_time: '08:00',
               duration_minutes: 45,
               subject_name: '',
               grade_name: '',
               teacher_name: '',
             };
              setSelected(newLesson);
              setShowModal(true);
            }}
          >
            + Новый урок
          </Button>
      </div>

      {teacherIds.map((teacherId) => {
        const teacherLessons = lessons.filter(l => l.teacher === teacherId);
        const teacherName = teacherLessons[0]?.teacher_name || `Учитель ${teacherId}`;

        const lessonEvents: EventInput[] = teacherLessons.map((lesson) => {
        const baseDate = weekdayMap[lesson.day_of_week];
        const safeTime = lesson.start_time.slice(0, 5);
        const [hour, minute] = safeTime.split(':').map(Number);

        const startDate = new Date(`${baseDate}T00:00`);
        startDate.setHours(hour, minute, 0, 0);
        const endDate = new Date(startDate.getTime() + lesson.duration_minutes * 60000);

        const emoji = lesson.type === 'course' ? '📗' : '📘';

        return {
          id: String(lesson.id),
          title: `${lesson.start_time} · ${lesson.duration_minutes} мин\n${emoji} ${lesson.subject_name}\n🏫 ${lesson.grade_name}`,
          start: startDate.toISOString(),
          end: endDate.toISOString(),
          backgroundColor: statusColorMap[lesson.status || 'ok'],
          textColor: '#111827',
          borderColor: 'transparent',
          display: 'block',
          extendedProps: {
            status: lesson.status,
            durationMin: lesson.duration_minutes,
          },
        };
      });

      const availabilityEvents: EventInput[] = teacherAvailability
        .filter((slot) => slot.teacher === teacherId)
        .map((slot, idx) => {
          const dayIndex = slot.day_of_week; // 0 — Пн
          const baseDate = weekdayMap[dayIndex];
          const cleanStart = slot.start_time.slice(0, 5);
          const cleanEnd = slot.end_time.slice(0, 5);

          return {
            id: `availability-${teacherId}-${idx}`,
            title: '', // важно для единообразного типа; на фоне не видно
            start: `${baseDate}T${cleanStart}`,
            end: `${baseDate}T${cleanEnd}`,
            display: 'background',
            backgroundColor: '#dbeafe',
          };
        });

      const events: EventInput[] = [...lessonEvents, ...availabilityEvents];

        return (
          <div key={teacherId} className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-md font-bold mb-2">👩‍🏫 {teacherName}</h3>
              {source === 'draft' && (
                <Button
                  className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
                  onClick={() => {
                     const emptyLesson: Lesson = {
                       id: Date.now(),
                       grade: 0 as unknown as number,
                       subject: 0 as unknown as number,
                       teacher: teacherId,
                       day_of_week: 0,
                       start_time: '08:00',
                       duration_minutes: 45,
                       subject_name: '',
                      grade_name: '',
                       teacher_name: '',
                     };
                     setSelected(emptyLesson);
                     setShowModal(true);
                                   }}
                                  >
                                    + Новый урок
                </Button>
              )}
            </div>
            <FullCalendarTemplateView
              events={events}
              collisionMap={collisionMap}
              editable={source === 'draft'}
              onEventClick={(info) => {
                if (source !== 'draft') return;
                const id = Number(info.event.id);
                const l = teacherLessons.find(x => x.id === id);
                if (l) {
                  setSelected(l);
                  setShowModal(true);
                }
              }}
              onEventDrop={(info) => {
                const id = Number(info.event.id);
                const src = lessons.find(x => x.id === id);
                if (!src) return;
                const updated = rebuildLesson(info, src);

                // Проверки (с исключением текущего урока)
                const base = checkLessons.filter(x => x.id !== src.id);
                const { errors, warnings } = validateLesson(toPlainLesson(updated), base, checkAvailability);

                  if (errors.length) {
                    message.error(errors.join('\n'));
                    // ОТМЕНИТЬ drag-n-drop — вернём событие на старое место:
                    info.revert();
                    return;
                  }
                  if (warnings.length) {
                    message.warning(warnings.join('\n'));
                    // Всё равно разрешаем drop!
                  }
                onLessonSave && onLessonSave(updated);
              }}
              /** ⬇️ resize */
              onEventResize={(info) => {
                const id = Number(info.event.id);
                const src = lessons.find(x => x.id === id);
                if (!src) return;
                const updated = rebuildLesson(info, src);

                  // Проверки!
                    const base = checkLessons.filter(x => x.id !== src.id);
                    const { errors, warnings } = validateLesson(toPlainLesson(updated), base, checkAvailability);

                  if (errors.length) {
                    message.error(errors.join('\n'));
                    info.revert();
                    return;
                  }
                  if (warnings.length) {
                    message.warning(warnings.join('\n'));
                    // Всё равно разрешаем resize!
                  }

                onLessonSave && onLessonSave(updated);
              }}
            />
            {selected && (
              <LessonEditorModal
                open={showModal}
                lesson={selected}
                grades={grades || []}
                subjects={subjects || []}
                teachers={teachers || []}
                allLessons={lessons}
                teacherAvailability={teacherAvailability}
                {...(onLessonModalProps || {})}
                onClose={() => setShowModal(false)}
                onSave={(plainLesson: PlainLesson) => {
                  if (!selected) return;
                  // собираем полный Lesson: подтягиваем subject и остальные поля из selected
                  const mergedLesson: Lesson = {
                    ...selected,
                    ...plainLesson, // перезапишет day_of_week, start_time, duration_minutes, grade, teacher
                  };
                  onLessonSave?.(mergedLesson);
                  setShowModal(false);
                }}
                onDelete={(id) => { if (onLessonDelete) onLessonDelete(id); setShowModal(false); }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default WeekViewByTeacher;
