// utils/prepareLessons.ts

export function formatTeacher(t: { last_name: string; first_name?: string; middle_name?: string }) {
  if (!t) return '';
  const first = t.first_name ? `${t.first_name[0]}.` : '';
  const middle = t.middle_name ? `${t.middle_name[0]}.` : '';
  return `${t.last_name} ${first}${middle}`.trim();
}

export function formatGrade(g: { name: string }) {
  return g ? g.name : '';
}

export function formatSubject(s: { name: string }) {
  return s ? s.name : '';
}

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
    subject: number | { id: number; name?: string };
    grade: number | { id: number; name?: string };
    lessons_per_week: number;
    courses_per_week: number;
  }[] = []
): EnrichedLesson[] {
  const getName = (id: number, list: any[], field = 'name') =>
    list.find((i) => i.id === id)?.[field] || `ID ${id}`;

  // --- теперь экспортируемую функцию formatTeacher используем тут ---
  const teacherMap = Object.fromEntries(
    teachers.map((t) => [t.id, formatTeacher(t)])
  );

  // ---- ПЛОСКИЕ нормы ----
  const flatNorms = weeklyNorms.map((n) => ({
    subject: typeof n.subject === 'object' ? n.subject.id : n.subject,
    grade: typeof n.grade === 'object' ? n.grade.id : n.grade,
    lessons_per_week: n.lessons_per_week,
    courses_per_week: n.courses_per_week,
  }));

  const countMap: Record<string, number> = {};
  lessons.forEach((l) => {
    const key = `${l.grade}-${l.subject}-${l.type || 'lesson'}`;
    countMap[key] = (countMap[key] || 0) + 1;
  });

  return lessons.map((l) => {
    const norm = flatNorms.find((n) => n.grade === l.grade && n.subject === l.subject);
    const count = countMap[`${l.grade}-${l.subject}-${l.type || 'lesson'}`] || 0;
    let status: 'ok' | 'under' | 'over' | undefined;
    if (norm) {
      const target = l.type === 'course' ? norm.courses_per_week : norm.lessons_per_week;
      if (count > target) status = 'over';
      else if (count < target) status = 'under';
      else status = 'ok';
    }

    // --- используем наши новые универсальные функции для формирования "name" полей ---
    const subjectObj = subjects.find(s => s.id === l.subject);
    const gradeObj = grades.find(g => g.id === l.grade);
    const teacherObj = teachers.find(t => t.id === l.teacher);

    return {
      ...l,
      start_time: l.start_time.slice(0, 5),
      subject_name: formatSubject(subjectObj),
      grade_name: formatGrade(gradeObj),
      teacher_name: formatTeacher(teacherObj),
      status,
    };
  });
}
