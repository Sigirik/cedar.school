import React, { useEffect, useState } from 'react';
import { Button, message, Table } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface Lesson {
  id: number;
  subject: string;
  teacher: string;
  day: string;
  time: string;
  class_name: string;
}

interface TemplateWeek {
  id: number;
  name: string;
  school_year: string;
  lessons: Lesson[];
}

const ActiveTemplateWeekView: React.FC = () => {
  const [activeWeek, setActiveWeek] = useState<TemplateWeek | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchActiveWeek = async () => {
      try {
        const response = await axios.get('/api/template-week/active/');
        setActiveWeek(response.data);
      } catch (error) {
        message.error('Не удалось загрузить активную неделю.');
      } finally {
        setLoading(false);
      }
    };
    fetchActiveWeek();
  }, []);

  const handleEdit = () => {
    navigate('/template-week/draft/edit');
  };

  const columns = [
    { title: 'День', dataIndex: 'day', key: 'day' },
    { title: 'Время', dataIndex: 'time', key: 'time' },
    { title: 'Предмет', dataIndex: 'subject', key: 'subject' },
    { title: 'Учитель', dataIndex: 'teacher', key: 'teacher' },
    { title: 'Класс', dataIndex: 'class_name', key: 'class_name' },
  ];

  return (
    <div>
      <h2>Текущая активная шаблонная неделя</h2>
      <p><strong>{activeWeek?.name}</strong> — {activeWeek?.school_year}</p>
      <Button type="primary" onClick={handleEdit}>
        Редактировать шаблон
      </Button>
      <Table
        columns={columns}
        dataSource={activeWeek?.lessons || []}
        rowKey="id"
        loading={loading}
        pagination={false}
        style={{ marginTop: 20 }}
      />
    </div>
  );
};

export default ActiveTemplateWeekView;
