// LessonEditorModal.tsx
import React, { useEffect } from 'react';
import { Modal, Form, InputNumber, Select, TimePicker, Button, message } from 'antd';
import dayjs from 'dayjs';
import { validateLesson, PlainLesson, TeacherSlot } from '../utils/validateLesson';

interface Lookup { id: number; name: string; }
interface Props {
  open: boolean;
  lesson: PlainLesson | null;
  grades: Lookup[];
  subjects: Lookup[];
  teachers: Lookup[];
  allLessons: PlainLesson[];          // для проверки пересечений
  teacherAvailability: TeacherSlot[]; // доступность учителей
  onClose: () => void;
  onSave: (updated: PlainLesson) => void;
  onDelete: (id: number) => void;
}

const LessonEditorModal: React.FC<Props> = ({
  open, lesson, grades, subjects, teachers,
  allLessons, teacherAvailability,
  onClose, onSave, onDelete
}) => {
  const [form] = Form.useForm();

  // при открытии выставляем поля
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

      // локальная валидация
      const errs = validateLesson(updated, allLessons, teacherAvailability);
      if (errs.length) {
        message.error(errs.join('\n'));
        return;
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
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item name="grade" label="Класс" rules={[{ required: true }]}>
          <Select options={grades.map(g => ({ value: g.id, label: g.name }))} />
        </Form.Item>

        <Form.Item name="subject" label="Предмет" rules={[{ required: true }]}>
          <Select options={subjects.map(s => ({ value: s.id, label: s.name }))} />
        </Form.Item>

        <Form.Item name="teacher" label="Учитель" rules={[{ required: true }]}>
          <Select
            showSearch
            options={teachers.map(t => ({ value: t.id, label: t.name }))}
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
          <TimePicker format="HH:mm" minuteStep={5} />
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
