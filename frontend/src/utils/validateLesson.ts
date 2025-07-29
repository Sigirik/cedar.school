import dayjs from 'dayjs';

export interface PlainLesson {
  id: number;
  grade: number;
  teacher: number;
  day_of_week: number;
  start_time: string;      // 'HH:mm'
  duration_minutes: number;
}

export interface TeacherSlot {
  teacher: number;
  day_of_week: number;
  start: string;           // 'HH:mm'
  end: string;             // 'HH:mm'
}

/**
 * Проверяем, нет ли пересечений по учителю и классу
 * + учитываем teacherAvailability [{ teacher, day_of_week, start: 'HH:mm', end: 'HH:mm' }]
 * Возвращаем массив ошибок (если пустой — всё ок).
 */
export function validateLesson(
  edited: PlainLesson,
  allLessons: PlainLesson[],
  teacherAvailability: TeacherSlot[] = []
): string[] {
  const errors: string[] = [];
  const warnings: string[] = [];
  const { id, teacher, grade, day_of_week, start_time, duration_minutes } = edited;

  // время начала/конца нового урока
  const start = dayjs(start_time, 'HH:mm');
  const end   = start.add(duration_minutes, 'minute');

  // 1. Пересечения для того же учителя
  allLessons
    .filter(l => l.id !== id && l.teacher === teacher && l.day_of_week === day_of_week)
    .forEach(l => {
      const s = dayjs(l.start_time, 'HH:mm');
      const e = s.add(l.duration_minutes, 'minute');
      if (s.isBefore(end) && start.isBefore(e)) {
        errors.push(`Учитель уже занят ${l.start_time}–${e.format('HH:mm')}`);
      }
    });

  // 2. Пересечения для того же класса
  allLessons
    .filter(l => l.id !== id && l.grade === grade && l.day_of_week === day_of_week)
    .forEach(l => {
      const s = dayjs(l.start_time, 'HH:mm');
      const e = s.add(l.duration_minutes, 'minute');
      if (s.isBefore(end) && start.isBefore(e)) {
        errors.push(`В классе уже есть урок ${l.start_time}–${e.format('HH:mm')}`);
      }
    });

  // 3. Доступность учителя
  const slots = teacherAvailability.filter(
    a => a.teacher === teacher && a.day_of_week === day_of_week
  );
  if (slots.length) {
    const insideSomeSlot = slots.some(a => {
      const s = dayjs(a.start_time, 'HH:mm');
      const e = dayjs(a.end_time,   'HH:mm');
      return !start.isBefore(s) && !end.isAfter(e);
    });
    if (!insideSomeSlot) warnings.push('Учитель недоступен в это время');
  }

  return { errors, warnings };
}
