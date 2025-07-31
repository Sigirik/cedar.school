import React, { useEffect, useState } from "react";
import axios from "axios";
import { formatSubject, formatGrade } from "../../utils/prepareLessons";

type KTPEntry = {
  id: number;
  lesson_number: number;
  type: "lesson" | "course";
  planned_date: string | null;
  actual_date: string | null;
  title: string;
  objectives: string;
  tasks: string;
  homework: string;
  materials: string;
  planned_outcomes: string;
  motivation: string;
  order: number;
};

type KTPSection = {
  id: number;
  title: string;
  description: string;
  order: number;
  hours: number;
  entries: KTPEntry[];
};

type KTPTemplate = {
  id: number;
  name: string;
  subject: number;
  subject_data?: { name: string };
  grade: number;
  grade_data?: { name: string };
  academic_year: number;
  sections: KTPSection[];
};

type GroupedTemplates = {
  [subjectTitle: string]: {
    subjectId: number;
    classes: { gradeId: number; gradeTitle: string; templateId: number }[];
  };
};

const KtpEditor: React.FC = () => {
  const [templates, setTemplates] = useState<KTPTemplate[]>([]);
  const [groupedTemplates, setGroupedTemplates] = useState<GroupedTemplates>({});
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [selectedGradeId, setSelectedGradeId] = useState<number | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<KTPTemplate | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [newSectionTitle, setNewSectionTitle] = useState("");
  const [subjects, setSubjects] = useState<{ id: number; name: string }[]>([]);
  const [grades, setGrades] = useState<{ id: number; name: string }[]>([]);

    useEffect(() => {
      axios.get("/api/core/subjects/").then((res) => setSubjects(res.data));
      axios.get("/api/core/grades/").then((res) => setGrades(res.data));
    }, []);

    useEffect(() => {
      if (subjects.length === 0 || grades.length === 0) return;

      axios.get("/api/ktp/templates/").then((res) => {
        const data: KTPTemplate[] = res.data;
        const grouped: GroupedTemplates = {};
        data.forEach((tpl) => {
          const subj = subjects.find((s) => s.id === tpl.subject);
          const grade = grades.find((g) => g.id === tpl.grade);
          const subjName = formatSubject(subj);
          const gradeName = formatGrade(grade);

          if (!grouped[subjName]) {
            grouped[subjName] = { subjectId: tpl.subject, classes: [] };
          }

          grouped[subjName].classes.push({
            gradeId: tpl.grade,
            gradeTitle: gradeName,
            templateId: tpl.id,
          });
        });

        setGroupedTemplates(grouped);
        setTemplates(data);
      });
    }, [subjects, grades]);

  useEffect(() => {
    if (selectedTemplateId !== null) {
      axios.get("/api/ktp/templates/" + selectedTemplateId + "/").then((res) => {
        setSelectedTemplate(res.data);
      });
    }
  }, [selectedTemplateId]);

  const refreshTemplate = () => {
    if (selectedTemplateId !== null) {
      axios.get("/api/ktp/templates/" + selectedTemplateId + "/").then((res) => {
        setSelectedTemplate(res.data);
      });
    }
  };

  const handleAddSection = () => {
    if (!newSectionTitle || !selectedTemplateId || !selectedTemplate) return;
    const maxOrder =
      selectedTemplate.sections.reduce((max, sec) => Math.max(max, sec.order), 0) ?? 0;
    axios
      .post("/api/ktp/sections/", {
        ktp_template: selectedTemplateId,
        title: newSectionTitle,
        description: "",
        order: maxOrder + 1,
        hours: 0,
      })
      .then(() => {
        setNewSectionTitle("");
        refreshTemplate();
      });
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">КТП: редактор</h1>

      {/* Выбор предмета и класса */}
      <div className="flex gap-4 mb-4">
        <select
          className="border p-2"
          onChange={(e) => {
            const subjId = Number(e.target.value);
            setSelectedSubjectId(subjId);
            setSelectedGradeId(null);
          }}
          value={selectedSubjectId ?? ""}
        >
          <option value="">Выберите предмет</option>
          {Object.entries(groupedTemplates).map(([title, group]) => (
            <option key={group.subjectId} value={group.subjectId}>
              {title}
            </option>
          ))}
        </select>

        <select
          className="border p-2"
          onChange={(e) => {
            const gradeId = Number(e.target.value);
            setSelectedGradeId(gradeId);
            const template = templates.find(
              (tpl) => tpl.subject === selectedSubjectId && tpl.grade === gradeId
            );
            if (template) setSelectedTemplateId(template.id);
          }}
          value={selectedGradeId ?? ""}
          disabled={!selectedSubjectId}
        >
          <option value="">Выберите класс</option>
          {selectedSubjectId &&
            groupedTemplates &&
            Object.values(groupedTemplates)
              .find((g) => g.subjectId === selectedSubjectId)
              ?.classes.map((cls) => (
                <option key={`${cls.gradeId}-${cls.templateId}`} value={cls.gradeId}>
                  {cls.gradeTitle}
                </option>
              ))}
        </select>
      </div>

      {selectedTemplate && (
        <>
          <button
            className={`mb-4 px-4 py-2 rounded ${editMode ? "bg-yellow-500" : "bg-gray-400"} text-white`}
            onClick={() => setEditMode((prev) => !prev)}
          >
            {editMode ? "🚫 Выключить режим правок" : "✏️ Режим правок"}
          </button>

          {selectedTemplate.sections
            .slice()
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <div key={section.id} className="mb-6 border p-3 rounded bg-gray-50">
                <h2 className="text-lg font-semibold mb-2">
                  📂 {section.order}. {section.title} ({section.hours} ч)
                </h2>

                <table className="table-auto w-full border text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-2">Дата план</th>
                      <th className="border px-2">Дата факт</th>
                      <th className="border px-2">Тип</th>
                      <th className="border px-2">Тема</th>
                      <th className="border px-2">Материалы</th>
                      <th className="border px-2">Домашка</th>
                      <th className="border px-2">Результаты</th>
                    </tr>
                  </thead>
                  <tbody>
                    {section.entries
                      .slice()
                      .sort((a, b) => a.order - b.order)
                      .map((entry) => (
                        <tr key={entry.id}>
                          <td className="border px-2">{entry.planned_date ?? "-"}</td>
                          <td className="border px-2">
                            {editMode ? (
                              <input
                                type="date"
                                className="border p-1"
                                value={entry.actual_date ?? ""}
                                onChange={(e) =>
                                  handleEntryEdit(section.id, entry.id, {
                                    actual_date: e.target.value,
                                  })
                                }
                              />
                            ) : (
                              entry.actual_date ?? "-"
                            )}
                          </td>
                          <td className="border px-2">{entry.type === "course" ? "Курс" : "Урок"}</td>
                          <td className="border px-2">{entry.title}</td>
                          <td className="border px-2">{entry.materials ?? "-"}</td>
                          <td className="border px-2">{entry.homework ?? "-"}</td>
                          <td className="border px-2">{entry.planned_outcomes ?? "-"}</td>
                          <td className="border px-2">
                              {editMode && (
                                <div className="flex gap-1">
                                  <button onClick={() => moveEntry(section, entry, "up")}>🔼</button>
                                  <button onClick={() => moveEntry(section, entry, "down")}>🔽</button>
                                  <button onClick={() => saveEntry(entry.id)}>💾</button>
                                  <button onClick={() => deleteEntry(entry.id)}>🗑️</button>
                                </div>
                              )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ))}

          {editMode && (
            <div className="mt-6">
              <input
                type="text"
                placeholder="Название раздела"
                className="border p-2 mr-2"
                value={newSectionTitle}
                onChange={(e) => setNewSectionTitle(e.target.value)}
              />
              <button
                className="px-4 py-2 bg-green-600 text-white rounded"
                onClick={handleAddSection}
              >
                ➕ Добавить раздел
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default KtpEditor;
