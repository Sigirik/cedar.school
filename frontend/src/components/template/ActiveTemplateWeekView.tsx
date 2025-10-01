// Загружает активную шаблонную неделю через API GET /api/template/template-week/active/
// Подтягивает справочники: предметы, классы, учителя, нормы, доступность учителей
// Формирует preparedLessons с названиями, статусами (ok, under, over) и передаёт их в WeekViewSwitcher
// Используется только для просмотра, без редактирования

// ActiveTemplateWeekView.tsx

import React, { useEffect, useState } from "react";
import { api } from "@/api/http";
import WeekViewSwitcher from '../calendar/WeekViewSwitcher';
import { prepareLessons } from '../../utils/prepareLessons';
import { message, Button } from "antd";

const ActiveTemplateWeekView: React.FC = () => {
  const [preparedLessons, setPreparedLessons] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [grades, setGrades] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [weeklyNorms, setWeeklyNorms] = useState<any[]>([]);
  const [availability, setAvailability] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [hasDraft, setHasDraft] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [weekRes, subjectsRes, gradesRes, teachersRes, normsRes, availabilityRes, draftRes] = await Promise.all([
          api.get("/template/active-week/"),
          api.get("/core/subjects/"),
          api.get("/core/grades/"),
          api.get("teachers/"),
          api.get("/core/weekly-norms/"),
          api.get("/core/availabilities/"),
          api.get("/draft/template-drafts/exists/"), // ❗ добавь такой эндпоинт или замени
        ]);

        const lessons = weekRes.data.lessons || weekRes.data.template?.lessons || [];
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
        setHasDraft(draftRes.data.exists || false);
        setTemplateId(weekRes.data.id || weekRes.data.template?.id || null);

        const prepared = prepareLessons(lessons, subjects, grades, teachers, norms);
        setPreparedLessons(prepared);
      } catch (e) {
        console.warn("Ошибка загрузки данных:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleRedirectToDraft = () => {
    window.location.href = "/template-week/draft/edit/";
  };

  const handleCreateDraftFromTemplate = async () => {
    if (!templateId) {
      message.error("ID шаблона не найден");
      return;
    }

    if (hasDraft) {
      const confirm = window.confirm("У вас уже есть черновик. Вы уверены, что хотите заменить его?");
      if (!confirm) return;
    }

    try {
      const csrftoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))?.split('=')[1];

      await api.post(
        `draft/template-drafts/create-from/`,
          { template_id: templateId },
        { headers: { 'X-CSRFToken': csrftoken }, withCredentials: true }
      );

      message.success("Черновик создан");
      handleRedirectToDraft();
    } catch (err) {
      message.error("Ошибка при создании черновика");
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">Активная шаблонная неделя</h1>

        <div className="flex gap-2 mb-4">
          <Button
            type="primary"
            onClick={handleCreateDraftFromTemplate}
          >
            ✏️ Редактировать шаблон
          </Button>

          {hasDraft && (
            <Button onClick={handleRedirectToDraft}>
              ↩ Перейти в черновик
            </Button>
          )}
        </div>

        {loading ? (
          <p className="text-gray-400">Загрузка…</p>
        ) : preparedLessons.length === 0 ? (
          <p className="text-gray-500">Нет уроков в активной неделе.</p>
        ) : (
          <WeekViewSwitcher
            source="active"
            lessons={preparedLessons}
            subjects={subjects}
            grades={grades}
            teachers={teachers}
            weeklyNorms={weeklyNorms}
            teacherAvailability={availability}
          />
        )}
      </div>
    </div>
  );
};

export default ActiveTemplateWeekView;
