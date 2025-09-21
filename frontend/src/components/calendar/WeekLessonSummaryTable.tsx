// frontend/src/components/calendar/WeekLessonSummaryTable.tsx
import React, { useState } from 'react';
import LessonEditorModal from './LessonEditorModal';
import { Button } from 'antd';

interface Lesson {
  id: number;
  subject: number;
  subject_name: string;
  grade: number;
  grade_name: string;
  teacher: number;
  teacher_name: string;
  day_of_week: number; // 0=Пн ... 4=Пт
  start_time: string; // HH:mm
  duration_minutes: number;
  status?: 'under' | 'ok' | 'over';
}

interface Teacher {
  id: number;
  full_name?: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
}

interface ReferenceItem {
  id: number;
  name: string;
}

interface Props {
  lessons: Lesson[];
  subjects: ReferenceItem[];
  grades: ReferenceItem[];
  teachers: Teacher[];
  teacherAvailability?: any[];
  onLessonModalProps?: any;
  onLessonSave?: (l: Lesson) => void;
  onLessonDelete?: (id: number) => void;
  /** для подсветки в календарном варианте, если добавите */
  collisionMap?: Record<string, 'error' | 'warning'>;
}

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];

// Пастельная палитра для учителей
function generatePastelPalette(count: number): string[] {
  const palette: string[] = [];
  const saturation = 70;
  const lightness = 85;
  const step = 360 / count;
  for (let i = 0; i < count; i++) {
    const hue = Math.round(i * step) % 360;
    palette.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
  }
  return palette;
}

function getTeacherColorMap(teachers: Teacher[]): Record<number, string> {
  const palette = generatePastelPalette(teachers.length);
  const map: Record<number, string> = {};
  teachers.forEach((t, i) => {
    map[t.id] = palette[i];
  });
  return map;
}

const WeekLessonSummaryTable: React.FC<Props> = ({
  lessons, subjects, grades, teachers, teacherAvailability = [],
  onLessonModalProps = {}, onLessonSave, onLessonDelete
}) => {
  const [selected, setSelected] = useState<Lesson | null>(null);
  const [showModal, setShowModal] = useState(false);

  type Row = {
    start_time: string;
    grade_name: string;
    duration_minutes: number;
    cells: Record<number, Lesson | undefined>;
  };

  const rowMap = new Map<string, Row>();

  lessons.forEach((l) => {
    const time = l.start_time.slice(0, 5);
    const key = `${time}__${l.grade}`;
    if (!rowMap.has(key)) {
      rowMap.set(key, {
        start_time: time,
        grade_name: l.grade_name,
        duration_minutes: l.duration_minutes,
        cells: {},
      });
    }
    rowMap.get(key)!.cells[l.day_of_week] = l;
  });

  const rows = Array.from(rowMap.values()).sort((a, b) => {
    if (a.start_time < b.start_time) return -1;
    if (a.start_time > b.start_time) return 1;
    return a.grade_name.localeCompare(b.grade_name);
  });

  const markHourStartRows = (rows: Row[]): (Row & { isNewHourStart: boolean })[] => {
    let prevHour: number | null = null;
    return rows.map((row) => {
      const hour = parseInt(row.start_time.split(':')[0], 10);
      const isNew = prevHour === null || hour > prevHour;
      prevHour = hour;
      return { ...row, isNewHourStart: isNew };
    });
  };

  const markedRows = markHourStartRows(rows);
  const teacherColors = getTeacherColorMap(teachers);

  return (
    <div className="overflow-x-auto border rounded">
      <div className="flex justify-end p-2">
        <Button
          className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
          onClick={() => {
            const newLesson: Lesson = {
              id: Date.now(),
              grade: 0 as unknown as number,   // заполните корректным классом в модалке
              subject: 0 as unknown as number, // idem
              teacher: 0 as unknown as number, // idem
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
      <table className="min-w-full text-sm table-fixed border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2 w-20 text-left">Время</th>
            {DAYS.map((day, idx) => (
              <th key={idx} className="border p-2 text-left">{day}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {markedRows.map((row, idx) => (
            <tr key={idx} className={row.isNewHourStart ? 'border-t-4 border-gray-400' : ''}>
              <td className="border p-1 text-xs text-gray-600 font-mono">
                <span className={row.isNewHourStart ? 'font-bold' : ''}>{row.start_time}</span>
              </td>
              {DAYS.map((_, i) => {
                const l = row.cells[i];
                return (
                  <td key={i} className="border p-1 align-top">
                    {l ? (
                      <div
                        className="p-1 rounded text-xs leading-tight whitespace-pre-line text-black cursor-pointer"
                        style={{ backgroundColor: teacherColors[l.teacher] }}
                        onClick={() => {
                          setSelected(l);
                          setShowModal(true);
                        }}
                      >
                        {row.grade_name}&nbsp;⏱{row.duration_minutes}&nbsp;
                        {l.subject_name}&nbsp;
                        [{l.teacher_name}]
                      </div>
                    ) : (
                      <div className="text-gray-300 text-xs text-center">—</div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex justify-end p-2">
        <Button
          className="text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded"
          onClick={() => {
            const emptyLesson: Lesson = {
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
            setSelected(emptyLesson);
            setShowModal(true);
          }}
        >
          + Новый урок
        </Button>
      </div>
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
          onSave={(l) => { onLessonSave?.(l as any); setShowModal(false); }}
          onDelete={(id) => { onLessonDelete?.(id as any); setShowModal(false); }}
        />
      )}
    </div>
  );
};

export default WeekLessonSummaryTable;
