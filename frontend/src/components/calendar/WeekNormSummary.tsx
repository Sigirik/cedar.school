// frontend/src/components/calendar/WeekNormSummary.tsx
// Использует переданный массив lessons
// Считает нормы отдельно по lesson и course
// Показывает subject_name, grade_name
// Подсвечивает превышения/недостачи цветом
import React from 'react';
import type { Lesson } from './FullCalendarTemplateView';

interface WeeklyNorm {
  subject: number;
  grade: number;
  lessons_per_week: number;
  hours_per_week: number;
  courses_per_week: number;
}

const WeekNormSummary: React.FC<{
  lessons: Lesson[];
  weeklyNorms: WeeklyNorm[];
}> = ({ lessons, weeklyNorms }) => {
  const gradeIds = [...new Set(lessons.map(l => l.grade))];

  const getLessonsByGradeAndSubject = (grade: number, subject: number, type: 'lesson' | 'course') => {
    return lessons.filter(
      l => l.grade === grade && l.subject === subject && (l.type || 'lesson') === type
    ).length;
  };

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Сводка по нормам</h2>
      {gradeIds.map(gradeId => {
        const gradeName = lessons.find(l => l.grade === gradeId)?.grade_name;
        const normsForGrade = weeklyNorms.filter(n => n.grade === gradeId);

        return (
          <div key={gradeId} className="mb-6">
            <h3 className="text-md font-bold mb-2">🏫 {gradeName}</h3>
            <table className="table-auto w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border px-2 py-1">Предмет</th>
                  <th className="border px-2 py-1">Норма (уроки)</th>
                  <th className="border px-2 py-1">Факт (уроки)</th>
                  <th className="border px-2 py-1">Норма (курсы)</th>
                  <th className="border px-2 py-1">Факт (курсы)</th>
                </tr>
              </thead>
              <tbody>
                {normsForGrade.map(norm => {
                  const subjectName = lessons.find(l => l.subject === norm.subject)?.subject_name || `ID ${norm.subject}`;
                  const lessonCount = getLessonsByGradeAndSubject(gradeId, norm.subject, 'lesson');
                  const courseCount = getLessonsByGradeAndSubject(gradeId, norm.subject, 'course');

                  return (
                    <tr key={norm.subject}>
                      <td className="border px-2 py-1">{subjectName}</td>
                      <td className="border px-2 py-1">{norm.lessons_per_week}</td>
                      <td className={`border px-2 py-1 ${lessonCount > norm.lessons_per_week ? 'bg-red-200' : lessonCount < norm.lessons_per_week ? 'bg-yellow-200' : ''}`}>{lessonCount}</td>
                      <td className="border px-2 py-1">{norm.courses_per_week}</td>
                      <td className={`border px-2 py-1 ${courseCount > norm.courses_per_week ? 'bg-red-200' : courseCount < norm.courses_per_week ? 'bg-yellow-200' : ''}`}>{courseCount}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
};

export default WeekNormSummary;
