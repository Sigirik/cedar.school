/**
 * WeekViewByGrade — календарь по классам.
 *  • В draft‑режиме открывает LessonEditorModal и
 *    сохраняет drag‑n‑drop / resize через onLessonSave.
 *  • В active‑режиме только просмотр.
 */

import React, { useState } from 'react';
import { Button, message } from 'antd';
import FullCalendarTemplateView, { type Lesson, type Teacher } from './FullCalendarTemplateView';
import LessonEditorModal from './LessonEditorModal';
import { validateLesson } from '@/utils/validateLesson';

import type { PlainLesson, TeacherSlot } from '@/utils/validateLesson';



interface Lookup { id: number; name: string; }

interface Props {
  lessons: Lesson[];
  source?: 'draft' | 'active';
  subjects: Lookup[];
  grades: Lookup[];
  teachers: Teacher[];
  teacherAvailability: any[];
  onLessonModalProps?: any;
  onLessonSave:   (l: Lesson) => void;
  onLessonDelete: (id: number) => void;
  collisionMap?: Record<string, 'error' | 'warning'>;
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
const toTeacherSlot = (availability: any): TeacherSlot => ({
  teacher: availability.teacher,
  day_of_week: availability.day_of_week,
  start_time: availability.start_time,
  end_time: availability.end_time,
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
  collisionMap,
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
                <Button
                  className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
                  onClick={() => {
                    const emptyLesson: Lesson = {
                      id: Date.now(),
                      grade: gradeId,
                      subject: 0 as unknown as number,
                      teacher: 0 as unknown as number,
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
                onLessonSave(updated);
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
          onSave={(plainLesson) => {
            if (!selected) return; // safety

            //TODO: я не знаю правильная логика или нет надо проверять работает ли
            const mergedLesson: Lesson = {
              ...selected,      // берём subject, names и всё что не приходит из редактора
              ...plainLesson,   // перезапишем day_of_week, start_time, duration_minutes, grade, teacher
            };
            onLessonSave(mergedLesson);
            setShowModal(false);
          }}
          onDelete={(id) => { onLessonDelete(id); setShowModal(false); }}
        />
      )}
    </div>
  );
};

export default WeekViewByGrade;