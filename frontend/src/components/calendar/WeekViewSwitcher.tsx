// Переключает режимы: по классам 🏫, по учителям 👩‍🏫, по нормам 📊
// Использует lessons, weeklyNorms, переданные из ActiveTemplateWeekView.tsx
// Компоненты WeekViewByGrade, WeekViewByTeacher, WeekNormSummary, WeekLessonSummaryTable теперь чисто отображающие
import React, { useState } from 'react';
import WeekViewByGrade from './WeekViewByGrade';
import WeekViewByTeacher from './WeekViewByTeacher';
import WeekNormSummary from './WeekNormSummary';
import WeekLessonSummaryTable from './WeekLessonSummaryTable';

interface Lesson {
  subject: number;
  subject_name: string;
  grade: number;
  grade_name: string;
  teacher: number;
  teacher_name: string;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
  status?: 'under' | 'ok' | 'over';
}

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
  teachers: ReferenceItem[];
  weeklyNorms: WeeklyNorm[];
  teacherAvailability: any[];
  source?: 'active' | 'draft';
  onLessonSave?: (l: any) => void;
  onLessonDelete?: (id: number) => void;
  gradeSubjects?: { grade: number; subject: number }[];
  teacherSubjects?: { teacher: number; subject: number }[];
  teacherGrades?: { teacher: number; grade: number }[];
}

const WeekViewSwitcher: React.FC<WeekViewSwitcherProps> = ({
  lessons, subjects, grades, teachers,
  weeklyNorms, teacherAvailability,
  onLessonSave, onLessonDelete,
  gradeSubjects,
  teacherSubjects,
  teacherGrades,
  source = 'active'
}) => {
  const [mode, setMode] = useState<'grade' | 'teacher' | 'norm'>('grade');

  return (
    <div className="mt-6">
      <div className="flex gap-2 mb-4">
        <button
          className={`px-3 py-1 rounded ${mode === 'grade' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('grade')}
        >
          🏫 По классам
        </button>
        <button
          className={`px-3 py-1 rounded ${mode === 'teacher' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('teacher')}
        >
          👩‍🏫 По учителям
        </button>
        <button
          className={`px-3 py-1 rounded ${mode === 'summary' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('summary')}
        >
          🧮 Сводная таблица
        </button>
        <button
          className={`px-3 py-1 rounded ${mode === 'norm' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('norm')}
        >
          📊 По нормам
        </button>

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
        />
      )}
    </div>
  );
};

export default WeekViewSwitcher;
