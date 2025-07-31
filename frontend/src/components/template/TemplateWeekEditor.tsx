// TemplateWeekEditor.tsx - редактор черновика

import React, { useEffect, useState } from 'react';
import { Button, Modal, Select, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import WeekViewSwitcher from '../calendar/WeekViewSwitcher';
import { prepareLessons, formatTeacher } from '../../utils/prepareLessons';

const TemplateWeekEditor: React.FC = () => {
  const [historicalTemplates, setHistoricalTemplates] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [showEmptyConfirm, setShowEmptyConfirm] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [lessons, setLessons] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);
  const [availability, setAvailability] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [gradeSubjects, setGradeSubjects] = useState<any[]>([]);
  const [teacherSubjects, setTeacherSubjects] = useState<any[]>([]);
  const [teacherGrades, setTeacherGrades] = useState<any[]>([]);

  const navigate = useNavigate();

  // --- INIT ---
  useEffect(() => {
    const init = async () => {
      try {
        const csrftoken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrftoken='))
          ?.split('=')[1];

        // Получаем или создаём единственный черновик для пользователя
        const draftRes = await axios.get('/api/draft/template-drafts/', {
          headers: { 'X-CSRFToken': csrftoken },
          withCredentials: true,
        });

        const draftWeek = draftRes.data;
        const rawLessons = draftWeek.data?.lessons || [];

        // Загружаем справочники (как и раньше)
        const [subjectsRes, gradesRes, teachersRes, normsRes, availabilityRes, templatesRes, gradeSubjectsRes, teacherSubjectsRes, teacherGradesRes] = await Promise.all([
          axios.get('/api/core/subjects/'),
          axios.get('/api/core/grades/'),
          axios.get('/api/users/teachers/'),
          axios.get('/api/core/weekly-norms/'),
          axios.get('/api/core/availabilities/'),
          axios.get('/api/template/weeks/'), // для импорта исторических шаблонов
          axios.get('/api/core/grade-subjects/'),
          axios.get('/api/core/teacher-subjects/'),
          axios.get('/api/core/teacher-grades/'),
        ]);

        const subjects = subjectsRes.data;
        const grades = gradesRes.data;
        const teachers = teachersRes.data;
        const availability = availabilityRes.data || [];
        // --- Плоские нормы! ---
        const norms = normsRes.data.map((n: any) => ({
          ...n,
          subject: typeof n.subject === 'object' ? n.subject.id : n.subject,
          grade: typeof n.grade === 'object' ? n.grade.id : n.grade,
        }));

        setSubjects(subjects);
        setGrades(grades);
        setTeachers(teachers);
        setWeeklyNorms(norms);
        setAvailability(availability);
        setGradeSubjects(gradeSubjectsRes.data);
        setTeacherSubjects(teacherSubjectsRes.data);
        setTeacherGrades(teacherGradesRes.data);

        // Исторические шаблоны для импорта
        setHistoricalTemplates(templatesRes.data);

        const prepared = prepareLessons(rawLessons, subjects, grades, teachers, norms);
        setLessons(prepared);
      } catch (e) {
        message.error('Ошибка при загрузке черновика.');
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // --- PATCH: обновление уроков в черновике
  const patchDraft = async (updatedLessonsRaw: any[]) => {
    const csrftoken = document.cookie
      .split('; ')
      .find(r => r.startsWith('csrftoken='))?.split('=')[1];
    await axios.patch(
      '/api/draft/template-drafts/update/',
      { data: { lessons: updatedLessonsRaw } },
      { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
    );
  };

    const enrichLesson = (l: any) => {
      const teacher = teachers.find(t => t.id === l.teacher);
      return {
        ...l,
        subject_name: subjects.find(s => s.id === l.subject)?.name || '',
        grade_name: grades.find(g => g.id === l.grade)?.name || '',
        teacher_name: teacher ? formatTeacher(teacher) : '',
      };
    };

    const handleLessonSave = async (updated: any) => {
      const enriched = enrichLesson(updated);
      const exists = lessons.some(l => l.id === enriched.id);
      const raw = exists
        ? lessons.map(l => (l.id === enriched.id ? enriched : l))
        : [...lessons, enriched];

      setLessons(raw);

      try {
        await patchDraft(raw);
        message.success('Урок сохранён');
      } catch {
        message.error('Не удалось сохранить черновик');
      }
    };

  const handleLessonDelete = async (id: number) => {
    const raw = lessons.filter(l => l.id !== id);
    setLessons(raw);
    try {
      await patchDraft(raw);
      message.success('Урок удалён');
    } catch {
      message.error('Не удалось сохранить черновик');
    }
  };

  // --- Опубликовать черновик как активную неделю
    const handlePublish = async () => {
      const confirm = window.confirm('Опубликовать этот черновик как новую активную неделю?');
      if (!confirm) return;

      try {
        const csrftoken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrftoken='))?.split('=')[1];

        // Извлекаем только нужные поля для backend
        const cleanedLessons = lessons.map((l) => ({
          id: l.id,
          grade: l.grade,
          subject: l.subject,
          teacher: l.teacher,
          day_of_week: l.day_of_week,
          start_time: l.start_time,
          duration_minutes: l.duration_minutes,
        }));

        await axios.patch(
          '/api/draft/template-drafts/update/',
          { data: { lessons: cleanedLessons } },
          { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
        );

        await axios.post(
          '/api/draft/template-drafts/commit/',
          {},
          {
            headers: { 'X-CSRFToken': csrftoken },
            withCredentials: true,
          }
        );

        message.success('Черновик опубликован.');
        setLessons([]);
        navigate('/template-week');
      } catch (err) {
        message.error('Ошибка при публикации.');
        console.error(err);
      }
    };

  // --- Импорт шаблона (из модалки)
  const handleImportTemplate = async () => {
    if (!selectedTemplateId) return;
    setIsLoading(true);
    const csrftoken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    try {
      await axios.post(
        '/api/draft/template-drafts/create-from/',
        { template_id: selectedTemplateId },
        { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
      );
      message.success('Шаблон импортирован в черновик!');
      setIsModalVisible(false);
      window.location.reload();
    } catch (e) {
      message.error('Ошибка при импорте шаблона');
      setIsLoading(false);
    }
  };

    const handleCreateEmpty = async () => {
      const csrftoken = document.cookie
        .split('; ')
        .find(r => r.startsWith('csrftoken='))?.split('=')[1];
      try {
        await axios.post(
          '/api/draft/template-drafts/create-empty/',
          {},
          { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
        );
        message.success('Создан пустой шаблон.');
        window.location.reload();
      } catch (e) {
        message.error('Ошибка при создании пустого шаблона');
      }
    };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Редактирование шаблонной недели (черновик)</h2>

      <div className="mb-4 space-x-2">
        <Button onClick={() => setIsModalVisible(true)}>Импортировать из другого шаблона</Button>
        <Button danger onClick={() => setShowEmptyConfirm(true)}>Пустой шаблон</Button>
        <Button type="primary" onClick={handlePublish}>Опубликовать</Button>
      </div>

      {loading ? (
        <p className="text-gray-400">Загрузка…</p>
      ) : (
        <WeekViewSwitcher
          source="draft"
          lessons={lessons}
          subjects={subjects}
          grades={grades}
          teachers={teachers}
          weeklyNorms={weeklyNorms}
          teacherAvailability={availability}
          gradeSubjects={gradeSubjects}
          teacherSubjects={teacherSubjects}
          teacherGrades={teacherGrades}
          onLessonSave={handleLessonSave}
          onLessonDelete={handleLessonDelete}
        />
      )}

      <Modal
        title="Выбор шаблона для импорта"
        open={isModalVisible}
        onOk={handleImportTemplate}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={isLoading}
        okText="Импортировать"
        cancelText="Отмена"
      >
        <Select
          style={{ width: '100%' }}
          placeholder="Выберите шаблон"
          onChange={(value: number) => setSelectedTemplateId(value)}
        >
          {historicalTemplates.map((template: any) => (
            <Select.Option key={template.id} value={template.id}>
              {template.name} — {template.school_year || template.created_at}
            </Select.Option>
          ))}
        </Select>
      </Modal>
      <Modal
          title="Создать пустой шаблон?"
          open={showEmptyConfirm}
          onOk={handleCreateEmpty}
          onCancel={() => setShowEmptyConfirm(false)}
          okText="Продолжить"
          cancelText="Отмена"
          okButtonProps={{ danger: true }}
      >
          <p className="text-red-600">
            Все текущие уроки из черновика будут удалены. Вы уверены, что хотите начать с пустого шаблона?
          </p>
      </Modal>
    </div>
  );
};

export default TemplateWeekEditor;
