// TemplateWeekEditor.tsx - редактор черновика

import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Button, Modal, Select, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import WeekViewSwitcher from '../calendar/WeekViewSwitcher';
import { prepareLessons, formatTeacher } from '../../utils/prepareLessons';

const TemplateWeekEditor: React.FC = () => {
  const [historicalTemplates, setHistoricalTemplates] = useState<any[]>([]);
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
  const [collisions, setCollisions] = useState<any[]>([]);
  const [issuesOpen, setIssuesOpen] = useState(true);
  const [validating, setValidating] = useState(false);

  const navigate = useNavigate();

  const getCSRF = () =>
    document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];

  // --- INIT ---
  useEffect(() => {
    const init = async () => {
      try {
        const csrftoken = getCSRF();

        const draftRes = await axios.get('/api/draft/template-drafts/', {
          headers: { 'X-CSRFToken': csrftoken }, withCredentials: true,
        });
        const draftWeek = draftRes.data;
        const rawLessons = draftWeek.data?.lessons || [];

        const [
          subjectsRes, gradesRes, teachersRes, normsRes,
          availabilityRes, templatesRes, gradeSubjectsRes, teacherSubjectsRes, teacherGradesRes
        ] = await Promise.all([
          axios.get('/api/core/subjects/'),
          axios.get('/api/core/grades/'),
          axios.get('/api/teachers/'),
          axios.get('/api/core/weekly-norms/'),
          axios.get('/api/core/availabilities/'),
          axios.get('/api/template/weeks/'),
          axios.get('/api/core/grade-subjects/'),
          axios.get('/api/core/teacher-subjects/'),
          axios.get('/api/core/teacher-grades/'),
        ]);

        const subjects = subjectsRes.data;
        const grades = gradesRes.data;
        const teachers = teachersRes.data;
        const availability = availabilityRes.data || [];
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

  // первичная валидация при загрузке страницы
  useEffect(() => {
    (async () => {
      const csrftoken = getCSRF();
      try {
        const res = await axios.post('/api/draft/template-drafts/validate/', {}, {
          headers: { 'X-CSRFToken': csrftoken }, withCredentials: true
        });
        setCollisions(res.data.collisions || []);
      } catch (e) {
        console.error('validate error', e);
      }
    })();
  }, []);

  // карта конфликтов для подсветки событий
  const collisionMap = useMemo(() => {
    const m = new Map<number, 'error' | 'warning'>();
    for (const c of collisions) {
      for (const id of c.lesson_ids || []) {
        if (m.get(id) === 'error') continue;
        m.set(id, c.severity);
      }
    }
    return m;
  }, [collisions]);

  // индикаторы
  const hasErrors = collisions.some((c: any) => c.severity === 'error');
  const warningsCount = collisions.filter((c: any) => c.severity === 'warning').length;

  const revalidate = useCallback(async () => {
    const csrftoken = getCSRF();
    try {
      setValidating(true);
      const res = await axios.post('/api/draft/template-drafts/validate/', {}, {
        headers: { 'X-CSRFToken': csrftoken }, withCredentials: true
      });
      setCollisions(res.data.collisions || []);
    } catch (e) {
      // no-op
    } finally {
      setValidating(false);
    }
  }, []);

  // --- PATCH: обновление уроков в черновике
  const patchDraft = async (updatedLessonsRaw: any[]) => {
    const csrftoken = getCSRF();
    await axios.patch('/api/draft/template-drafts/update/', { data: { lessons: updatedLessonsRaw } }, {
      headers: { 'X-CSRFToken': csrftoken }, withCredentials: true
    });
  };

  const enrichLesson = (l: any) => {
    const teacher = teachers.find((t: any) => t.id === l.teacher);
    return {
      ...l,
      subject_name: subjects.find((s: any) => s.id === l.subject)?.name || '',
      grade_name: grades.find((g: any) => g.id === l.grade)?.name || '',
      teacher_name: teacher ? formatTeacher(teacher) : '',
    };
  };

  const handleLessonSave = async (updated: any) => {
    const enriched = enrichLesson(updated);
    const exists = lessons.some((l: any) => l.id === enriched.id);
    const next = exists ? lessons.map((l: any) => (l.id === enriched.id ? enriched : l)) : [...lessons, enriched];
    setLessons(next);
    try {
      await patchDraft(next);
      await revalidate();
      message.success('Урок сохранён');
    } catch {
      message.error('Не удалось сохранить черновик');
    }
  };

  const handleLessonDelete = async (id: number) => {
    const next = lessons.filter((l: any) => l.id !== id);
    setLessons(next);
    try {
      await patchDraft(next);
      await revalidate();
      message.success('Урок удалён');
    } catch {
      message.error('Не удалось сохранить черновик');
    }
  };

  // прокрутить/подсветить событие в календаре по его id (без изменений других компонентов)
  const focusLesson = (lessonId: number | string) => {
    const el = document.querySelector<HTMLElement>(`.fc .fc-event[data-event-id="${lessonId}"]`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('tw-flash');
      setTimeout(() => el.classList.remove('tw-flash'), 1500);
    } else {
      message.info('Не удалось найти занятие на экране. Возможно, другой день.');
    }
  };

  // --- Опубликовать черновик как активную неделю
  const handlePublish = async () => {
    const confirm = window.confirm('Опубликовать этот черновик как новую активную неделю?');
    if (!confirm) return;

    try {
      const csrftoken = getCSRF();

      // ⚠️ ВАЖНО: не теряем тип урока — пробрасываем l.type (ключ) или l.type_id (если присутствует)
      const cleanedLessons = lessons.map((l: any) => ({
        id: l.id,
        grade: l.grade,
        subject: l.subject,
        teacher: l.teacher,
        day_of_week: l.day_of_week,
        start_time: l.start_time,
        duration_minutes: l.duration_minutes,
        // добавлено:
        type: l.type ?? l.type_key ?? null,
        type_id: typeof l.type_id === 'number' ? l.type_id : undefined,
      }));

      await axios.patch(
        '/api/draft/template-drafts/update/',
        { data: { lessons: cleanedLessons } },
        { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
      );

      await axios.post(
        '/api/draft/template-drafts/commit/',
        {},
        { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
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
    const csrftoken = getCSRF();
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
    const csrftoken = getCSRF();
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

      <div className="mb-4 flex flex-wrap gap-8 items-center">
        <div className="space-x-2">
          <Button onClick={() => setIsModalVisible(true)}>Импортировать из другого шаблона</Button>
          <Button danger onClick={() => setShowEmptyConfirm(true)}>Пустой шаблон</Button>
          <Button type="primary" onClick={handlePublish}>Опубликовать</Button>
        </div>
        <div className="ml-auto flex gap-8 items-center">
          <Button onClick={revalidate} loading={validating}>Проверить коллизии</Button>
          <Button
            className="text-sm text-gray-600 underline underline-offset-2"
            onClick={() => setIssuesOpen(v => !v)}
          >
            {issuesOpen ? 'Скрыть' : 'Показать'} проблемы
          </Button>
          <div className="text-sm">
            {hasErrors ? <span className="text-red-600 font-semibold">Есть ошибки</span> : <span className="text-green-600">Ошибок нет</span>}
            {warningsCount > 0 ? <span className="text-yellow-700 ml-3">Предупр.: {warningsCount}</span> : null}
          </div>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-400">Загрузка…</p>
      ) : (
        <div className="flex gap-4">
          <div className="flex-1 min-w-0">
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
              // индикаторы и подсветка
              hasCollisionErrors={hasErrors}
              warningsCount={warningsCount}
              collisionMap={collisionMap as any}
            />
          </div>

          {issuesOpen && (
            <aside className="w-96 shrink-0 border-l border-gray-200 pl-3">
              <h3 className="text-sm font-semibold mb-2">Проблемы расписания</h3>
              {collisions.length === 0 ? (
                <div className="text-xs text-gray-500">Пока проблем не найдено. Нажмите «Проверить коллизии».</div>
              ) : (
                <ul className="space-y-2 max-h-[70vh] overflow-auto pr-1">
                  {collisions.map((issue: any, idx: number) => (
                    <li
                      key={idx}
                      className={`p-2 rounded border ${
                        issue.severity === 'error' ? 'border-red-300 bg-red-50' : 'border-yellow-300 bg-yellow-50'
                      }`}
                    >
                      <div className="text-xs mb-1">
                        <span className={`font-semibold mr-2 ${issue.severity === 'error' ? 'text-red-600' : 'text-yellow-700'}`}>
                          {issue.severity === 'error' ? 'Ошибка' : 'Предупреждение'}
                        </span>
                        {issue.message}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {(issue.lesson_ids || []).map((lid: number) => (
                          <Button
                            key={lid}
                            onClick={() => focusLesson(lid)}
                            className="text-[11px] px-2 py-0.5 rounded border border-gray-300 hover:bg-gray-50"
                            title="Показать на календаре"
                          >
                            #{lid}
                          </Button>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </aside>
          )}
        </div>
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

      {/* локальная подсветка кликом по проблеме */}
      <style>{`
        .tw-flash {
          outline: 2px solid rgba(220, 38, 38, 0.9) !important;
          transition: outline 0.2s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default TemplateWeekEditor;
