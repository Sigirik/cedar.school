// utils/prepareLessons.ts

export function formatTeacher(
  teacher?: { last_name?: string; first_name?: string; middle_name?: string } | null
) {
  if (!teacher || !teacher.last_name) return '';
  const firstInitial = teacher.first_name ? `${teacher.first_name[0]}.` : '';
  const middleInitial = teacher.middle_name ? `${teacher.middle_name[0]}.` : '';
  return `${teacher.last_name} ${firstInitial}${middleInitial}`.trim();
}

export function formatGrade(grade?: { name?: string } | null) {
  return grade?.name ?? '';
}

export function formatSubject(subject?: { name?: string } | null) {
  return subject?.name ?? '';
}

export type LessonRaw = {
  id: number;
  subject: number;
  grade: number;
  teacher: number;
  day_of_week: number;     // 0=Пн … 4=Пт (или как у вас заведено)
  start_time: string;      // 'HH:mm' или 'HH:mm:ss'
  duration_minutes: number;
  type?: string;
};

export type PreparedLesson = LessonRaw & {
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
): PreparedLesson[] {
  // Нормализуем нормы до простых id
  const flatNorms = weeklyNorms.map((norm) => ({
    subject: typeof norm.subject === 'object' ? norm.subject.id : norm.subject,
    grade: typeof norm.grade === 'object' ? norm.grade.id : norm.grade,
    lessons_per_week: norm.lessons_per_week,
    courses_per_week: norm.courses_per_week,
  }));

  // Подсчёт кол-ва уроков по связке (grade, subject, type)
  const lessonCountMap: Record<string, number> = {};
  for (const lesson of lessons) {
    const key = `${lesson.grade}-${lesson.subject}-${lesson.type || 'lesson'}`;
    lessonCountMap[key] = (lessonCountMap[key] || 0) + 1;
  }

  return lessons.map((lesson) => {
    const norm = flatNorms.find(
      (n) => n.grade === lesson.grade && n.subject === lesson.subject
    );
    const count = lessonCountMap[`${lesson.grade}-${lesson.subject}-${lesson.type || 'lesson'}`] || 0;

    let status: 'ok' | 'under' | 'over' | undefined;
    if (norm) {
      const target = lesson.type === 'course' ? norm.courses_per_week : norm.lessons_per_week;
      status = count > target ? 'over' : count < target ? 'under' : 'ok';
    }

    const subjectObj = subjects.find((subject) => subject.id === lesson.subject);
    const gradeObj   = grades.find((grade) => grade.id === lesson.grade);
    const teacherObj = teachers.find((teacher) => teacher.id === lesson.teacher);

    return {
      ...lesson,
      start_time: (lesson.start_time || '').slice(0, 5), // 'HH:mm'
      subject_name: formatSubject(subjectObj),
      grade_name: formatGrade(gradeObj),
      teacher_name: formatTeacher(teacherObj),
      status,
    };
  });
}
