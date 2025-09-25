//frontend/src/components/calendar/WeekViewSwitcher.tsx
// Переключает режимы: по классам 🏫, по учителям 👩‍🏫, по нормам 📊
// Использует lessons, weeklyNorms, переданные из ActiveTemplateWeekView.tsx
// Компоненты WeekViewByGrade, WeekViewByTeacher, WeekNormSummary, WeekLessonSummaryTable теперь чисто отображающие
import React, { useState, useEffect } from 'react';
import WeekViewByGrade from './WeekViewByGrade';
import WeekViewByTeacher from './WeekViewByTeacher';
import WeekNormSummary from './WeekNormSummary';
import WeekLessonSummaryTable from './WeekLessonSummaryTable';
import { Button } from 'antd';
import type { Lesson, Teacher } from './FullCalendarTemplateView';

interface ReferenceItem {
  id: number;
  name: string;
  username?: string;
}

interface WeeklyNorm {
  subject: number;
  grade: number;
  lessons_per_week: number;
  hours_per_week: number;
  courses_per_week: number;
}

interface WeekViewSwitcherProps {
  lessons: Lesson[];
  subjects: ReferenceItem[];
  grades: ReferenceItem[];
  teachers: Teacher[];
  weeklyNorms: WeeklyNorm[];
  teacherAvailability: any[];
  source?: 'active' | 'draft';
  onLessonSave?: (l: any) => void;
  onLessonDelete?: (id: number) => void;
  gradeSubjects?: { grade: number; subject: number }[];
  teacherSubjects?: { teacher: number; subject: number }[];
  teacherGrades?: { teacher: number; grade: number }[];
  hasCollisionErrors?: boolean;
  warningsCount?: number;
  collisionMap?: Map<number, 'error' | 'warning'>;
}

const mapToRecord = (m?: Map<number, 'error' | 'warning'>): Record<string, 'error' | 'warning'> => {
  if (!m) return {};
  const obj: Record<string, 'error' | 'warning'> = {};
  m.forEach((v, k) => { obj[String(k)] = v; });
  return obj;
};

const WeekViewSwitcher: React.FC<WeekViewSwitcherProps> = ({
  lessons, subjects, grades, teachers,
  weeklyNorms, teacherAvailability,
  onLessonSave, onLessonDelete,
  gradeSubjects, teacherSubjects, teacherGrades,
  source = 'active',
  hasCollisionErrors, warningsCount, collisionMap,
}) => {
  const [mode, setMode] = useState<'grade' | 'teacher' | 'summary' | 'norm'>(() => {
    const saved = localStorage.getItem('weekViewMode');
    return saved === 'teacher' || saved === 'norm' || saved === 'summary' ? saved : 'grade';
  });

  useEffect(() => {
    localStorage.setItem('weekViewMode', mode);
  }, [mode]);

  return (
    <div className="mt-6">
      <div className="flex gap-2 mb-4 items-center">
        <Button
          type={mode === 'grade' ? 'primary' : 'default'}
          onClick={() => setMode('grade')}
        >
          🏫 По классам
        </Button>
        <Button
          type={mode === 'teacher' ? 'primary' : 'default'}
          onClick={() => setMode('teacher')}
        >
          👩‍🏫 По учителям
        </Button>
        <Button
          type={mode === 'summary' ? 'primary' : 'default'}
          onClick={() => setMode('summary')}
        >
          🧮 Сводная таблица
        </Button>
        <Button
          type={mode === 'norm' ? 'primary' : 'default'}
          onClick={() => setMode('norm')}
        >
          📊 По нормам
        </Button>

        <div className="ml-auto text-sm">
          {hasCollisionErrors ? (
            <span className="px-2 py-0.5 rounded bg-red-100 text-red-700">Коллизии обнаружены</span>
          ) : warningsCount ? (
            <span className="px-2 py-0.5 rounded bg-yellow-100 text-yellow-700">Предупреждений: {warningsCount}</span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700">Всё чисто</span>
          )}
        </div>
      </div>

      {mode === 'grade' && (
        <WeekViewByGrade
          lessons={lessons}
          subjects={subjects}
          grades={grades}
          teachers={teachers}
          teacherAvailability={teacherAvailability}
          source={source}
          onLessonModalProps={source === 'draft' ? {
            gradeSubjects,
            teacherSubjects,
            teacherGrades
          } : undefined}
          onLessonSave={onLessonSave!}
          onLessonDelete={onLessonDelete!}
          collisionMap={mapToRecord(collisionMap)}
        />
      )}
      {mode === 'teacher' && (
        <WeekViewByTeacher
          lessons={lessons}
          subjects={subjects}
          grades={grades}
          teachers={teachers}
          teacherAvailability={teacherAvailability}
          source={source}
          onLessonModalProps={source === 'draft' ? {
            gradeSubjects,
            teacherSubjects,
            teacherGrades
          } : undefined}
          onLessonSave={onLessonSave!}
          onLessonDelete={onLessonDelete!}
          collisionMap={mapToRecord(collisionMap)}
        />
      )}
      {mode === 'norm' && <WeekNormSummary lessons={lessons} weeklyNorms={weeklyNorms} />}
      {mode === 'summary' && (
        <WeekLessonSummaryTable
          lessons={lessons}
          subjects={subjects}
          grades={grades}
          teachers={teachers}
          onLessonModalProps={source === 'draft' ? {
            gradeSubjects,
            teacherSubjects,
            teacherGrades
          } : undefined}
          onLessonSave={onLessonSave!}
          onLessonDelete={onLessonDelete!}
          collisionMap={mapToRecord(collisionMap)}
        />
      )}
    </div>
  );
};

export default WeekViewSwitcher;
