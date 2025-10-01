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
  start_time: string;      // 'HH:mm'
  end_time: string;        // 'HH:mm'
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
): { errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  const { id, teacher, grade, day_of_week, start_time, duration_minutes } = edited;

  const newStart = dayjs(start_time, 'HH:mm');
  const newEnd   = newStart.add(duration_minutes, 'minute');

  // пересечения по учителю
  allLessons
    .filter(lesson => lesson.id !== id && lesson.teacher === teacher && lesson.day_of_week === day_of_week)
    .forEach(lesson => {
      const lessonStart = dayjs(lesson.start_time, 'HH:mm');
      const lessonEnd   = lessonStart.add(lesson.duration_minutes, 'minute');
      if (lessonStart.isBefore(newEnd) && newStart.isBefore(lessonEnd)) {
        errors.push(`Учитель уже занят ${lesson.start_time}–${lessonEnd.format('HH:mm')}`);
      }
    });

  // пересечения по классу
  allLessons
    .filter(lesson => lesson.id !== id && lesson.grade === grade && lesson.day_of_week === day_of_week)
    .forEach(lesson => {
      const lessonStart = dayjs(lesson.start_time, 'HH:mm');
      const lessonEnd   = lessonStart.add(lesson.duration_minutes, 'minute');
      if (lessonStart.isBefore(newEnd) && newStart.isBefore(lessonEnd)) {
        errors.push(`В классе уже есть урок ${lesson.start_time}–${lessonEnd.format('HH:mm')}`);
      }
    });

  // доступность учителя
  const slotsToday = teacherAvailability.filter(
    slot => slot.teacher === teacher && slot.day_of_week === day_of_week
  );
  if (slotsToday.length) {
    const insideSomeSlot = slotsToday.some(slot => {
      const slotStart = dayjs(slot.start_time, 'HH:mm');
      const slotEnd   = dayjs(slot.end_time,   'HH:mm');
      return !newStart.isBefore(slotStart) && !newEnd.isAfter(slotEnd);
    });
    if (!insideSomeSlot) warnings.push('Учитель недоступен в это время');
  }

  return { errors, warnings };
}
