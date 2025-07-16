// TemplateWeekEditor.tsx - редактор черновика
import React, { useEffect, useState } from 'react';
import { Button, Modal, Select, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import TemplateWeekCalendar from './TemplateWeekCalendar';
import WeekViewByGrade from './WeekViewByGrade';
import WeekViewSwitcher from './WeekViewSwitcher';

interface TemplateWeek {
  id: number;
  name: string;
  school_year: string;
  created_at: string;
}

const TemplateWeekEditor: React.FC = () => {
  const [historicalTemplates, setHistoricalTemplates] = useState<TemplateWeek[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [draftId, setDraftId] = useState<number | null>(null);
  const navigate = useNavigate();

  // 🔄 При монтировании — создать пустой черновик
  useEffect(() => {
    const createInitialDraft = async () => {
      try {
        const res = await axios.post('/api/draft/template-drafts/create-empty/');
        setDraftId(res.data.id);
        console.log("✅ Пустой черновик создан:", res.data);
      } catch (err) {
        message.error("Ошибка при создании черновика.");
        console.error(err);
      }
    };
    createInitialDraft();
  }, []);

  const fetchHistoricalTemplates = async () => {
    try {
      const response = await axios.get('/api/template-week/historical_templates/');
      setHistoricalTemplates(response.data);
    } catch (error) {
      message.error('Не удалось загрузить шаблоны.');
    }
  };

  const handleImportClick = () => {
    fetchHistoricalTemplates();
    setIsModalVisible(true);
  };

  const handleClone = async () => {
    if (!selectedTemplateId) return;

    const confirmReplace = window.confirm('Черновик будет перезаписан. Продолжить?');
    if (!confirmReplace) return;

    setIsLoading(true);
    try {
      const res = await axios.post(`/api/draft/template-drafts/create-from/${selectedTemplateId}/`);
      message.success('Черновик обновлён из шаблона.');
      setDraftId(res.data.id);
      setIsModalVisible(false);
    } catch (error: any) {
      if (error.response?.status === 409) {
        message.warning('Уже существует черновик.');
      } else {
        message.error('Ошибка при копировании.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!draftId) {
      message.error("Нет активного черновика.");
      return;
    }

    const confirm = window.confirm("Опубликовать этот черновик как новую активную неделю?");
    if (!confirm) return;

    try {
      await axios.post(`/api/draft/template-drafts/${draftId}/commit/`);
      message.success("Черновик опубликован.");
      navigate("/template-week/active");
    } catch (err) {
      message.error("Ошибка при публикации.");
      console.error(err);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Редактирование шаблонной недели (черновик)</h2>

      <div className="mb-4 space-x-2">
        <Button onClick={handleImportClick}>Импортировать из другого шаблона</Button>
        <Button type="primary" disabled={!draftId} onClick={handlePublish}>
          Опубликовать
        </Button>
      </div>
      {draftId && <TemplateWeekCalendar draftId={draftId} />}
      {draftId && <WeekViewByGrade draftId={draftId} />}
      {draftId && <WeekViewSwitcher draftId={draftId} />}

      <Modal
        title="Выбор шаблона для импорта"
        open={isModalVisible}
        onOk={handleClone}
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
