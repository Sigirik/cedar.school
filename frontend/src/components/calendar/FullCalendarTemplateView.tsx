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
import FullCalendar from '@fullcalendar/react';
import type { EventClickArg } from '@fullcalendar/core';
import type { EventDropArg, EventResizeDoneArg } from '@fullcalendar/interaction';
import timeGridPlugin from '@fullcalendar/timegrid';
import dayGridPlugin from "@fullcalendar/daygrid"
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

interface Props {
  events: EventItem[];
  height?: string | number;
  editable?: boolean;
  onEventDrop?: (info: EventDropArg) => void;
  onEventResize?: (info: EventResizeDoneArg) => void;
  onEventClick?: (info: EventClickArg) => void;
  collisionMap?: Record<string, 'error' | 'warning'>;
  initialDate?: string | Date;                           // новое (якорь)
  view?: "timeGridDay" | "timeGridWeek" | "dayGridMonth"; // новое (вид)
}

const FullCalendarTemplateView: React.FC<Props> = ({
  events,
  height = 'auto',
  editable = true,
  onEventDrop,
  onEventResize,
  onEventClick,
  collisionMap,
  initialDate,
  view = "timeGridWeek",
}) => {
  return (
    <>
      <FullCalendar
        key={`${view}-${String(initialDate)}`}           // безопасный ремоунт при смене
        plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
        initialView={view}
        initialDate={initialDate ?? "2025-07-07"}
        hiddenDays={view === "dayGridMonth" ? [] : [0, 6]} // в месяце показываем все дни
        allDaySlot={false}
        slotMinTime="08:00:00"
        slotMaxTime="17:00:00"
        slotDuration="00:15:00"
        slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
        dayHeaderFormat={{ weekday: 'short' }}
        locales={[ruLocale]}
        locale="ru"
        events={events}
        eventClassNames={(arg) => {
          const sev = collisionMap?.[arg.event.id];
          return sev === 'error' ? ['lsn-error']
               : sev === 'warning' ? ['lsn-warning']
               : [];
        }}
        editable={editable}
        droppable={editable}
        selectable={false}
        height={height}
        headerToolbar={false}
        eventDrop={onEventDrop}
        eventResize={onEventResize}
        eventClick={onEventClick}
        eventDidMount={(info) => {
          (info.el as HTMLElement).style.borderRadius = '12px';
        }}
        eventContent={(arg) => {
          const lines = arg.event.title.split('\n');
          while (lines.length < 3) lines.push('');
          const time = arg.event.start?.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          });
          const durationMin = (arg.event.extendedProps as any)?.durationMin ?? '?';

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
      <style>{`
        .fc .lsn-error {
          border: 2px solid #dc2626 !important;
          background: rgba(220, 38, 38, 0.12) !important;
        }
        .fc .lsn-warning {
          border: 2px solid #ca8a04 !important;
          background: rgba(202, 138, 4, 0.10) !important;
        }
      `}</style>
    </>
  );
};

export default FullCalendarTemplateView;

