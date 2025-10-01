import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/api/http";
import FullCalendarTemplateView from "@/components/calendar/FullCalendarTemplateView";
import { prepareLessons } from "@/utils/prepareLessons";
import { Button } from "antd";

type PreparedLesson = ReturnType<typeof prepareLessons>[number];
type ViewType = "timeGridDay" | "timeGridWeek" | "dayGridMonth";

// ===== helpers (даты) =====
function pad2(n: number) { return n < 10 ? `0${n}` : String(n); }
function ymd(d: Date) { return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`; }
function addDays(d: Date, days: number) { const x = new Date(d); x.setDate(x.getDate()+days); return x; }
function addMonths(d: Date, months: number) { const x = new Date(d); x.setMonth(x.getMonth()+months); return x; }
function mondayOf(d: Date) { const x = new Date(d); const w = x.getDay(); const delta = w===0 ? -6 : 1-w; x.setDate(x.getDate()+delta); x.setHours(0,0,0,0); return x; }
function endOfWeekSun(d: Date) { const mon = mondayOf(d); return addDays(mon, 6); }
function startOfMonth(d: Date) { return new Date(d.getFullYear(), d.getMonth(), 1); }
function endOfMonth(d: Date) { return new Date(d.getFullYear(), d.getMonth()+1, 0); }
function ruRangeLabel(view: ViewType, anchor: Date) {
  if (view === "timeGridDay") return anchor.toLocaleString("ru-RU",{ day:"numeric", month:"long", year:"numeric" });
  if (view === "timeGridWeek") {
    const a=mondayOf(anchor), b=endOfWeekSun(anchor);
    const fmt=(dt:Date)=>dt.toLocaleString("ru-RU",{ day:"numeric", month:"short" });
    return `${fmt(a)} — ${fmt(b)}`;
  }
  return anchor.toLocaleString("ru-RU",{ month:"long", year:"numeric" });
}

const STATUS_COLORS: Record<string,string> = { over:"#fecaca", under:"#fef08a", ok:"#bbf7d0" };

// ====== СКЕЛЕТОН =============================================================
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
export default function SchedulePage() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string|null>(null);

  const [preparedLessons, setPreparedLessons] = useState<PreparedLesson[]>([]);
  console.log("🚀 ~ SchedulePage ~ preparedLessons:", preparedLessons)

  // 🔀 Вид и «якорная» дата периода
  const [view, setView] = useState<ViewType>("timeGridWeek");
  const [anchorDate, setAnchorDate] = useState<Date>(new Date());

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      setLoading(true);
      setError(null);

      // ⬇️ считаем границы периода по текущим view + anchorDate
      const computeRange = () => {
        if (view === "timeGridDay") {
          const d = new Date(anchorDate);
          return { from: ymd(d), to: ymd(d) };
        }
        if (view === "timeGridWeek") {
          const a = mondayOf(anchorDate);
          const b = endOfWeekSun(anchorDate);
          return { from: ymd(a), to: ymd(b) };
        }
        // dayGridMonth
        const a = startOfMonth(anchorDate);
        const b = endOfMonth(anchorDate);
        return { from: ymd(a), to: ymd(b) };
      };

      const { from, to } = computeRange();

      try {
        // Отправляем оба варианта имён параметров (на случай другой схемы на бэке)
        const [weekRes, subjectsRes, gradesRes, teachersRes] = await Promise.all([
          api.get("/real_schedule/my/", { params: { from, to, date_from: from, date_to: to }, signal: ctrl.signal }),
          api.get("/core/subjects/",   { signal: ctrl.signal }),
          api.get("/core/grades/",     { signal: ctrl.signal }),
          api.get("/teachers/",        { signal: ctrl.signal }),
        ]);

        const lessons = weekRes?.data?.results ?? [];
        const prepared = prepareLessons(lessons, subjectsRes.data, gradesRes.data, teachersRes.data);
        setPreparedLessons(prepared);
      } catch (e: any) {
        if (e?.name === "CanceledError") return;
        setError(e?.response?.data?.detail || "Не удалось загрузить расписание");
      } finally {
        setLoading(false);
      }
    })();

    return () => ctrl.abort();
  }, [view, anchorDate]);

  // === целевые даты периода (локальные YYYY-MM-DD), только будни ===
  const targetDates: string[] = useMemo(() => {
    if (view === "timeGridDay") {
      return [ymd(anchorDate)];
    }
    if (view === "timeGridWeek") {
      const mon = mondayOf(anchorDate);
      return [0,1,2,3,4,5,6].map(i => ymd(addDays(mon, i)));
    }
    // month: все дни месяца
    const start = startOfMonth(anchorDate), end = endOfMonth(anchorDate);
    const days: string[] = [];
    for (let d = new Date(start); d <= end; d = addDays(d, 1)) {
      days.push(ymd(d));
    }
    return days;
  }, [view, anchorDate]);

  // === нормализуем старт/энд урока из разных форматов ===
  const parseStart = (l: any): Date | null => {
    // Возможные поля: start | start_at | (date + start_time)
    const iso: string | undefined =
      l.start || l.start_at ||
      (l.date && l.start_time && `${l.date}T${String(l.start_time).slice(0,5)}:00`);
    if (!iso) return null;
    const d = new Date(iso);
    return isNaN(d.getTime()) ? null : d;
  };

  const durationMin = (l: any) => {
    const x = Number(l.duration_minutes);
    return Number.isFinite(x) && x > 0 ? x : 45;
  };

  const titleParts = (l: any) => {
    const primary = (l.title?.trim?.()) || `${l.grade_name ?? ""} · ${l.subject_name ?? ""}`.trim();
    const teacher = l.teacher_name ?? "";
    return { primary, teacher };
  };

  // === events из preparedLessons ===
  const events = useMemo(() => {
    const out: any[] = [];
    const targetSet = new Set(targetDates); // ["YYYY-MM-DD", ...]

    for (const l of preparedLessons) {
      const start = parseStart(l);
      if (!start) continue;

      // Фильтруем по ЛОКАЛЬНОЙ дате старта
      const localDateStr = ymd(start);
      if (!targetSet.has(localDateStr)) continue;

      const end = new Date(start.getTime() + durationMin(l) * 60000);
      const { primary, teacher } = titleParts(l);
      const hm = `${pad2(start.getHours())}:${pad2(start.getMinutes())}`;

      out.push({
        id: `${l.id}-${localDateStr}`,
        title: `${hm} · ${durationMin(l)} мин\n${primary}\n${teacher}`,
        start,               // <-- Date (без toISOString)
        end,                 // <-- Date
        backgroundColor: STATUS_COLORS[l.status || "ok"],
        textColor: "#111827",
        borderColor: "transparent",
        display: "block",
        extendedProps: {
          status: l.status,
          durationMin: durationMin(l),
          lessonId: l.id,
        },
      });
    }

    return out;
  }, [preparedLessons, targetDates]);

  // навигация и подпись периода
  const periodLabel = useMemo(() => ruRangeLabel(view, anchorDate), [view, anchorDate]);
  const goPrev = () =>
    setAnchorDate(d => view==="timeGridDay" ? addDays(d,-1) : view==="timeGridWeek" ? addDays(d,-7) : addMonths(d,-1));
  const goToday = () => setAnchorDate(new Date());
  const goNext = () =>
    setAnchorDate(d => view==="timeGridDay" ? addDays(d, 1) : view==="timeGridWeek" ? addDays(d, 7) : addMonths(d, 1));

  // обработчик клика по занятию
  const handleEventClick = (info: any) => {
    const ep = info?.event?.extendedProps || {};
    const lessonId = ep.lessonId ?? String(info?.event?.id).split("-")[0];
    if (lessonId) navigate(`/lesson/${lessonId}`);
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-2xl font-bold">Моё расписание</h1>
          <div className="flex items-center gap-2">
            <Button
              className="px-2 py-1 border rounded"
              onClick={goPrev}
              aria-label="Предыдущий период"
            >
              Назад
            </Button>
            <Button
              className="px-2 py-1 border rounded"
              onClick={goToday}
              aria-label="Сегодня"
            >
              Сегодня
            </Button>
            <Button
              className="px-2 py-1 border rounded"
              onClick={goNext}
              aria-label="Следующий период"
            >
              Вперёд
            </Button>
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
            <Button
              key={b.key}
              onClick={() => setView(b.key as ViewType)}
              type={view === (b.key as ViewType) ? "primary" : "default"}
              aria-pressed={view === b.key}
            >
              {b.label}
            </Button>
          ))}
        </div>

        {/* Скелетон на загрузке */}
        {loading && <CalendarSkeleton view={view} />}

        {/* Ошибка */}
        {error && !loading && <p className="text-red-600">{error}</p>}

        {/* Календарь после загрузки */}
        {!loading && !error && (
          <FullCalendarTemplateView
            slotMaxTime={"21:00:00"}
            events={events}
            editable={false}
            collisionMap={{}}
            view={view}
            initialDate={view === "timeGridWeek" ? mondayOf(anchorDate) : anchorDate}
            onEventClick={handleEventClick}
            dayHeaderContent={(arg: any) => {
              const date = arg.date; // JS Date
              const weekday = date.toLocaleDateString("ru-RU", { weekday: "short" }); // Пн, Вт...
              const fullDate = date.toLocaleDateString("ru-RU", { day: "numeric", month: "numeric" });
              return view === "dayGridMonth" ? `${weekday}` : `${weekday} ${fullDate}`;
            }}
          />
        )}
      </div>
    </div>
  );
}
