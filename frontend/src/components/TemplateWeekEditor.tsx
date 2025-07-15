// TemplateWeekEditor.tsx (теперь только редактор черновика)

import React, { useEffect, useState } from 'react';
import { Button, Modal, Select, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

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
  const navigate = useNavigate();

  // При монтировании — копировать активную неделю в черновик
  useEffect(() => {
    const cloneActiveWeek = async () => {
      try {
        await axios.post('/api/template-week/active/clone_to_draft/', { force: true });
        message.success('Черновик создан из активной недели.');
      } catch (error) {
        message.error('Не удалось создать черновик из активной недели.');
      }
    };
    cloneActiveWeek();
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
      await axios.post(`/api/template-week/${selectedTemplateId}/clone_to_draft/`, {
        force: true,
      });
      message.success('Черновик обновлён из шаблона.');
      setIsModalVisible(false);
      // можно перезагрузить страницу или данные черновика
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

  return (
    <div>
      <h2>Редактирование шаблонной недели (черновик)</h2>
      <Button onClick={handleImportClick}>Импортировать из другого шаблона</Button>

      <Modal
        title="Выбор шаблона для импорта"
        visible={isModalVisible}
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
