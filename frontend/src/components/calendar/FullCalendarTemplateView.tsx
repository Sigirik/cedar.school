// FullCalendarTemplateView.tsx
//
// принимает массив events (уже подготовленных)
// настраивает:
// фиксированную неделю: 2025-07-07 — 2025-07-11
// отображение ПН–ПТ
// временной диапазон 08:00–17:00
// формат времени: чч:мм
// поддерживает drag-n-drop и resize
// отдаёт обработчики через пропсы: onEventDrop, onEventResize, onEventClick

import React from 'react';
import FullCalendar, { EventDropArg, EventResizeDoneArg, EventClickArg } from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import ruLocale from '@fullcalendar/core/locales/ru';

interface EventItem {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor?: string;
  textColor?: string;
  borderColor?: string;
  display?: string;
  editable?: boolean;
  extendedProps?: Record<string, any>;
}

const FullCalendarTemplateView: React.FC<{
  events: EventItem[];
  height?: string | number;
  editable?: boolean;
  onEventDrop?: (info: EventDropArg) => void;
  onEventResize?: (info: EventResizeDoneArg) => void;
  onEventClick?: (info: EventClickArg) => void;
}> = ({
  events,
  height = 'auto',
  editable = true,
  onEventDrop,
  onEventResize,
  onEventClick,
}) => {
  return (
    <FullCalendar
      plugins={[timeGridPlugin, interactionPlugin]}
      initialView="timeGridWeek"
      initialDate="2025-07-07"
      hiddenDays={[6, 0]}
      allDaySlot={false}
      slotMinTime="08:00:00"
      slotMaxTime="17:00:00"
      slotDuration="00:15:00"
      slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
      dayHeaderFormat={{ weekday: 'short' }}
      locale={ruLocale}
      events={events}
      editable={editable}
      droppable={editable}
      selectable={false}
      height={height}
      headerToolbar={false}
      eventDrop={onEventDrop}
      eventResize={onEventResize}
      eventClick={onEventClick}
      eventDidMount={(info) => {
      // 12 px — можете изменить на любой
       (info.el as HTMLElement).style.borderRadius = '12px';
      }}
      eventContent={(arg) => {
        const lines = arg.event.title.split('\n');
        const time = arg.event.start?.toLocaleTimeString('ru-RU', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });

        const durationMin = arg.event.extendedProps?.durationMin ?? '?';

        return (
          <div
            className="text-xs leading-tight px-1 py-0.5 text-gray-900 h-full"
            style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
            title={arg.event.title.replaceAll('\n', ' | ')}
          >
            <div>{time} · {durationMin} мин</div>
            <div>{lines[1]}</div>
            <div>{lines[2]}</div>
          </div>
        );
      }}
    />
  );
};

export default FullCalendarTemplateView;
