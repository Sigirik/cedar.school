// TemplateWeekEditor.tsx - редактор черновика

import React, { useEffect, useState } from 'react';
import { Button, Modal, Select, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import WeekViewSwitcher from '../calendar/WeekViewSwitcher';
import { prepareLessons } from '../utils/prepareLessons';

const TemplateWeekEditor: React.FC = () => {
  const [historicalTemplates, setHistoricalTemplates] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [draftId, setDraftId] = useState<number | null>(null);

  const [lessons, setLessons] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);
  const [availability, setAvailability] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    const init = async () => {
      try {
        let draftRes;

        const csrftoken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrftoken='))
          ?.split('=')[1];

        // 1. Пытаемся найти уже существующий черновик
        const existingDrafts = await axios.get('/api/draft/template-drafts/', {
          headers: { 'X-CSRFToken': csrftoken },
          withCredentials: true,
        });

        if (existingDrafts.data.length > 0) {
          draftRes = { data: existingDrafts.data[0] };
          console.log('🟢 Найден существующий черновик', draftRes.data);
        } else {
          // 2. Если не найден — создаём
          const active = await axios.get('/api/template/template-week/active/');
          const activeId = active.data.id;

          draftRes = await axios.post(
            `/api/draft/template-drafts/create-from/${activeId}/`,
            {},
            {
              headers: { 'X-CSRFToken': csrftoken },
              withCredentials: true,
            }
          );
          console.log('🟡 Создан черновик на основе активной недели', draftRes.data);
        }

        const id = draftRes.data.id;
        setDraftId(id);

        const [draftWeek, subjectsRes, gradesRes, teachersRes, normsRes, availabilityRes] = await Promise.all([
          axios.get(`/api/draft/template-drafts/${id}/`),
          axios.get('/api/ktp/subjects/'),
          axios.get('/api/ktp/grades/'),
          axios.get('/api/ktp/teachers/'),
          axios.get('/api/ktp/weekly-norms/'),
          axios.get('/api/template/teacher-availability/'),
        ]);

        const rawLessons = draftWeek.data.data.lessons || [];
        const subjects = subjectsRes.data;
        const grades = gradesRes.data;
        const teachers = teachersRes.data;
        const norms = normsRes.data;
        const availability = availabilityRes.data || [];

        setSubjects(subjects);
        setGrades(grades);
        setTeachers(teachers);
        setWeeklyNorms(norms);
        setAvailability(availability);

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

    // 🔄 Обновление урока в state + PATCH на бэкенд
    const patchDraft = async (updatedLessonsRaw: any[]) => {
      if (!draftId) return;
      const csrftoken = document.cookie
        .split('; ')
        .find(r => r.startsWith('csrftoken='))?.split('=')[1];
      await axios.patch(
        `/api/draft/template-drafts/${draftId}/`,
        { data: { lessons: updatedLessonsRaw } },
        { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
      );
    };

    const handleLessonSave = async (updated: any) => {
      const raw = lessons.map(l => (l.id === updated.id ? updated : l));
          // 💡 При желании — запрос к /api/schedule/validate/ и блокировка по ошибкам.
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


  const handlePublish = async () => {
    if (!draftId) return;
    const confirm = window.confirm('Опубликовать этот черновик как новую активную неделю?');
    if (!confirm) return;
    try {
      const csrftoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

      await axios.post(
        `/api/draft/template-drafts/${draftId}/commit/`,
        {},
        {
          headers: {
            'X-CSRFToken': csrftoken,
          },
          withCredentials: true,
        }
      );
      message.success('Черновик опубликован.');
      navigate('/template-week/active');
    } catch (err) {
      message.error('Ошибка при публикации.');
      console.error(err);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Редактирование шаблонной недели (черновик)</h2>

      <div className="mb-4 space-x-2">
        <Button onClick={() => setIsModalVisible(true)}>Импортировать из другого шаблона</Button>
        <Button type="primary" disabled={!draftId} onClick={handlePublish}>Опубликовать</Button>
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
          onLessonSave={handleLessonSave}
          onLessonDelete={handleLessonDelete}
        />
      )}

      <Modal
        title="Выбор шаблона для импорта"
        open={isModalVisible}
        onOk={() => {}} // TODO: implement clone
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
          {historicalTemplates.map(template => (
            <Select.Option key={template.id} value={template.id}>
              {template.name} — {template.school_year}
            </Select.Option>
          ))}
        </Select>
      </Modal>
    </div>
  );
};

export default TemplateWeekEditor;
