import { useState } from 'react';
import LessonEditorModal from '../components/LessonEditorModal';
import { PlainLesson } from '../utils/validateLesson';

export function useLessonModal({ lessons, teachers, grades, subjects, teacherAvailability, onLessonSave, onLessonDelete }: any) {
  const [selected, setSelected] = useState<PlainLesson | null>(null);
  const [showModal, setShowModal] = useState(false);

  const modal = selected && (
    <LessonEditorModal
      open={showModal}
      lesson={selected}
      grades={grades}
      subjects={subjects}
      teachers={teachers}
      allLessons={lessons}
      teacherAvailability={teacherAvailability}
      onClose={() => setShowModal(false)}
      onSave={(l) => { onLessonSave(l); setShowModal(false); }}
      onDelete={(id) => { onLessonDelete(id); setShowModal(false); }}
    />
  );

  return { selected, setSelected, showModal, setShowModal, modal };
}
