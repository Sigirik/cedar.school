/**
 * WeekViewByGrade — календарь по классам.
 *  • В draft‑режиме открывает LessonEditorModal и
 *    сохраняет drag‑n‑drop / resize через onLessonSave.
 *  • В active‑режиме только просмотр.
 */

import React, { useState } from 'react';
import { message } from 'antd';
import FullCalendarTemplateView from './FullCalendarTemplateView';
import LessonEditorModal from './LessonEditorModal';
import { validateLesson, PlainLesson, TeacherSlot } from '../../utils/validateLesson';

interface Lesson {
  id: number;
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;          // 0 = Пн … 4 = Пт
  start_time: string;           // 'HH:mm'
  duration_minutes: number;
  type?: string;
  subject_name?: string;
  grade_name?: string;
  teacher_name?: string;
  status?: 'under' | 'ok' | 'over';
}

interface Lookup { id: number; name: string; }

interface Props {
  lessons: Lesson[];
  source?: 'draft' | 'active';
  subjects: Lookup[];
  grades: Lookup[];
  teachers: Lookup[];
  teacherAvailability: any[];
  onLessonModalProps?: any;
  onLessonSave:   (l: Lesson) => void;
  onLessonDelete: (id: number) => void;
}

const weekdayMap = [
  '2025-07-07', // Пн
  '2025-07-08',
  '2025-07-09',
  '2025-07-10',
  '2025-07-11', // Пт
];

const statusColor: Record<string, string> = {
  over:  '#fecaca',
  under: '#fef08a',
  ok:    '#bbf7d0',
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
const toTeacherSlot = (a: any): TeacherSlot => ({
  teacher: a.teacher,
  day_of_week: a.day_of_week,
  start_time: a.start_time ?? a.start,  // поддержка разных полей
  end_time: a.end_time ?? a.end,
});

const WeekViewByGrade: React.FC<Props> = ({
  lessons,
  source = 'active',
  subjects,
  grades,
  teachers,
  teacherAvailability,
  onLessonModalProps = {},
  onLessonSave,
  onLessonDelete,
}) => {
  const [selected, setSelected] = useState<Lesson | null>(null);
  const [showModal, setShowModal] = useState(false);

//  if (!lessons.length) return <p className="text-gray-500">Нет уроков</p>;

  const gradeIds = [...new Set(lessons.map(l => l.grade))];

  const checkLessons: PlainLesson[] = lessons.map(toPlainLesson);
  const checkAvailability: TeacherSlot[] = teacherAvailability.map(toTeacherSlot);

  /** Пересчитать объект урока после drag‑n‑drop / resize */
  const rebuildLesson = (ev: any, src: Lesson): Lesson => {
    const jsDate = ev.event.start as Date;             // новая дата‑время начала
    const endJs  = ev.event.end   as Date;
    const newDay = jsDate.getDay() === 1 ? 0 : jsDate.getDay() - 1; // 1=Mon→0, 5=Fri→4
    const hh     = String(jsDate.getHours()).padStart(2, '0');
    const mm     = String(jsDate.getMinutes()).padStart(2, '0');
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
        <h2 className="text-lg font-semibold mb-4">Расписание по классам</h2>
          <button
            className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
            onClick={() => {
              const newLesson: Lesson = {
                  id: Date.now(),
                  grade: '',
                  subject: '',
                  teacher: '',
                  day_of_week: 0,
                  start_time: '08:00',
                  duration_minutes: 45,
              };
              setSelected(newLesson);
              setShowModal(true);
            }}
          >
            + Новый урок
          </button>
      </div>

      {gradeIds.map((gradeId) => {
        const gradeLessons = lessons.filter(l => l.grade === gradeId);
        const gradeName    = gradeLessons[0]?.grade_name || `Класс ${gradeId}`;

        const events = gradeLessons.map(l => {
          const base = weekdayMap[l.day_of_week];
          const [h, m]  = l.start_time.split(':').map(Number);
          const start   = new Date(`${base}T${l.start_time}:00`);
          start.setHours(h, m, 0, 0);
          const end     = new Date(start.getTime() + l.duration_minutes * 60000);

          const emoji = l.type === 'course' ? '📗' : '📘';

          return {
            id:    String(l.id),
            title: `🏫 ${l.grade_name}\n${emoji} ${l.subject_name}\n👩‍🏫 ${l.teacher_name}`,
            start: start.toISOString(),
            end:   end.toISOString(),
            backgroundColor: statusColor[l.status ?? 'ok'],
            textColor:  '#111827',
            borderColor: 'transparent',
            display: 'block',
            extendedProps: { durationMin: l.duration_minutes },
          };
        });

        return (
          <div key={gradeId} className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-md font-bold">🏫 {gradeName}</h3>
              {source === 'draft' && (
                <button
                  className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
                  onClick={() => {
                    const emptyLesson: Lesson = {
                      id: Date.now(), // временный ID
                      grade: gradeId,
                      subject: '',
                      teacher: '',
                      day_of_week: 0,
                      start_time: '08:00',
                      duration_minutes: 45,
                    };
                    setSelected(emptyLesson);
                    setShowModal(true);
                  }}
                >
                  + Новый урок
                </button>
              )}
            </div>

            <FullCalendarTemplateView
              events={events}
              editable={source === 'draft'}
              /** ⬇️ клик по карточке */
              onEventClick={(info) => {
                if (source !== 'draft') return;
                const id = Number(info.event.id);
                const l  = lessons.find(x => x.id === id);
                if (l) {
                  setSelected(l);
                  setShowModal(true);     // form уже «привязан» к DOM – warning исчез
                }
              }}
              /** ⬇️ drag‑n‑drop */
              onEventDrop={(info) => {
                const id = Number(info.event.id);
                const src = lessons.find(x => x.id === id);
                if (!src) return;
                const updated = rebuildLesson(info, src);

                  // Проверки!
                    const { errors, warnings } = validateLesson(
                        toPlainLesson(updated),
                        checkLessons,
                        checkAvailability
                    );
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
                onLessonSave(updated);
              }}
              /** ⬇️ resize */
              onEventResize={(info) => {
                const id = Number(info.event.id);
                const src = lessons.find(x => x.id === id);
                if (!src) return;
                const updated = rebuildLesson(info, src);

                  // Проверки!
                  const { errors, warnings } = validateLesson(
                        toPlainLesson(updated),
                        checkLessons,
                        checkAvailability
                  );
                  if (errors.length) {
                    message.error(errors.join('\n'));
                    info.revert();
                    return;
                  }
                  if (warnings.length) {
                    message.warning(warnings.join('\n'));
                    // Всё равно разрешаем resize!
                  }

                onLessonSave(updated);
              }}
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
          {...(onLessonModalProps || {})}
          onClose={() => setShowModal(false)}
          onSave={(l) => { onLessonSave(l); setShowModal(false); }}
          onDelete={(id) => { onLessonDelete(id); setShowModal(false); }}
        />
      )}
    </div>
  );
};

export default WeekViewByGrade;