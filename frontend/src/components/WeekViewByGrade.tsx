// Загружает черновик по draftId
// Строит таблицу с вертикальными столбцами по дням недели (Пн–Сб)
// Группирует уроки по классам (🏫 5А, 🏫 6Б, ...)
// Показывает упорядоченные уроки в ячейках
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Spin, message } from 'antd';

interface Lesson {
  subject: number;
  grade: number;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
}

interface ReferenceItem {
  id: number;
  name: string;
}

const weekdayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];

const getNameById = (id: number, list: ReferenceItem[]): string => {
  return list.find(i => i.id === id)?.name || `ID ${id}`;
};

const WeekViewByGrade: React.FC<{
  source: 'draft' | 'active';
  id?: number;
  subjects: ReferenceItem[];
  grades: ReferenceItem[];
}> = ({ source, id, subjects, grades }) => {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [gradeIds, setGradeIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLessons() {
      try {
        const url =
          source === 'draft'
            ? `/api/draft/template-drafts/${id}/`
            : '/api/template/template-week/active/';
        const res = await axios.get(url);
        const allLessons: Lesson[] = res.data.lessons || [];

        const uniqueGrades = [...new Set(allLessons.map(l => l.grade))];
        setGradeIds(uniqueGrades);
        setLessons(allLessons);

        console.log('🔍 lessons from API:', allLessons);
        console.log('📚 subjects:', subjects);
        console.log('🏫 grades:', grades);
      } catch (e) {
        message.error('Не удалось загрузить шаблон.');
      } finally {
        setLoading(false);
      }
    }
    fetchLessons();
  }, [source, id]);

  const getColorClass = (gradeId: number, subjectId: number) => {
    const count = lessons.filter(
      l => l.grade === gradeId && l.subject === subjectId
    ).length;
    if (count > 5) return 'bg-red-200';
    if (count < 5) return 'bg-yellow-200';
    return '';
  };

  if (loading) return <Spin />;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Расписание по классам</h2>
      {gradeIds.map(grade => (
        <div key={grade} className="mb-6">
          <h3 className="text-md font-bold mb-1">🏫 {getNameById(grade, grades)}</h3>
          <div className="grid grid-cols-5 gap-4 text-sm">
            {weekdayLabels.map((day, dayIndex) => {
              const lessonsOfDay = lessons
                .filter(l => l.grade === grade && l.day_of_week === dayIndex)
                .sort((a, b) => a.start_time.localeCompare(b.start_time));

              return (
                <div key={dayIndex}>
                  <div className="font-semibold mb-1">{day}</div>
                  {lessonsOfDay.length > 0 ? (
                    lessonsOfDay.map((l, i) => (
                      <div
                        key={i}
                        className={`mb-1 border px-2 py-1 rounded ${getColorClass(
                          l.grade,
                          l.subject
                        )}`}
                      >
                        ⏰ {l.start_time.slice(0, 5)} ⏳ {l.duration_minutes} мин<br />
                        {l.type === 'course' ? '📗' : '📘'} {getNameById(l.subject, subjects)}
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

export default WeekViewByGrade;


