import React, { useEffect, useState } from "react";
import axios from "axios";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface BaseItem {
  id: number;
  name: string;
}

export default function AdminReferenceEditor() {
  const [tab, setTab] = useState("subjects");
  const [subjects, setSubjects] = useState<BaseItem[]>([]);
  const [grades, setGrades] = useState<BaseItem[]>([]);
  const [lessonTypes, setLessonTypes] = useState<any[]>([]);

  const [newSubject, setNewSubject] = useState("");
  const [newGrade, setNewGrade] = useState("");

  const fetchData = () => {
    axios.get("/api/core/subjects/").then((res) => setSubjects(res.data));
    axios.get("/api/core/grades/").then((res) => setGrades(res.data));
    axios.get("/api/core/lesson-types/").then((res) => setLessonTypes(res.data));
  };

  useEffect(fetchData, []);

  const createSubject = () => {
    axios.post("/api/core/subjects/", { name: newSubject }).then(() => {
      setNewSubject("");
      fetchData();
    });
  };

  const updateSubject = (id: number, name: string) => {
    axios.patch(`/api/core/subjects/${id}/`, { name }).then(fetchData);
  };

  const createGrade = () => {
    axios.post("/api/core/grades/", { name: newGrade }).then(() => {
      setNewGrade("");
      fetchData();
    });
  };

  const updateGrade = (id: number, name: string) => {
    axios.patch(`/api/core/grades/${id}/`, { name }).then(fetchData);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">📋 Настройки школы</h1>
      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="subjects">📚 Предметы</TabsTrigger>
          <TabsTrigger value="grades">🎓 Классы</TabsTrigger>
          <TabsTrigger value="lessonTypes">📘 Типы уроков</TabsTrigger>
        </TabsList>

        <TabsContent value="subjects">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Название</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {subjects.map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{s.id}</TableCell>
                  <TableCell>
                    <Input
                      value={s.name}
                      onChange={(e) => updateSubject(s.id, e.target.value)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex gap-2 mt-4">
            <Input value={newSubject} onChange={(e) => setNewSubject(e.target.value)} placeholder="Новый предмет" />
            <Button onClick={createSubject}>➕ Добавить</Button>
          </div>
        </TabsContent>

        <TabsContent value="grades">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Название</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {grades.map((g) => (
                <TableRow key={g.id}>
                  <TableCell>{g.id}</TableCell>
                  <TableCell>
                    <Input
                      value={g.name}
                      onChange={(e) => updateGrade(g.id, e.target.value)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex gap-2 mt-4">
            <Input value={newGrade} onChange={(e) => setNewGrade(e.target.value)} placeholder="Новый класс (например, 5А)" />
            <Button onClick={createGrade}>➕ Добавить</Button>
          </div>
        </TabsContent>

        <TabsContent value="lessonTypes">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Ключ</TableHead>
                <TableHead>Название</TableHead>
                <TableHead>Учитывается в норме</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lessonTypes.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{t.id}</TableCell>
                  <TableCell>{t.key}</TableCell>
                  <TableCell>{t.label}</TableCell>
                  <TableCell>{t.counts_towards_norm ? "✅" : "🚫"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </div>
  );
}
