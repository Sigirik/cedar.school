// Загружает расписание (lessons) и нормы (weekly-norms)
// Считает:
// факт / норма по урокам (type === 'lesson')
// факт / норма по курсам (type === 'course')
// Строит таблицу с подсветкой отклонений:
// ✅ если соблюдено
// ⚠️ если превышено или недобор
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Table, Tag, Spin, message } from 'antd';

interface Lesson {
  grade: string;
  subject: string;
  type: 'lesson' | 'course';
}

interface Norm {
  grade: string;
  subject: string;
  lessons_per_week: number;
  courses_per_week: number;
}

interface RowData {
  key: string;
  grade: string;
  subject: string;
  factLessons: number;
  factCourses: number;
  normLessons: number;
  normCourses: number;
}

const WeekNormSummary: React.FC<{ source: 'draft' | 'active'; id?: number }> = ({ source, id }) => {
  const [data, setData] = useState<RowData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const url =
          source === 'draft'
            ? `/api/draft/template-drafts/${id}/`
            : '/api/template/template-week/active/';
        const [lessRes, normRes] = await Promise.all([
          axios.get(url),
          axios.get('/api/ktp/weekly-norms/')
        ]);

        const lessons: Lesson[] = lessRes.data.lessons.map((l: any) => ({
          grade: l.grade_name || l.grade,
          subject: l.subject_name || l.subject,
          type: l.type || 'lesson'
        }));

        const norms: Norm[] = normRes.data;

        const counts: Record<string, RowData> = {};

        for (const l of lessons) {
          const key = `${l.grade}-${l.subject}`;
          if (!counts[key]) {
            const n = norms.find(n => n.grade === l.grade && n.subject === l.subject);
            counts[key] = {
              key,
              grade: l.grade,
              subject: l.subject,
              factLessons: 0,
              factCourses: 0,
              normLessons: n?.lessons_per_week || 0,
              normCourses: n?.courses_per_week || 0,
            };
          }
          if (l.type === 'course') counts[key].factCourses++;
          else counts[key].factLessons++;
        }

        setData(Object.values(counts));
      } catch (e) {
        message.error('Ошибка при загрузке норм или расписания.');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [source, id]);

  const columns = [
    { title: 'Класс', dataIndex: 'grade', key: 'grade' },
    { title: 'Предмет', dataIndex: 'subject', key: 'subject' },
    {
      title: 'Уроки (факт / норма)',
      key: 'lessons',
      render: (_: any, row: RowData) => {
        const diff = row.factLessons - row.normLessons;
        return diff === 0 ? (
          <Tag color="green">✅ {row.factLessons} / {row.normLessons}</Tag>
        ) : (
          <Tag color="red">⚠️ {row.factLessons} / {row.normLessons}</Tag>
        );
      }
    },
    {
      title: 'Курсы (факт / норма)',
      key: 'courses',
      render: (_: any, row: RowData) => {
        const diff = row.factCourses - row.normCourses;
        return diff === 0 ? (
          <Tag color="green">✅ {row.factCourses} / {row.normCourses}</Tag>
        ) : (
          <Tag color="red">⚠️ {row.factCourses} / {row.normCourses}</Tag>
        );
      }
    }
  ];

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Сводка по нормам</h2>
      {loading ? <Spin /> : <Table columns={columns} dataSource={data} pagination={false} size="small" />}
    </div>
  );
};

export default WeekNormSummary;
