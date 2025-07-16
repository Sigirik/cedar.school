import React, { useState } from 'react';
import { Segmented } from 'antd';
import WeekViewByGrade from './WeekViewByGrade';
import WeekViewByTeacher from './WeekViewByTeacher';
import WeekNormSummary from './WeekNormSummary';

interface ReferenceItem {
  id: number;
  name: string;
}

interface Props {
  source: 'draft' | 'active';
  id?: number;
  subjects?: ReferenceItem[];
  grades?: ReferenceItem[];
  teachers?: ReferenceItem[];
}

const WeekViewSwitcher: React.FC<Props> = ({ source, id, subjects = [], grades = [], teachers = [] }) => {
  const [mode, setMode] = useState<'grade' | 'teacher' | 'norm'>('grade');

  return (
    <div className="space-y-4">
      <Segmented
        options={[
          { label: 'По классам', value: 'grade' },
          { label: 'По учителям', value: 'teacher' },
          { label: 'По нормам', value: 'norm' },
        ]}
        value={mode}
        onChange={val => setMode(val as typeof mode)}
      />

      {mode === 'grade' && <WeekViewByGrade source={source} id={id} subjects={subjects} grades={grades} />}
      {mode === 'teacher' && <WeekViewByTeacher source={source} id={id} subjects={subjects} teachers={teachers} />}
      {mode === 'norm' && <WeekNormSummary source={source} id={id} subjects={subjects} grades={grades} />}
    </div>
  );
};

export default WeekViewSwitcher;