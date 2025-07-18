import React, { useState } from 'react';
import WeekViewByGrade from './WeekViewByGrade';
import WeekViewByTeacher from './WeekViewByTeacher';
import WeekNormSummary from './WeekNormSummary';
// import FullCalendarEditor from './FullCalendarEditor'; // 🔸 пока не нужен

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

const WeekViewSwitcher: React.FC<{
  lessons: Lesson[];
  subjects: ReferenceItem[];
  grades: ReferenceItem[];
  teachers: ReferenceItem[];
  weeklyNorms: WeeklyNorm[];
}> = ({ lessons, subjects, grades, teachers, weeklyNorms }) => {
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
          className={`px-3 py-1 rounded ${mode === 'norm' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('norm')}
        >
          📊 По нормам
        </button>
        {/*
        🔧 Позже можно вернуть:
        <button
          className={`px-3 py-1 rounded ${mode === 'calendar' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('calendar')}
        >
          📅 Сводная неделя
        </button>
        */}
      </div>

      {mode === 'grade' && <WeekViewByGrade lessons={lessons} />}
      {mode === 'teacher' && <WeekViewByTeacher lessons={lessons} />}
      {mode === 'norm' && <WeekNormSummary lessons={lessons} weeklyNorms={weeklyNorms} />}
      {/* {mode === 'calendar' && <FullCalendarEditor lessons={lessons} />} */}
    </div>
  );
};

export default WeekViewSwitcher;
