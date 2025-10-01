import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, RefreshCw, Users, CalendarClock } from "lucide-react";

// ---- Types aligned to the provided API ----
export type OpenLessonApiItem = {
  room_id: number;
  public_slug: string | null;
  status: "PENDING" | "OPEN" | "LIVE" | "ENDED" | string;
  scheduled_start?: string | null; // ISO (UTC)
  scheduled_end?: string | null;   // ISO (UTC)
  lesson: {
    id: number;
    subject: { id: number; name: string } | null;
    grade: { id: number; name: string } | null;
    teacher?: { id: number; fio: string } | null;
    start?: string | null; // ISO with TZ
    end?: string | null;   // ISO with TZ
    duration_minutes?: number | null;
    lesson_type?: { id: number; key: string; label: string } | null;
    topic_order?: number | null;
    topic_title?: string | null;
  };
};

// ---- Utils ----
function toDateSafe(v?: string | null): Date | null {
  if (!v) return null;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

function formatDateRange(startISO?: string | null, endISO?: string | null, locale: string = "ru-RU"): string {
  const s = toDateSafe(startISO);
  const e = toDateSafe(endISO);
  if (!s) return "—";

  const sameDay = e && s.toDateString() === e.toDateString();
  const dateFmt: Intl.DateTimeFormatOptions = { weekday: "short", day: "2-digit", month: "short" };
  const timeFmt: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" };

  const datePart = new Intl.DateTimeFormat(locale, dateFmt).format(s);
  const startTime = new Intl.DateTimeFormat(locale, timeFmt).format(s);
  const endTime = e ? new Intl.DateTimeFormat(locale, timeFmt).format(e) : "";
  if (sameDay && endTime) return `${datePart} · ${startTime}–${endTime}`;

  if (endTime) {
    const endDate = new Intl.DateTimeFormat(locale, dateFmt).format(e as Date);
    return `${datePart} ${startTime} → ${endDate} ${endTime}`;
  }
  return `${datePart} · ${startTime}`;
}

function subjectFrom(item: OpenLessonApiItem): string {
  return item.lesson?.subject?.name || "Предмет";
}

function classFrom(item: OpenLessonApiItem): string {
  const name = item.lesson?.grade?.name;
  return name ? `Класс: ${name}` : "Класс: —";
}

function startFrom(item: OpenLessonApiItem): string | undefined {
  // приоритет фактического времени урока; запасной вариант — расписание
  return (item.lesson?.start ?? undefined) || (item.scheduled_start ?? undefined);
}

function endFrom(item: OpenLessonApiItem): string | undefined {
  return (item.lesson?.end ?? undefined) || (item.scheduled_end ?? undefined);
}

function getCSRFCookie(name = "csrftoken"): string | null {
  const match = document.cookie.match(new RegExp(`(^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[2]) : null;
}

// ---- API ----
async function apiFetchOpenLessons(hours = 48, init?: RequestInit): Promise<OpenLessonApiItem[]> {
  const res = await fetch(`/api/rooms/open-lessons/?hours=${hours}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`Не удалось загрузить список (${res.status})`);
  const data = await res.json();
  return Array.isArray(data) ? (data as OpenLessonApiItem[]) : (data.results ?? []);
}

async function apiJoinPublicRoom(public_slug: string, displayName = "Гость"): Promise<{ join_url?: string }>
{
  const csrf = getCSRFCookie();
  const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "application/json" };
  if (csrf) headers["X-CSRFToken"] = csrf;

  const res = await fetch(`/api/rooms/public/${encodeURIComponent(public_slug)}/join/`, {
    method: "POST",
    headers,
    body: JSON.stringify({ display_name: displayName }),
  });
  if (!res.ok) throw new Error(`Не удалось подключиться (${res.status})`);
  return res.json();
}

function canJoin(item: OpenLessonApiItem): boolean {
  // Можно подключаться только если есть public_slug и урок не завершён
  return Boolean(item.public_slug) && item.status !== "ENDED";
}

// ---- Component ----
export default function OpenLessonsFeed({ hours = 48 }: { hours?: number }) {
  const [items, setItems] = useState<OpenLessonApiItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [joiningSlug, setJoiningSlug] = useState<string | null>(null);

  const locale = useMemo(() => (navigator?.language || "ru-RU"), []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetchOpenLessons(hours);
      setItems(data);
    } catch (e: any) {
      setError(e?.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hours]);

  async function handleJoin(slug: string) {
    try {
      setJoiningSlug(slug);
      const { join_url } = await apiJoinPublicRoom(slug, "Гость");
      if (join_url) {
        window.location.href = join_url;
      } else {
        throw new Error("join_url не получен от сервера");
      }
    } catch (e: any) {
      alert(e?.message || "Не удалось подключиться к уроку");
    } finally {
      setJoiningSlug(null);
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Открытые уроки · ближайшие {hours} ч</h1>
        <Button variant="outline" onClick={load} disabled={loading} className="gap-2">
          <RefreshCw className={loading ? "animate-spin h-4 w-4" : "h-4 w-4"} />
          Обновить
        </Button>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-3">
          <AlertCircle className="h-5 w-5 mt-0.5" />
          <div>
            <div className="font-medium">Ошибка</div>
            <div className="opacity-80">{error}</div>
          </div>
        </div>
      )}

      {loading && !items && (
        <div className="text-muted-foreground">Загрузка…</div>
      )}

      {items && items.length === 0 && (
        <EmptyState />
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items?.map((item) => (
          <div key={`${item.room_id}`}>
            <Card className="rounded-2xl shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between gap-3">
                  <span className="truncate">{subjectFrom(item)}</span>
                  <span className="text-xs font-normal text-muted-foreground flex items-center gap-1">
                    <Users className="h-4 w-4" /> {classFrom(item)}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CalendarClock className="h-4 w-4" />
                  <span>{formatDateRange(startFrom(item), endFrom(item), locale)}</span>
                </div>

                <div className="mt-4">
                  <Button
                    className="w-full"
                    onClick={() => item.public_slug && handleJoin(item.public_slug)}
                    disabled={!canJoin(item) || joiningSlug === item.public_slug!}
                  >
                    {canJoin(item) ? "Подключаем…" : item.public_slug && joiningSlug === item.public_slug ? "Подключиться" : "Недоступно"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="rounded-2xl">
      <CardContent className="py-8 text-center text-muted-foreground">
        За ближайшие 48 часов открытых уроков нет.
      </CardContent>
    </Card>
  );
}
