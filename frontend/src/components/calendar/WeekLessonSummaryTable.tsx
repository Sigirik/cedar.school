// WeekLessonSummaryTable.tsx

import React from 'react';

interface Lesson {
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
  full_name: string;
  first_name: string;
  last_name: string;
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
}

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];

// Пастельная палитра
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

const WeekLessonSummaryTable: React.FC<Props> = ({ lessons, teachers }) => {
  type Row = {
    start_time: string;
    grade_name: string;
    duration_minutes: number;
    cells: Record<number, Lesson | undefined>; // ключи 0–4
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
                        className="p-1 rounded text-xs leading-tight whitespace-pre-line text-black"
                        style={{ backgroundColor: teacherColors[l.teacher] }}
                      >
                        <div
                          className="p-1 rounded text-xs leading-tight text-black break-words whitespace-normal"
                          style={{ backgroundColor: teacherColors[l.teacher] }}
                        >
                          {row.grade_name}&nbsp;⏱{row.duration_minutes}&nbsp;
                          {l.subject_name}&nbsp;
                          [{l.teacher_name}]
                        </div>
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
    </div>
  );
};

export default WeekLessonSummaryTable;
