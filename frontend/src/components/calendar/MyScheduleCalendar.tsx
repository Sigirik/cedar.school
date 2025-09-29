import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/api/http";
import FullCalendarTemplateView from "@/components/calendar/FullCalendarTemplateView";
import { prepareLessons } from "@/utils/prepareLessons";

type PreparedLesson = ReturnType<typeof prepareLessons>[number];
type ViewType = "timeGridDay" | "timeGridWeek" | "dayGridMonth";

// ===== helpers (даты) =====
function pad2(n: number) { return n < 10 ? `0${n}` : String(n); }
function ymd(d: Date) { return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`; }
function addDays(d: Date, days: number) { const x = new Date(d); x.setDate(x.getDate()+days); return x; }
function addMonths(d: Date, months: number) { const x = new Date(d); x.setMonth(x.getMonth()+months); return x; }
function mondayOf(d: Date) { const x = new Date(d); const w = x.getDay(); const delta = w===0 ? -6 : 1-w; x.setDate(x.getDate()+delta); x.setHours(0,0,0,0); return x; }
function endOfWeekFri(d: Date) { const mon = mondayOf(d); return addDays(mon, 4); }
function startOfMonth(d: Date) { return new Date(d.getFullYear(), d.getMonth(), 1); }
function endOfMonth(d: Date) { return new Date(d.getFullYear(), d.getMonth()+1, 0); }
function mon0Index(d: Date) { return (d.getDay() + 6) % 7; } // Пн=0 … Вс=6
function ruRangeLabel(view: ViewType, anchor: Date) {
  if (view === "timeGridDay") return anchor.toLocaleString("ru-RU",{ day:"numeric", month:"long", year:"numeric" });
  if (view === "timeGridWeek") {
    const a=mondayOf(anchor), b=endOfWeekFri(anchor);
    const fmt=(dt:Date)=>dt.toLocaleString("ru-RU",{ day:"numeric", month:"short" });
    return `${fmt(a)} — ${fmt(b)}`;
  }
  return anchor.toLocaleString("ru-RU",{ month:"long", year:"numeric" });
}

// Для блока FIXME:
function dayOfWeekFromDate(iso: string): number {
  const d = new Date(iso);
  const dow = d.getUTCDay(); // 0=Sun..6=Sat
  return (dow + 6) % 7;      // 0=Mon..6=Sun
}

const STATUS_COLORS: Record<string,string> = { over:"#fecaca", under:"#fef08a", ok:"#bbf7d0" };

// ====== СКЕЛЕТОН (оставляю как в предыдущей версии, если уже есть — можно убрать здесь) ======
function CalendarSkeleton({ view }: { view: ViewType }) {
  if (view === "dayGridMonth") {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <div className="grid grid-cols-7 border-b border-gray-200">
          {Array.from({ length: 7 }).map((_, i) => <div key={i} className="p-2 h-8 bg-gray-50" />)}
        </div>
        <div className="grid grid-cols-7 gap-px bg-gray-200">
          {Array.from({ length: 42 }).map((_, i) => (
            <div key={i} className="bg-white h-24">
              <div className="animate-pulse h-full">
                <div className="h-3 w-12 bg-gray-100 m-2 rounded" />
                <div className="h-3 w-20 bg-gray-100 m-2 rounded" />
                <div className="h-3 w-24 bg-gray-100 m-2 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  const cols = view === "timeGridDay" ? 1 : 5;
  return (
    <div className="rounded-xl overflow-hidden border border-gray-200">
      <div className={`grid ${cols===1 ? "grid-cols-1" : "grid-cols-5"} border-b border-gray-200`}>
        {Array.from({ length: cols }).map((_, i) => <div key={i} className="p-2 h-8 bg-gray-50" />)}
      </div>
      <div className="divide-y divide-gray-200">
        {Array.from({ length: 10 }).map((_, r) => (
          <div key={r} className="grid grid-cols-5 gap-2 p-2">
            {Array.from({ length: cols }).map((_, c) => (
              <div key={c} className="animate-pulse">
                <div className="h-4 w-28 bg-gray-100 rounded mb-2" />
                <div className="h-3 w-40 bg-gray-100 rounded mb-1" />
                <div className="h-3 w-32 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ====== КОМПОНЕНТ ============================================================
export default function MyScheduleCalendar() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string|null>(null);

  const [preparedLessons, setPreparedLessons] = useState<PreparedLesson[]>([]);

  // 🔀 Вид и «якорная» дата периода
  const [view, setView] = useState<ViewType>("timeGridWeek");
  const [anchorDate, setAnchorDate] = useState<Date>(new Date());

  useEffect(() => {
    (async () => {
      setLoading(true); setError(null);
      try {
        const [weekRes, subjectsRes, gradesRes, teachersRes] = await Promise.all([
          api.get("/real_schedule/my/"),
          api.get("/core/subjects/"),
          api.get("/core/grades/"),
          api.get("teachers/"),
        ]);

        // --- ВАЖНО: НЕ МЕНЯТЬ ЭТОТ БЛОК -------------------------------
        //FIXME: это должно быть сделано на беке
        const lessons = weekRes.data.results.map((el: any) => {
            console.log("el", el);
            return {
                ...el,
                start_time: el.start.split("T")?.[1]?.slice(0, -1),
                day_of_week: dayOfWeekFromDate(el.start),
            }
        }) || [];
        // --------------------------------------------------------------

        const prepared = prepareLessons(lessons, subjectsRes.data, gradesRes.data, teachersRes.data);
        setPreparedLessons(prepared);
      } catch (e: any) {
        setError(e?.response?.data?.detail || "Не удалось загрузить расписание");
      } finally { setLoading(false); }
    })();
  }, []);

  // целевые даты периода (на которые раскладываем preparedLessons)
  const targetDates: string[] = useMemo(() => {
    if (view === "timeGridDay") {
      return mon0Index(anchorDate) <= 4 ? [ymd(anchorDate)] : [];
    }
    if (view === "timeGridWeek") {
      const mon = mondayOf(anchorDate);
      return [0,1,2,3,4].map(i => ymd(addDays(mon, i)));
    }
    // month: все будни месяца
    const start = startOfMonth(anchorDate), end = endOfMonth(anchorDate);
    const days: string[] = [];
    for (let d = new Date(start); d <= end; d = addDays(d, 1)) {
      if (mon0Index(d) <= 4) days.push(ymd(d));
    }
    return days;
  }, [view, anchorDate]);

  // events из preparedLessons (кладём lessonId в extendedProps)
  const events = useMemo(() => {
    const out: any[] = [];
    for (const l of preparedLessons) {
      const matches = targetDates.filter(dStr => mon0Index(new Date(`${dStr}T00:00:00`)) === l.day_of_week);
      for (const dateStr of matches) {
        const [h,m] = (l.start_time || "08:00").split(":").map(Number);
        const start = new Date(`${dateStr}T00:00:00`); start.setHours(h, m, 0, 0);
        const end = new Date(start.getTime() + (l.duration_minutes ?? 45) * 60000);

        const primary = l.title?.trim?.() || `${l.grade_name} · ${l.subject_name}`;
        const teacher = l.teacher_name || "";

        out.push({
          id: `${l.id}-${dateStr}`, // уникально в пределах периода
          title: `${l.start_time} · ${l.duration_minutes} мин\n${primary}\n${teacher}`,
          start: start.toISOString(),
          end: end.toISOString(),
          backgroundColor: STATUS_COLORS[l.status || "ok"],
          textColor: "#111827",
          borderColor: "transparent",
          display: "block",
          extendedProps: {
            status: l.status,
            durationMin: l.duration_minutes,
            lessonId: l.id,               // ⬅️ понадобится для навигации
          },
        });
      }
    }
    return out;
  }, [preparedLessons, targetDates]);

  // навигация и подпись периода
  const periodLabel = useMemo(() => ruRangeLabel(view, anchorDate), [view, anchorDate]);
  const goPrev = () => setAnchorDate(d => view==="timeGridDay" ? addDays(d,-1) : view==="timeGridWeek" ? addDays(d,-7) : addMonths(d,-1));
  const goToday = () => setAnchorDate(new Date());
  const goNext = () => setAnchorDate(d => view==="timeGridDay" ? addDays(d, 1) : view==="timeGridWeek" ? addDays(d, 7) : addMonths(d, 1));

  // обработчик клика по занятию
  const handleEventClick = (info: any) => {
    const ep = info?.event?.extendedProps || {};
    const lessonId = ep.lessonId ?? String(info?.event?.id).split("-")[0]; // запасной вариант
    if (lessonId) navigate(`/lesson/${lessonId}`);
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-2xl font-bold">Моё расписание</h1>
        <div className="flex items-center gap-2">
          <button className="px-2 py-1 border rounded" onClick={goPrev} aria-label="Предыдущий период">Назад</button>
          <button className="px-2 py-1 border rounded" onClick={goToday} aria-label="Сегодня">Сегодня</button>
          <button className="px-2 py-1 border rounded" onClick={goNext} aria-label="Следующий период">Вперёд</button>
          <span className="ml-3 text-sm opacity-70">{periodLabel}</span>
        </div>
      </div>

      {/* Переключатели вида */}
      <div className="flex gap-1 mb-3">
        {[
          { key: "timeGridDay", label: "День" },
          { key: "timeGridWeek", label: "Неделя" },
          { key: "dayGridMonth", label: "Месяц" },
        ].map(b => (
          <button
            key={b.key}
            onClick={() => setView(b.key as ViewType)}
            className={`px-3 py-1 rounded border ${view === b.key ? "bg-gray-900 text-white" : "bg-white"}`}
            aria-pressed={view === b.key}
          >
            {b.label}
          </button>
        ))}
      </div>

      {/* Скелетон на загрузке */}
      {loading && <CalendarSkeleton view={view} />}

      {/* Ошибка */}
      {error && !loading && <p className="text-red-600">{error}</p>}

      {/* Календарь после загрузки */}
      {!loading && !error && (
        <FullCalendarTemplateView
          events={events}
          editable={false}
          collisionMap={{}}
          view={view}
          initialDate={view === "timeGridWeek" ? mondayOf(anchorDate) : anchorDate}
          onEventClick={handleEventClick}            // ⬅️ переход по клику
        />
      )}
    </div>
  );
}
