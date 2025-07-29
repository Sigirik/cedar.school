import { message } from 'antd';
import { validateLesson, PlainLesson, TeacherSlot } from '../utils/validateLesson';
import { rebuildLesson, toPlainLesson } from '../utils/calendar';

export const useCalendarHandlers = (lessons: any[], teacherAvailability: TeacherSlot[], onLessonSave: (l: any) => void) => {
  const checkLessons = lessons.map(toPlainLesson);
  const checkAvailability = teacherAvailability.map(x => ({
    teacher: x.teacher,
    day_of_week: x.day_of_week,
    start_time: x.start_time,
    end_time: x.end_time
  }));

  const validateAndSave = (updated: any, info: any) => {
    const { errors, warnings } = validateLesson(toPlainLesson(updated), checkLessons, checkAvailability);
    if (errors.length) {
      message.error(errors.join('\n'));
      info.revert();
      return;
    }
    if (warnings.length) {
      message.warning(warnings.join('\n'));
    }
    onLessonSave(updated);
  };

  return {
    onEventDrop: (info: any) => {
      const src = lessons.find(x => x.id === Number(info.event.id));
      if (!src) return;
      const updated = rebuildLesson(info, src);
      validateAndSave(updated, info);
    },
    onEventResize: (info: any) => {
      const src = lessons.find(x => x.id === Number(info.event.id));
      if (!src) return;
      const updated = rebuildLesson(info, src);
      validateAndSave(updated, info);
    },
  };
};
