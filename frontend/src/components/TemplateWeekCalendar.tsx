// Загружает уроки из /api/draft/template-drafts/{draftId}/
// Преобразует их в события для FullCalendar
// Отображает визуальную сетку расписания по дням недели
import React, { useEffect, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';
import { Spin, message } from 'antd';

interface LessonEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor?: string;
}

const weekdayMap = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06", "2023-01-07"];

const TemplateWeekCalendar: React.FC<{ draftId: number }> = ({ draftId }) => {
  const [events, setEvents] = useState<LessonEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDraft() {
      try {
        const res = await axios.get(`/api/draft/template-drafts/${draftId}/`);
        const lessons = res.data.data.lessons;

        const mapped = lessons.map((lesson: any, index: number) => {
          const baseDate = weekdayMap[lesson.day_of_week];
          const start = `${baseDate}T${lesson.start_time}`;

          const [hh, mm] = lesson.start_time.split(":").map(Number);
          const endDate = new Date(`${baseDate}T${lesson.start_time}`);
          endDate.setMinutes(endDate.getMinutes() + lesson.duration_minutes);
          const end = endDate.toISOString().slice(0, 16);

          return {
            id: `lesson-${index}`,
            title: `${lesson.subject_name || "Предмет"} (${lesson.grade_name || "Класс"})`,
            start,
            end,
            backgroundColor: '#1890ff',
          };
        });

        setEvents(mapped);
      } catch (err) {
        message.error("Ошибка загрузки черновика");
      } finally {
        setLoading(false);
      }
    }

    fetchDraft();
  }, [draftId]);

  if (loading) return <Spin />;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-2">Визуализация шаблонной недели</h2>
      <FullCalendar
        plugins={[timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        allDaySlot={false}
        slotMinTime="08:00:00"
        slotMaxTime="18:00:00"
        events={events}
        height="auto"
        headerToolbar={false}
        dayHeaderFormat={{ weekday: 'short' }}
      />
    </div>
  );
};

export default TemplateWeekCalendar;
