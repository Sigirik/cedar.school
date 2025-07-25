
import React, { useEffect, useState } from "react";
import axios from "axios";

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
  grade: number;
  academic_year: number;
  sections: KTPSection[];
};

const API_BASE = "http://localhost:8000/schedule/api/ktp/";

const KtpEditor: React.FC = () => {
  const [templates, setTemplates] = useState<KTPTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<KTPTemplate | null>(null);
  const [newSectionTitle, setNewSectionTitle] = useState("");
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    axios.get(API_BASE + "ktp-templates/").then((res) => setTemplates(res.data));
  }, []);

  useEffect(() => {
    if (selectedTemplateId !== null) {
      axios.get(API_BASE + "ktp-templates/" + selectedTemplateId + "/").then((res) => {
        setSelectedTemplate(res.data);
      });
    }
  }, [selectedTemplateId]);

  const refreshTemplate = () => {
    if (selectedTemplateId !== null) {
      axios.get(API_BASE + "ktp-templates/" + selectedTemplateId + "/").then((res) => {
        setSelectedTemplate(res.data);
      });
    }
  };

  const handleAddSection = () => {
    if (!newSectionTitle || !selectedTemplateId || !selectedTemplate) return;
    const maxOrder =
      selectedTemplate.sections.reduce((max, sec) => Math.max(max, sec.order), 0) ?? 0;
    axios
      .post(API_BASE + "ktp-sections/", {
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

  const moveSection = (sectionId: number, direction: "up" | "down") => {
    if (!selectedTemplate) return;
    const sections = [...selectedTemplate.sections].sort((a, b) => a.order - b.order);
    const index = sections.findIndex((s) => s.id === sectionId);
    const targetIndex = direction === "up" ? index - 1 : index + 1;

    if (index === -1 || targetIndex < 0 || targetIndex >= sections.length) return;

    const current = sections[index];
    const target = sections[targetIndex];

    Promise.all([
      axios.patch(API_BASE + "ktp-sections/" + current.id + "/", { order: target.order }),
      axios.patch(API_BASE + "ktp-sections/" + target.id + "/", { order: current.order }),
    ]).then(() => refreshTemplate());
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">КТП: редактор шаблона</h1>

      <select
        className="border p-2 mb-4"
        onChange={(e) => setSelectedTemplateId(Number(e.target.value))}
        value={selectedTemplateId ?? ""}
      >
        <option value="">Выберите шаблон КТП</option>
        {templates.map((tpl) => (
          <option key={tpl.id} value={tpl.id}>
            {tpl.name}
          </option>
        ))}
      </select>

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
                <div className="flex justify-between items-center mb-2">
                  <h2 className="text-lg font-semibold">
                    {section.order}. {section.title} ({section.hours} ч)
                  </h2>
                  {editMode && (
                    <div className="space-x-1">
                      <button
                        className="text-sm bg-blue-500 text-white px-2 py-1 rounded"
                        onClick={() => moveSection(section.id, "up")}
                      >
                        🔼
                      </button>
                      <button
                        className="text-sm bg-blue-500 text-white px-2 py-1 rounded"
                        onClick={() => moveSection(section.id, "down")}
                      >
                        🔽
                      </button>
                    </div>
                  )}
                </div>

                {section.entries.length > 0 ? (
                  <table className="table-auto w-full border text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="border px-2">#</th>
                        <th className="border px-2">Тип</th>
                        <th className="border px-2">Тема</th>
                        <th className="border px-2">Дата</th>
                        <th className="border px-2">Домашка</th>
                      </tr>
                    </thead>
                    <tbody>
                    {section.entries
                      .slice()
                      .sort((a, b) => a.order - b.order)
                      .map((entry, index) => (
                        <tr key={entry.id}>
                          <td className="border px-2">{entry.lesson_number}</td>
                          <td className="border px-2">
                            {editMode ? (
                              <select
                                value={entry.type}
                                onChange={(e) =>
                                  handleEntryEdit(section.id, entry.id, { type: e.target.value })
                                }
                              >
                                <option value="lesson">Урок</option>
                                <option value="course">Курс</option>
                              </select>
                            ) : (
                              entry.type === "lesson" ? "Урок" : "Курс"
                            )}
                          </td>
                          <td className="border px-2">
                            {editMode ? (
                              <input
                                value={entry.title}
                                onChange={(e) =>
                                  handleEntryEdit(section.id, entry.id, { title: e.target.value })
                                }
                              />
                            ) : (
                              entry.title
                            )}
                          </td>
                          <td className="border px-2">
                            {editMode ? (
                              <input
                                type="date"
                                value={entry.planned_date ?? ""}
                                onChange={(e) =>
                                  handleEntryEdit(section.id, entry.id, {
                                    planned_date: e.target.value,
                                  })
                                }
                              />
                            ) : (
                              entry.planned_date ?? "-"
                            )}
                          </td>
                          <td className="border px-2">
                            {editMode ? (
                              <input
                                value={entry.homework ?? ""}
                                onChange={(e) =>
                                  handleEntryEdit(section.id, entry.id, { homework: e.target.value })
                                }
                              />
                            ) : (
                              entry.homework ?? "-"
                            )}
                          </td>
                          <td className="border px-2">
                            {editMode && (
                              <>
                                <button onClick={() => moveEntry(section, entry, "up")}>🔼</button>
                                <button onClick={() => moveEntry(section, entry, "down")}>🔽</button>
                                <button onClick={() => saveEntry(entry.id)}>💾</button>
                                <button onClick={() => deleteEntry(entry.id)}>🗑️</button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-gray-500">Нет записей</p>
                )}
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
