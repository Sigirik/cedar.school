// utils/prepareLessons.ts

export type LessonRaw = {
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;
  start_time: string;
  duration_minutes: number;
  type?: string;
};

export type EnrichedLesson = LessonRaw & {
  subject_name: string;
  grade_name: string;
  teacher_name: string;
  status?: 'under' | 'ok' | 'over';
};

export function prepareLessons(
  lessons: LessonRaw[],
  subjects: { id: number; name: string }[],
  grades: { id: number; name: string }[],
  teachers: { id: number; first_name: string; last_name: string; middle_name?: string }[],
  weeklyNorms: {
    subject: number;
    grade: number;
    lessons_per_week: number;
    courses_per_week: number;
  }[] = []
): EnrichedLesson[] {
  const getName = (id: number, list: any[], field = 'name') =>
    list.find((i) => i.id === id)?.[field] || `ID ${id}`;

  const formatTeacher = (t: any) => {
    const initials =
      (t.first_name?.[0] || '') + '.' +
      (t.middle_name?.[0] || '') + '.';
    return `${t.last_name} ${initials}`;
  };

  const teacherMap = Object.fromEntries(
    teachers.map((t) => [t.id, formatTeacher(t)])
  );

  const countMap: Record<string, number> = {};
  lessons.forEach((l) => {
    const key = `${l.grade}-${l.subject}-${l.type || 'lesson'}`;
    countMap[key] = (countMap[key] || 0) + 1;
  });

  return lessons.map((l) => {
    const norm = weeklyNorms.find((n) => n.grade === l.grade && n.subject === l.subject);
    const count = countMap[`${l.grade}-${l.subject}-${l.type || 'lesson'}`] || 0;
    let status: 'ok' | 'under' | 'over' | undefined;
    if (norm) {
      const target = l.type === 'course' ? norm.courses_per_week : norm.lessons_per_week;
      if (count > target) status = 'over';
      else if (count < target) status = 'under';
      else status = 'ok';
    }

    return {
      ...l,
      start_time: l.start_time.slice(0, 5),
      subject_name: getName(l.subject, subjects),
      grade_name: getName(l.grade, grades),
      teacher_name: teacherMap[l.teacher] || `ID ${l.teacher}`,
      status,
    };
  });
}
