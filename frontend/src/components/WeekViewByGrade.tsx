// Загружает черновик по draftId
// Строит таблицу с вертикальными столбцами по дням недели (Пн–Сб)
// Группирует уроки по классам (🏫 5А, 🏫 6Б, ...)
// Показывает упорядоченные уроки в ячейках
import axios from 'axios';
import { Table, Tag, Spin, message } from 'antd';

interface Lesson {
  subject: string;
  grade: string;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
}

const weekdayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

const WeekViewByGrade: React.FC<{ draftId: number }> = ({ draftId }) => {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [grades, setGrades] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDraftLessons() {
      try {
        const res = await axios.get(`/api/draft/template-drafts/${draftId}/`);
        const allLessons = res.data.data.lessons;

        const parsed: Lesson[] = allLessons.map((l: any) => ({
          subject: l.subject_name || `Предмет ${l.subject}`,
          grade: l.grade_name || `Класс ${l.grade}`,
          day_of_week: l.day_of_week,
          start_time: l.start_time,
          duration_minutes: l.duration_minutes,
          type: l.type || 'lesson',
        }));

        const uniqueGrades = [...new Set(parsed.map(l => l.grade))];
        setGrades(uniqueGrades);
        setLessons(parsed);
      } catch (e) {
        message.error('Не удалось загрузить черновик.');
      } finally {
        setLoading(false);
      }
    }
    fetchDraftLessons();
  }, [draftId]);

  if (loading) return <Spin />;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Расписание по классам</h2>
      {grades.map(grade => (
        <div key={grade} className="mb-6">
          <h3 className="text-md font-bold mb-1">🏫 {grade}</h3>
          <div className="grid grid-cols-6 gap-4 text-sm">
            {weekdayLabels.map((day, dayIndex) => {
              const lessonsOfDay = lessons
                .filter(l => l.grade === grade && l.day_of_week === dayIndex)
                .sort((a, b) => a.start_time.localeCompare(b.start_time));

              return (
                <div key={dayIndex}>
                  <div className="font-semibold mb-1">{day}</div>
                  {lessonsOfDay.length > 0 ? (
                    lessonsOfDay.map((l, i) => (
                      <div key={i} className="mb-1 border px-2 py-1 rounded bg-blue-50">
                        ⏰ {l.start_time} <br />
                        {l.type === 'course' ? '📗' : '📘'} {l.subject}
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
