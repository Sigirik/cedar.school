import React, { useEffect } from 'react';
import { Modal, Form, InputNumber, Select, TimePicker, Button, message } from 'antd';
import dayjs from 'dayjs';
import { validateLesson, PlainLesson, TeacherSlot } from '../../utils/validateLesson';
import { formatTeacher, formatGrade, formatSubject } from '../../utils/prepareLessons';

interface Lookup { id: number; name: string; }
interface Props {
  open: boolean;
  lesson: PlainLesson | null;
  grades: Lookup[];
  subjects: Lookup[];
  teachers: { id: number; last_name: string; first_name?: string; middle_name?: string; name?: string }[];
  allLessons: PlainLesson[];
  teacherAvailability: TeacherSlot[];
  gradeSubjects?: { grade: number; subject: number }[];
  teacherSubjects?: { teacher: number; subject: number }[];
  teacherGrades?: { teacher: number; grade: number }[];
  onClose: () => void;
  onSave: (updated: PlainLesson) => void;
  onDelete: (id: number) => void;
}

const LessonEditorModal: React.FC<Props> = ({
  open, lesson, grades, subjects, teachers,
  allLessons, teacherAvailability,
  gradeSubjects, teacherSubjects, teacherGrades,
  onClose, onSave, onDelete
}) => {
  const [form] = Form.useForm();

  const currentGrade = Form.useWatch('grade', form);
  const currentSubject = Form.useWatch('subject', form);
  const currentTeacher = Form.useWatch('teacher', form);

  const gradeSubjectsSafe = gradeSubjects ?? [];
  const teacherSubjectsSafe = teacherSubjects ?? [];
  const teacherGradesSafe = teacherGrades ?? [];

  // --- ФИЛЬТРАЦИЯ: Предмет ---
  let filteredSubjects = subjects;
  if (currentGrade) {
    const allowedSubjectIds = gradeSubjects
      .filter(gs => gs.grade === currentGrade)
      .map(gs => gs.subject);
    filteredSubjects = subjects.filter(s => allowedSubjectIds.includes(s.id));
  }

  // --- ФИЛЬТРАЦИЯ: Учитель ---
  let filteredTeachers = teachers;
  if (currentGrade) {
    const allowedTeacherIds = teacherGrades
      .filter(tg => tg.grade === currentGrade)
      .map(tg => tg.teacher);
    filteredTeachers = teachers.filter(t => allowedTeacherIds.includes(t.id));
  }
  if (currentSubject) {
    const allowedTeacherIds = teacherSubjects
      .filter(ts => ts.subject === currentSubject)
      .map(ts => ts.teacher);
    filteredTeachers = filteredTeachers.filter(t => allowedTeacherIds.includes(t.id));
  }

  // --- Добавить пустой вариант "—" для сброса фильтра ---
  const subjectOptions = [{ value: '', label: '—' }, ...filteredSubjects.map(s => ({
    value: s.id,
    label: formatSubject(s)
  }))];

  const teacherOptions = [{ value: '', label: '—' }, ...filteredTeachers.map(t => ({
    value: t.id,
    label: formatTeacher(t)
  }))];

  useEffect(() => {
    if (open && lesson) {
      form.setFieldsValue({
        ...lesson,
        time: dayjs(lesson.start_time, 'HH:mm'),
      });
    } else {
      form.resetFields();
    }
  }, [open, lesson, form]);

  const handleSubmit = () => {
    form.validateFields().then(values => {
      const updated = {
        ...(lesson as PlainLesson),
        grade: values.grade,
        subject: values.subject,
        teacher: values.teacher,
        day_of_week: values.day_of_week,
        start_time: values.time.format('HH:mm'),
        duration_minutes: values.duration_minutes,
      };

        const { errors, warnings } = validateLesson(updated, allLessons, teacherAvailability);
        if (errors.length) {
          message.error(errors.join('\n'));
          return;
        }
        if (warnings.length) {
          message.warning(warnings.join('\n'));
          // разрешаем сохранить!
        }

      onSave(updated);
    });
  };

  if (!lesson) return null;

  return (
    <Modal
      title="Редактирование урока"
      open={open}
      onCancel={onClose}
      footer={null}
      destroyOnHidden
    >
      <Form form={form} layout="vertical">
        <Form.Item name="grade" label="Класс" rules={[{ required: true }]}>
          <Select options={grades.map(g => ({ value: g.id, label: formatGrade(g) }))} />
        </Form.Item>

        <Form.Item name="subject" label="Предмет" rules={[{ required: true }]}>
          <Select options={subjectOptions} />
        </Form.Item>

        <Form.Item name="teacher" label="Учитель" rules={[{ required: true }]}>
          <Select
            showSearch
            options={teacherOptions}
            filterOption={(input, opt) =>
              (opt?.label as string).toLowerCase().includes(input.toLowerCase())
            }
          />
        </Form.Item>

        <Form.Item name="day_of_week" label="День недели" rules={[{ required: true }]}>
          <Select
            options={[
              { value: 0, label: 'Понедельник' },
              { value: 1, label: 'Вторник' },
              { value: 2, label: 'Среда' },
              { value: 3, label: 'Четверг' },
              { value: 4, label: 'Пятница' },
            ]}
          />
        </Form.Item>

        <Form.Item name="time" label="Время начала" rules={[{ required: true }]}>
          <TimePicker
            format="HH:mm"
            minuteStep={5}
            allowClear={false}
            onBlur={(e) => {
              // Принудительно триггерим обновление формы при потере фокуса
              const value = e.target.value;
              const parsed = dayjs(value, 'HH:mm', true);
              if (parsed.isValid()) {
                form.setFieldsValue({ time: parsed });
              }
            }}
          />
        </Form.Item>

        <Form.Item name="duration_minutes" label="Длительность (мин)" rules={[{ required: true }]}>
          <InputNumber min={5} max={120} step={5} className="w-full" />
        </Form.Item>

        <div className="flex justify-between mt-4">
          <Button danger onClick={() => onDelete(lesson.id)}>Удалить</Button>
          <div>
            <Button onClick={onClose} style={{ marginRight: 8 }}>Отмена</Button>
            <Button type="primary" onClick={handleSubmit}>Сохранить</Button>
          </div>
        </div>
      </Form>
    </Modal>
  );
};

export default LessonEditorModal;
