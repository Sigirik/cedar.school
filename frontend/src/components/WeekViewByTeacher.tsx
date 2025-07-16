import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Spin, message } from 'antd';

interface Lesson {
  subject: number;
  teacher: number;
  grade: number;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
}

interface ReferenceItem {
  id: number;
  name: string;
  username?: string;
}

interface Availability {
  teacher: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface WeeklyNorm {
  subject: number;
  grade: number;
  lessons_per_week: number;
  hours_per_week: number;
  courses_per_week: number;
}

const weekdayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];

const getNameById = (
  id: number,
  list?: ReferenceItem[],
  field: 'name' | 'username' = 'name'
): string => {
  if (!Array.isArray(list)) return `—`;
  const item = list.find(i => i.id === id);
  return item ? item[field] || `—` : `—`;
};

const WeekViewByTeacher: React.FC<{
  source: 'draft' | 'active';
  id?: number;
  subjects: ReferenceItem[];
  teachers: ReferenceItem[];
  grades: ReferenceItem[];
  weeklyNorms?: WeeklyNorm[];
}> = ({ source, id, subjects, teachers, grades, weeklyNorms = [] }) => {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [teacherIds, setTeacherIds] = useState<number[]>([]);
  const [availabilities, setAvailabilities] = useState<Availability[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const url =
          source === 'draft'
            ? `/api/draft/template-drafts/${id}/`
            : '/api/template/template-week/active/';
        const res = await axios.get(url);
        const allLessons: Lesson[] = res.data.lessons || [];
        const uniqueTeachers = [...new Set(allLessons.map(l => l.teacher))];
        setTeacherIds(uniqueTeachers);
        setLessons(allLessons);
      } catch (e) {
        message.error('Не удалось загрузить шаблон.');
      }

      try {
        const availRes = await axios.get('/api/template/teacher-availability/');
        setAvailabilities(availRes.data);
      } catch (e) {
        console.warn('Нет данных о доступности учителей');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [source, id]);

  const getNorm = (gradeId: number, subjectId: number) => {
    return weeklyNorms.find(
      norm => norm.grade === gradeId && norm.subject === subjectId
    );
  };

  const getLessonColor = (gradeId: number, subjectId: number) => {
    const count = lessons.filter(
      l => l.grade === gradeId && l.subject === subjectId
    ).length;
    const norm = getNorm(gradeId, subjectId);
    if (norm) {
      if (count > norm.lessons_per_week) return 'bg-red-200';
      if (count < norm.lessons_per_week) return 'bg-yellow-200';
    }
    return '';
  };

  const isInAvailability = (lesson: Lesson): boolean => {
    return availabilities.some(av =>
      av.teacher === lesson.teacher &&
      av.day_of_week === lesson.day_of_week &&
      lesson.start_time >= av.start_time &&
      lesson.start_time < av.end_time
    );
  };

  const renderAvailabilityBounds = (teacherId: number, dayIndex: number) => {
    const bounds = availabilities.filter(
      av => av.teacher === teacherId && av.day_of_week === dayIndex
    );
    if (bounds.length === 0) return null;

    const earliest = bounds[0].start_time;
    const latest = bounds[bounds.length - 1].end_time;

    return (
      <div className="text-xs text-gray-500 mt-1">
        ⏱ Доступ: {earliest.slice(0, 5)} – {latest.slice(0, 5)}
      </div>
    );
  };

  if (loading) return <Spin />;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Расписание по учителям</h2>
      {teacherIds.map(teacher => (
        <div key={teacher} className="mb-6">
          <h3 className="text-md font-bold mb-1">👩‍🏫 {getNameById(teacher, teachers, 'username')}</h3>
          <div className="grid grid-cols-5 gap-4 text-sm">
            {weekdayLabels.map((day, dayIndex) => {
              const lessonsOfDay = lessons
                .filter(l => l.teacher === teacher && l.day_of_week === dayIndex)
                .sort((a, b) => a.start_time.localeCompare(b.start_time));

              return (
                <div key={dayIndex}>
                  <div className="font-semibold mb-1">{day}</div>
                  {renderAvailabilityBounds(teacher, dayIndex)}
                  {lessonsOfDay.length > 0 ? (
                    lessonsOfDay.map((l, i) => (
                      <div
                        key={i}
                        className={`mb-1 border px-2 py-1 rounded ${getLessonColor(
                          l.grade,
                          l.subject
                        )} ${isInAvailability(l) ? 'bg-white' : 'bg-gray-200'}`}
                      >
                        ⏰ {l.start_time.slice(0, 5)} ⏳ {l.duration_minutes} мин<br />
                        {l.type === 'course' ? '📗' : '📘'} {getNameById(l.subject, subjects)}<br />
                        🏫 {getNameById(l.grade, grades)}
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-400">—</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default WeekViewByTeacher;
