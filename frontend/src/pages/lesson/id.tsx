import React from "react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Calendar, Clock, User, GraduationCap, TriangleAlert, Video } from "lucide-react";
import { toast } from "sonner";
import axios, { AxiosError } from "axios";
// ⬇️ УТОЧНИ путь до prepareLessons под свой проект (например, '@/utils/prepareLessons' или '@/lib/prepareLessons')
import { prepareLessons } from "@/utils/prepareLessons";

// --- Types ---
interface Teacher { fio?: string }
interface Grade { name?: string }
interface Subject { name?: string }
interface Lesson {
  id: string | number
  title?: string | null

  // старый формат
  start?: string // ISO
  end?: string   // ISO
  teacher?: Teacher
  grade?: Grade
  subject?: Subject

  // новый формат
  date?: string               // "YYYY-MM-DD"
  start_time?: string         // "HH:MM:SS"
  duration_minutes?: number
  status?: string
}

// после prepareLessons обычно появляются *_name
type PreparedLesson = Lesson & {
  subject_name?: string
  grade_name?: string
  teacher_name?: string
}

interface Room {
  id: number
  type?: string
  lesson?: number
  jitsi_domain?: string
  jitsi_room?: string
  jitsi_env?: string
  join_url?: string | null
  is_open?: boolean
  public_slug?: string | null
  status?: string | null
  scheduled_start?: string | null
  scheduled_end?: string | null
  started_at?: string | null
  ended_at?: string | null
  available_from?: string | null
  available_until?: string | null
  is_join_allowed_now?: boolean
  recording_status?: string | null
  recording_file_url?: string | null
  created_at?: string | null
}

// --- Utilities ---
const tz = "Europe/Amsterdam";

function formatRange(startISO?: string, endISO?: string) {
  if (!startISO) return "—";
  const start = new Date(startISO);
  const end = endISO ? new Date(endISO) : undefined;
  const dateFmt = new Intl.DateTimeFormat("ru-RU", {
    timeZone: tz,
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const timeFmt = new Intl.DateTimeFormat("ru-RU", {
    timeZone: tz,
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateStr = dateFmt.format(start);
  const timeStr = end ? `${timeFmt.format(start)}–${timeFmt.format(end)}` : timeFmt.format(start);
  return `${dateStr}, ${timeStr}`;
}

// Показать только время начала, если длительность уже выводится отдельно
function formatDateLabel(startISO?: string, endISO?: string, startOnly?: boolean) {
  if (!startISO) return "—";
  const start = new Date(startISO);
  const end = endISO ? new Date(endISO) : undefined;
  const dateFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" });
  const timeFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, hour: "2-digit", minute: "2-digit" });
  const dateStr = dateFmt.format(start);
  if (startOnly) return `${dateStr}, ${timeFmt.format(start)}`;
  const timeStr = end ? `${timeFmt.format(start)}–${timeFmt.format(end)}` : timeFmt.format(start);
  return `${dateStr}, ${timeStr}`;
}

function fioToSurnameWithInitials(fio?: string) {
  if (!fio) return "—";
  const parts = fio.trim().split(/\s+/);
  if (parts.length === 0) return "—";
  const [surname, name, patronymic] = [parts[0], parts[1], parts[2]];
  const initials = [name, patronymic]
    .filter(Boolean)
    .map((p) => (p ? p[0].toUpperCase() + "." : ""))
    .join("");
  return initials ? `${surname} ${initials}` : surname;
}

// --- Data fetching hook (axios + prepareLessons) ---
function useLesson(lessonId?: string) {
  const [data, setData] = useState<PreparedLesson | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "notFound">("idle");

  useEffect(() => {
    if (!lessonId) return;
    setStatus("loading");
    const ctrl = new AbortController();

    (async () => {
      try {
        const [lessonRes, subjectsRes, gradesRes, teachersRes] = await Promise.all([
          axios.get<Lesson | Lesson[]>(`/api/real_schedule/lessons/${lessonId}` , { signal: ctrl.signal }),
          axios.get(`/api/core/subjects/`, { signal: ctrl.signal }),
          axios.get(`/api/core/grades/`,   { signal: ctrl.signal }),
          axios.get(`/api/teachers/`,      { signal: ctrl.signal }),
        ]);

        // поддержка разных форматов ответа (объект или {results:[]})
        const raw = (lessonRes as any)?.data?.results ?? lessonRes.data;
        const rawArr: Lesson[] = Array.isArray(raw) ? raw : [raw];

        const preparedArr: PreparedLesson[] = prepareLessons(
          rawArr,
          subjectsRes.data,
          gradesRes.data,
          teachersRes.data
        );

        const prepared = preparedArr?.[0] ?? null;
        setData(prepared);
        setStatus("success");
      } catch (e: unknown) {
        // отмена запроса
        // @ts-expect-error возможны разные типы cancel
        if ((axios as any).isCancel?.(e) || (e as any)?.name === "CanceledError") return;
        const err = e as AxiosError<any>;
        if (err.response?.status === 404) {
          setStatus("notFound");
          return;
        }
        console.error(err);
        setStatus("error");
        toast.error("Не удалось загрузить урок");
      }
    })();

    return () => ctrl.abort();
  }, [lessonId]);

  return { data, status } as const;
}


// --- Webinar URL (lazy) ---
function useWebinarUrl(lessonId?: string, initial?: string | null) {
  const [url, setUrl] = useState<string | null>(initial ?? null);
  const [room, setRoom] = useState<Room | null>(null);
  const [loading, setLoading] = useState(false);
  const [tried, setTried] = useState(false);

  useEffect(() => {
    setUrl(initial ?? null);
  }, [initial]);

  useEffect(() => {
    if (!lessonId) return;

    const ctrl = new AbortController();
    setLoading(true);
    (async () => {
      try {
        const res = await axios.get(`/api/rooms/by-lesson/${lessonId}/`, { signal: ctrl.signal });
        const roomObj = res.data as Room;
        setRoom(roomObj);
        const value = (roomObj?.join_url ?? (res as any).data?.webinar_url ?? (res as any).data?.url ?? (res as any).data?.room_url) as string | null;
        setUrl(value || null);
      } catch (e: any) {
        if ((axios as any).isCancel?.(e) || e?.name === "CanceledError") return;
        setRoom(null);
        if (!initial) setUrl(null);
      } finally {
        setLoading(false);
        setTried(true);
      }
    })();

    return () => ctrl.abort();
  }, [lessonId, initial]);

  return { url, room, loading, tried } as const;
}

// перевод машинных статусов в RU
const tRoomStatus = (s?: string | null) => {
  switch ((s || "").toUpperCase()) {
    case "SCHEDULED": return "Запланирована";
    case "OPEN":      return "Открыта";
    case "LIVE":
    case "STARTED":   return "Идёт";
    case "ENDED":     return "Завершена";
    case "CLOSED":    return "Закрыта";
    case "PENDING":   return "Ожидается";
    default:          return "—";
  }
};

// --- Skeletons ---
function LessonSkeleton() {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="space-y-2">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-8 w-3/5" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[0,1,2,3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-5 w-5 rounded-full" />
              <div className="space-y-2 w-full">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-40" />
              </div>
            </div>
          ))}
        </div>
        <Skeleton className="h-4 w-24" />
      </CardContent>
    </Card>
  );
}

// --- Not Found ---
function NotFound({ onBack }: { onBack: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center text-center gap-4 py-20">
      <TriangleAlert className="h-10 w-10" />
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Урок не найден</h2>
        <p className="text-sm text-muted-foreground">Возможно, ссылка устарела или у вас нет доступа.</p>
      </div>
      <div className="flex gap-3">
        <Button onClick={onBack} variant="secondary"><ArrowLeft className="h-4 w-4 mr-2"/>Назад</Button>
        <Button asChild>
          <Link to="/schedule">Назад в расписание</Link>
        </Button>
      </div>
    </div>
  );
}

// --- Main ---
export default function LessonPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: lesson, status } = useLesson(id);
  const { url: webinarUrl, room } = useWebinarUrl(id, (lesson as any)?.webinar_url ?? (lesson as any)?.webinar?.url ?? null);
  const [joining, setJoining] = useState(false);

  // поддержка обоих форматов времени: (start/end) ИЛИ (date + start_time + duration)
  const startISO = useMemo(() => {
    if (lesson?.start) return lesson.start;
    if (lesson?.date && lesson?.start_time) {
      return new Date(`${lesson.date}T${lesson.start_time}`).toISOString();
    }
    return undefined;
  }, [lesson]);

  const dateLabel = formatDateLabel(startISO);

  const roomTime = useMemo(() => {
    if (!room?.scheduled_start) return "—";
    const start = new Date(room.scheduled_start);
    const end = room.scheduled_end ? new Date(room.scheduled_end) : undefined;
    const dateFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" });
    const timeFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, hour: "2-digit", minute: "2-digit" });
    const dateStr = dateFmt.format(start);
    const timeStr = end ? `${timeFmt.format(start)}–${timeFmt.format(end)}` : timeFmt.format(start);
    return `${dateStr}, ${timeStr}`;
  }, [room]);

  const roomDateLabel = useMemo(() => {
    if (!room?.scheduled_start) return "—";
    const start = new Date(room.scheduled_start);
    const fmt = new Intl.DateTimeFormat("ru-RU", {
      timeZone: tz, weekday: "short", day: "2-digit", month: "2-digit", year: "numeric"
    });
    return fmt.format(start);
  }, [room]);

  const roomTimeLabel = useMemo(() => {
    if (!room?.scheduled_start) return "—";
    const start = new Date(room.scheduled_start);
    const end = room.scheduled_end ? new Date(room.scheduled_end) : undefined;
    const fmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, hour: "2-digit", minute: "2-digit" });
    return end ? `${fmt.format(start)}–${fmt.format(end)}` : fmt.format(start);
  }, [room]);

  const tStatus = tRoomStatus(room?.status);

  const availWindow = useMemo(() => {
    if (!room?.available_from || !room?.available_until) return "—";
    const a = new Date(room.available_from);
    const b = new Date(room.available_until);
    const dateFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, day: "2-digit", month: "2-digit", year: "numeric" });
    const timeFmt = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, hour: "2-digit", minute: "2-digit" });
    const same = dateFmt.format(a) === dateFmt.format(b);
    if (same) return `${dateFmt.format(a)}, ${timeFmt.format(a)}–${timeFmt.format(b)}`;
    return `${dateFmt.format(a)} ${timeFmt.format(a)} — ${dateFmt.format(b)} ${timeFmt.format(b)}`;
  }, [room]);

  const joinAllowedLabel = room?.is_join_allowed_now ? "Да" : "Нет";
  const joinAllowedClass = room?.is_join_allowed_now ? "text-green-600 dark:text-green-400" : "text-muted-foreground";
  const statusBadgeClass = (() => {
    const s = (room?.status || "").toUpperCase();
    if (["OPEN", "LIVE", "STARTED"].includes(s)) return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300";
    if (["ENDED", "CLOSED"].includes(s)) return "bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-300";
    return "bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-300";
  })();

  const endISO = useMemo(() => {
    if (lesson?.end) return lesson.end;
    if (startISO && lesson?.duration_minutes) {
      const start = new Date(startISO).getTime();
      return new Date(start + lesson.duration_minutes * 60_000).toISOString();
    }
    return undefined;
  }, [lesson, startISO]);



  const title = useMemo(() => {
    if (!lesson) return "";
    return lesson.title?.trim() || (lesson as any).subject_name || lesson.subject?.name || "Занятие";
  }, [lesson]);

  const teacher = useMemo(() => (lesson as any)?.teacher_name || fioToSurnameWithInitials(lesson?.teacher?.fio), [lesson]);
  const grade = (lesson as any)?.grade_name || lesson?.grade?.name || "—";
  // dateLabel вычислим ниже после подсчёта длительности
  const subject = (lesson as any)?.subject_name || lesson?.subject?.name || "—";

  const durationDisplay = useMemo(() => {
    if (lesson?.start && lesson?.end) {
      const diff = Math.max(0, Math.round((new Date(lesson.end).getTime() - new Date(lesson.start).getTime()) / 60000));
      return `${diff} мин`;
    }
    if (lesson?.duration_minutes) return `${lesson.duration_minutes} мин`;
    return "—";
  }, [lesson]);

  // Урок: отдельные метки даты и времени
  const lessonDateLabel = useMemo(() => {
    if (!startISO) return "—";
    const start = new Date(startISO);
    const fmt = new Intl.DateTimeFormat("ru-RU", {
      timeZone: tz, weekday: "short", day: "2-digit", month: "2-digit", year: "numeric",
    });
    return fmt.format(start);
  }, [startISO]);

  const lessonTimeLabel = useMemo(() => {
    if (!startISO) return "—";
    const start = new Date(startISO);
    const tf = new Intl.DateTimeFormat("ru-RU", { timeZone: tz, hour: "2-digit", minute: "2-digit" });
    // если длительность уже показываем отдельно — выводим только время начала
    if (durationDisplay !== "—") return tf.format(start);
    // иначе, если есть endISO — показываем диапазон
    if (endISO) return `${tf.format(start)}–${tf.format(new Date(endISO))}`;
    return tf.format(start);
  }, [startISO, endISO, durationDisplay]);

  const handleJoin = async () => {
    if (!room?.id || joining) return;
    try {
      setJoining(true);
      const res = await axios.post(`/api/rooms/${room.id}/join/`);
      const url = (res.data?.join_url ?? res.data?.url ?? res.data) as string | null;
      if (url && typeof url === "string") {
      window.open(url, "_blank", "noopener,noreferrer");
    } else {
      toast.error("Не удалось получить ссылку для подключения");
    }
    } catch (e) {
      console.error(e);
      toast.error("Не удалось подключиться к уроку");
    } finally {
      setJoining(false);
    }
  };


  if (status === "loading" || status === "idle") {
    return (
      <div className="container mx-auto p-4 md:p-6">
        <div className="mb-4">
          <Button onClick={() => navigate(-1)} variant="ghost" className="px-0"><ArrowLeft className="h-4 w-4 mr-2"/>Назад</Button>
        </div>
        <LessonSkeleton />
      </div>
    );
  }

  if (status === "notFound") {
    return (
      <div className="container mx-auto p-4 md:p-6">
        <NotFound onBack={() => navigate(-1)} />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="container mx-auto p-4 md:p-6">
        <div className="mb-4">
          <Button onClick={() => navigate(-1)} variant="ghost" className="px-0"><ArrowLeft className="h-4 w-4 mr-2"/>Назад</Button>
        </div>
        <Alert variant="destructive">
          <TriangleAlert className="h-4 w-4" />
          <AlertTitle>Ошибка</AlertTitle>
          <AlertDescription>Не удалось загрузить урок</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto p-4 md:p-6">
        <div className="mb-4 flex items-center gap-3">
          <Button onClick={() => navigate(-1)} variant="ghost" className="px-0"><ArrowLeft className="h-4 w-4 mr-2"/>Назад</Button>
          <Button variant="secondary" asChild><Link to="/schedule">В расписание</Link></Button>
        </div>

        <Card className="w-full max-w-2xl">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm text-muted-foreground">{subject || "Предмет"}</div>
                <CardTitle className="text-2xl md:text-3xl leading-tight">{title}</CardTitle>
              </div>
              <div className="shrink-0">
                {(room?.is_join_allowed_now && webinarUrl) ? (
                  <Button asChild variant={"secondary"} onClick={handleJoin}>
                    <Video className="h-4 w-4 mr-2" /> Подключиться к уроку
                  </Button>
                ) : (
                  <Button disabled>
                    <Video className="h-4 w-4 mr-2" /> Подключиться к уроку
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 mt-0.5" />
                <div>
                  <div className="text-xs uppercase text-muted-foreground">Дата/время</div>
                  <div className="text-sm md:text-base font-medium">
                    <div>{lessonDateLabel}</div>
                    <div className="text-muted-foreground">{lessonTimeLabel}</div>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <User className="h-5 w-5 mt-0.5" />
                <div>
                  <div className="text-xs uppercase text-muted-foreground">Учитель</div>
                  <div className="text-sm md:text-base font-medium">{teacher}</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <GraduationCap className="h-5 w-5 mt-0.5" />
                <div>
                  <div className="text-xs uppercase text-muted-foreground">Класс</div>
                  <div className="text-sm md:text-base font-medium">{grade}</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Clock className="h-5 w-5 mt-0.5" />
                <div>
                  <div className="text-xs uppercase text-muted-foreground">Длительность</div>
                  <div className="text-sm md:text-base font-medium">{durationDisplay}</div>
                </div>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">{subject}</div>
          </CardContent>
        </Card>

        {/* Комната — карточка */}
        <div className="mt-6 w-full max-w-2xl">
          <Card>
            <CardHeader className="pb-3 gap-3 flex">
              <CardTitle className="text-xl">Комната</CardTitle>
            </CardHeader>
            <CardContent>
              {!room ? (
                <div className="text-sm text-muted-foreground">Данных о комнате нет</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs uppercase text-muted-foreground">Время</div>
                    <div className="text-sm md:text-base font-medium">
                      <div>{roomDateLabel}</div>
                      <div className="text-muted-foreground">{roomTimeLabel}</div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-3 items-start">
                    <div className="text-xs uppercase text-muted-foreground">Статус</div>
                    {/* <div className="text-sm md:text-base font-medium">{tStatus}</div> */}
                    <span className={`px-2 py-1 text-xs rounded-full ${statusBadgeClass}`}>
                      {tStatus}
                    </span>
                  </div>
                  {/* <div>
                    <div className="text-xs uppercase text-muted-foreground">Доступность</div>
                    <div className="text-sm md:text-base font-medium">
                      <div>{availParts.fromDate}, {availParts.fromTime}</div>
                      <div className="text-muted-foreground">{availParts.untilDate}, {availParts.untilTime}</div>
                    </div>
                  </div> */}
                  <div>
                    <div className="text-xs uppercase text-muted-foreground">Можно подключиться сейчас</div>
                    <div className={`text-sm md:text-base font-medium ${joinAllowedClass}`}>{joinAllowedLabel}</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Домашка — заглушка */}
        <div className="mt-6 w-full max-w-2xl">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-xl">Домашка</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Пока нет заданий
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
