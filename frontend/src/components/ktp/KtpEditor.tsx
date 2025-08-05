import React, { useEffect, useState } from "react";
import axios from "axios";
import { formatSubject, formatGrade } from "../../utils/prepareLessons";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MoveUp, MoveDown, Trash2, Save } from "lucide-react";

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
  const [editedEntries, setEditedEntries] = useState<Record<number, Partial<KTPEntry>>>({});

  const handleEntryEdit = (sectionId: number, entryId: number, data: Partial<KTPEntry>) => {
    axios.patch(`/api/ktp/entries/${entryId}/`, data).then(refreshTemplate);
  };

    const saveEntry = (entryId: number) => {
      const patch = editedEntries[entryId];
      if (patch) {
        axios.patch(`/api/ktp/entries/${entryId}/`, patch).then(() => {
          setEditedEntries((prev) => {
            const newEdits = { ...prev };
            delete newEdits[entryId];
            return newEdits;
          });
          refreshTemplate();
        });
      }
    };

    const saveAll = () => {
      const requests = Object.entries(editedEntries).map(([id, patch]) =>
        axios.patch(`/api/ktp/entries/${id}/`, patch)
      );
      Promise.all(requests).then(() => {
        setEditedEntries({});
        refreshTemplate();
      });
    };

    const getEditedValue = (
      entryId: number,
      field: keyof KTPEntry,
      original: any
    ) => {
      return editedEntries[entryId]?.[field] ?? original;
    };

  const deleteEntry = (entryId: number) => {
    axios.delete(`/api/ktp/entries/${entryId}/`).then(refreshTemplate);
  };

  const moveEntry = (section: KTPSection, entry: KTPEntry, direction: "up" | "down") => {
    const entries = [...section.entries].sort((a, b) => a.order - b.order);
    const index = entries.findIndex((e) => e.id === entry.id);
    const targetIndex = direction === "up" ? index - 1 : index + 1;

    if (index < 0 || targetIndex < 0 || targetIndex >= entries.length) return;

    const current = entries[index];
    const target = entries[targetIndex];

    Promise.all([
      axios.patch(`/api/ktp/entries/${current.id}/`, { order: target.order }),
      axios.patch(`/api/ktp/entries/${target.id}/`, { order: current.order }),
    ]).then(refreshTemplate);
  };

  const handleSectionEdit = (sectionId: number, data: Partial<KTPSection>) => {
    axios.patch(`/api/ktp/sections/${sectionId}/`, data).then(refreshTemplate);
  };

  const moveSection = (sectionId: number, direction: "up" | "down") => {
    if (!selectedTemplate) return;
    const sections = [...selectedTemplate.sections].sort((a, b) => a.order - b.order);
    const index = sections.findIndex((s) => s.id === sectionId);
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (index < 0 || targetIndex < 0 || targetIndex >= sections.length) return;
    const current = sections[index];
    const target = sections[targetIndex];

    Promise.all([
      axios.patch(`/api/ktp/sections/${current.id}/`, { order: target.order }),
      axios.patch(`/api/ktp/sections/${target.id}/`, { order: current.order }),
    ]).then(refreshTemplate);
  };

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
      const savedSubject = localStorage.getItem("ktp_subject");
      const savedGrade = localStorage.getItem("ktp_grade");
      if (savedSubject) setSelectedSubjectId(Number(savedSubject));
      if (savedGrade) setSelectedGradeId(Number(savedGrade));
    }, []);

    useEffect(() => {
      if (selectedSubjectId && selectedGradeId && templates.length > 0) {
        const tpl = templates.find(
          (tpl) => tpl.subject === selectedSubjectId && tpl.grade === selectedGradeId
        );
        if (tpl) {
          setSelectedTemplateId(tpl.id);
        }
      }
    }, [selectedSubjectId, selectedGradeId, templates]);

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

    const handleAddEntry = (section: KTPSection) => {
      const maxOrder = Math.max(0, ...section.entries.map((e) => e.order));
      axios
        .post("/api/ktp/entries/", {
          section: section.id,
          title: "",
          type: "lesson",
          lesson_number: 1,
          order: maxOrder + 1,
        })
        .then(refreshTemplate)
        .catch((err) => {
          alert(JSON.stringify(err.response?.data || err));
          console.error("Ошибка при создании урока:", err.response?.data || err);
        });
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
      <h1 className="text-xl font-bold mb-4">Календарно-тематические планы</h1>

      <div className="flex gap-4 mb-4">
        <select
          className="border p-2"
            onChange={(e) => {
              const subjId = Number(e.target.value);
              localStorage.setItem("ktp_subject", subjId.toString());
              setSelectedSubjectId(subjId);
              setSelectedGradeId(null);
              setSelectedTemplateId(null);
            }}
          value={selectedSubjectId ?? ""}
        >
          <option value="">Выберите предмет</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {formatSubject(s)}
            </option>
          ))}
        </select>

        <select
          className="border p-2"
            onChange={(e) => {
              const gradeId = Number(e.target.value);
              localStorage.setItem("ktp_grade", gradeId.toString());
              setSelectedGradeId(gradeId);
              const tpl = templates.find(
                (tpl) => tpl.subject === selectedSubjectId && tpl.grade === gradeId
              );
              if (tpl) setSelectedTemplateId(tpl.id);
            }}
          value={selectedGradeId ?? ""}
          disabled={!selectedSubjectId}
        >
          <option value="">Выберите класс</option>
          {grades
            .filter((g) =>
              templates.some(
                (tpl) => tpl.subject === selectedSubjectId && tpl.grade === g.id
              )
            )
            .map((g) => (
              <option key={g.id} value={g.id}>
                {formatGrade(g)}
              </option>
            ))}
        </select>
      </div>

      {selectedTemplate && (
        <>
          <Button
            className="mb-4"
            variant={editMode ? "default" : "secondary"}
            onClick={() => setEditMode((prev) => !prev)}
          >
            {editMode ? "🚫 Выключить режим правок" : "✏️ Режим правок"}
          </Button>

            {editMode && (
              <Button
                variant="secondary"
                className="mb-4 ml-4"
                onClick={saveAll}
              >
                💾 Сохранить все
              </Button>
            )}

          {selectedTemplate.sections
            .slice()
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <div key={section.id} className="mb-6 border p-3 rounded bg-gray-50">
                <div className="flex justify-between items-center mb-2">
                  {editMode ? (
                    <Input
                      value={section.title}
                      onChange={(e) =>
                        handleSectionEdit(section.id, { title: e.target.value })
                      }
                      className="font-semibold text-lg w-full"
                    />
                  ) : (
                    <h2 className="text-lg font-semibold">
                      📂 {section.order}. {section.title} ({section.hours} ч)
                    </h2>
                  )}

                  {editMode && (
                    <div className="flex gap-1">
                      <Button size="icon" variant="ghost" onClick={() => moveSection(section.id, "up")}><MoveUp size={16} /></Button>
                      <Button size="icon" variant="ghost" onClick={() => moveSection(section.id, "down")}><MoveDown size={16} /></Button>
                    </div>
                  )}
                </div>

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
                      {editMode && <th className="border px-2">Действия</th>}
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
                                <Input
                                  type="date"
                                  value={getEditedValue(entry.id, "actual_date", entry.actual_date) || ""}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        actual_date: e.target.value,
                                      },
                                    }))
                                  }
                                />
                              ) : (
                                entry.actual_date ?? "-"
                              )}
                            </td>

                            <td className="border px-2">
                              {editMode ? (
                                <select
                                  className="border p-1 rounded"
                                  value={getEditedValue(entry.id, "type", entry.type)}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        type: e.target.value as "lesson" | "course",
                                      },
                                    }))
                                  }
                                >
                                  <option value="lesson">Урок</option>
                                  <option value="course">Курс</option>
                                </select>
                              ) : entry.type === "course" ? "Курс" : "Урок"}
                            </td>

                            <td className="border px-2">
                              {editMode ? (
                                <Input
                                  value={getEditedValue(entry.id, "title", entry.title)}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        title: e.target.value,
                                      },
                                    }))
                                  }
                                />
                              ) : (
                                entry.title
                              )}
                            </td>

                            <td className="border px-2">
                              {editMode ? (
                                <Input
                                  value={getEditedValue(entry.id, "materials", entry.materials)}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        materials: e.target.value,
                                      },
                                    }))
                                  }
                                />
                              ) : (
                                entry.materials ?? "-"
                              )}
                            </td>

                            <td className="border px-2">
                              {editMode ? (
                                <Input
                                  value={getEditedValue(entry.id, "homework", entry.homework)}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        homework: e.target.value,
                                      },
                                    }))
                                  }
                                />
                              ) : (
                                entry.homework ?? "-"
                              )}
                            </td>

                            <td className="border px-2">
                              {editMode ? (
                                <Input
                                  value={getEditedValue(entry.id, "planned_outcomes", entry.planned_outcomes)}
                                  onChange={(e) =>
                                    setEditedEntries((prev) => ({
                                      ...prev,
                                      [entry.id]: {
                                        ...prev[entry.id],
                                        planned_outcomes: e.target.value,
                                      },
                                    }))
                                  }
                                />
                              ) : (
                                entry.planned_outcomes ?? "-"
                              )}
                            </td>

                            {editMode && (
                              <td className="border px-2">
                                <div className="flex gap-1">
                                  <Button size="icon" variant="ghost" onClick={() => moveEntry(section, entry, "up")}><MoveUp size={14} /></Button>
                                  <Button size="icon" variant="ghost" onClick={() => moveEntry(section, entry, "down")}><MoveDown size={14} /></Button>
                                  <Button size="icon" variant="ghost" onClick={() => saveEntry(entry.id)}><Save size={14} /></Button>
                                  <Button size="icon" variant="default" onClick={() => deleteEntry(entry.id)}><Trash2 size={14} /></Button>
                                </div>
                              </td>
                            )}
                          </tr>
                        ))}
                    </tbody>
                    {editMode && (
                      <tfoot>
                        <tr>
                          <td colSpan={8} className="border px-2 text-right">
                            <Button
                              variant="ghost"
                              onClick={() => handleAddEntry(section)}
                            >
                              ➕ Добавить урок
                            </Button>
                          </td>
                        </tr>
                      </tfoot>
                    )}
                </table>
              </div>
            ))}

          {editMode && (
            <div className="mt-6 flex items-center gap-2">
              <Input
                placeholder="Название раздела"
                value={newSectionTitle}
                onChange={(e) => setNewSectionTitle(e.target.value)}
              />
              <Button variant="secondary" onClick={handleAddSection}>➕ Добавить раздел</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default KtpEditor;
