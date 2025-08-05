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

export default function AcademicCalendarEditor() {
  const [tab, setTab] = useState("years");
  const [years, setYears] = useState<any[]>([]);
  const [quarters, setQuarters] = useState<any[]>([]);
  const [holidays, setHolidays] = useState<any[]>([]);

  const [newYear, setNewYear] = useState({ name: "", start_date: "", end_date: "" });
  const [newQuarter, setNewQuarter] = useState({ year: "", name: "", start_date: "", end_date: "" });
  const [newHoliday, setNewHoliday] = useState({ date: "", name: "", type: "official" });

  const fetchAll = () => {
    axios.get("/api/core/academic-years/").then((r) => setYears(r.data));
    axios.get("/api/core/quarters/").then((r) => setQuarters(r.data));
    axios.get("/api/core/holidays/").then((r) => setHolidays(r.data));
  };

  useEffect(fetchAll, []);

  const updateItem = (url: string, id: number, data: any) => {
    axios.patch(`/api/core/${url}/${id}/`, data).then(fetchAll);
  };

  const createItem = (url: string, data: any, reset: () => void) => {
    axios.post(`/api/core/${url}/`, data).then(() => {
      reset();
      fetchAll();
    });
  };

  const quarterNameOptions = ["I", "II", "III", "IV"];

  const syncYearDates = (yearId: number) => {
    const yearQuarters = quarters.filter((q) => q.year === yearId);
    const q1 = yearQuarters.find((q) => q.name === "I");
    const q4 = yearQuarters.find((q) => q.name === "IV");
    const year = years.find((y) => y.id === yearId);

    const updates: any = {};
    if (q1?.start_date && year?.start_date !== q1.start_date) {
      updates.start_date = q1.start_date;
    }
    if (q4?.end_date && year?.end_date !== q4.end_date) {
      updates.end_date = q4.end_date;
    }
    if (Object.keys(updates).length > 0) {
      updateItem("academic-years", yearId, updates);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">🗓️ Учебный календарь</h1>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="years">📆 Учебные года</TabsTrigger>
          <TabsTrigger value="quarters">Ⅰ–Ⅳ Четверти</TabsTrigger>
          <TabsTrigger value="holidays">🎉 Праздники</TabsTrigger>
        </TabsList>

        <TabsContent value="years">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Название</TableHead>
                <TableHead>Начало</TableHead>
                <TableHead>Конец</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {years.map((y) => (
                <TableRow key={y.id}>
                  <TableCell>
                    <Input value={y.name} onChange={(e) => updateItem("academic-years", y.id, { name: e.target.value })} />
                  </TableCell>
                  <TableCell>
                    <Input type="date" value={y.start_date || ""} onChange={(e) => {
                      const val = e.target.value;
                      updateItem("academic-years", y.id, { start_date: val });
                      const q1 = quarters.find(q => q.year === y.id && q.name === "I");
                      if (!q1) createItem("quarters", { year: y.id, name: "I", start_date: val, end_date: val }, () => {});
                    }} />
                  </TableCell>
                  <TableCell>
                    <Input type="date" value={y.end_date || ""} onChange={(e) => {
                      const val = e.target.value;
                      updateItem("academic-years", y.id, { end_date: val });
                      const q4 = quarters.find(q => q.year === y.id && q.name === "IV");
                      if (!q4) createItem("quarters", { year: y.id, name: "IV", start_date: val, end_date: val }, () => {});
                    }} />
                  </TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <Input value={newYear.name} onChange={(e) => setNewYear({ ...newYear, name: e.target.value })} placeholder="Название" />
                </TableCell>
                <TableCell>
                  <Input type="date" value={newYear.start_date} onChange={(e) => setNewYear({ ...newYear, start_date: e.target.value })} />
                </TableCell>
                <TableCell>
                  <Input type="date" value={newYear.end_date} onChange={(e) => setNewYear({ ...newYear, end_date: e.target.value })} />
                  <Button className="mt-2" onClick={() => createItem("academic-years", newYear, () => setNewYear({ name: "", start_date: "", end_date: "" }))}>➕</Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="quarters">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Год</TableHead>
                <TableHead>Название</TableHead>
                <TableHead>Начало</TableHead>
                <TableHead>Конец</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {quarters.map((q) => (
                <TableRow key={q.id}>
                  <TableCell>{years.find(y => y.id === q.year)?.name || q.year}</TableCell>
                  <TableCell>
                    <select value={q.name} onChange={(e) => updateItem("quarters", q.id, { name: e.target.value })}>
                      {quarterNameOptions.map(qn => <option key={qn}>{qn}</option>)}
                    </select>
                  </TableCell>
                  <TableCell>
                    <Input type="date" value={q.start_date} onChange={(e) => {
                      updateItem("quarters", q.id, { start_date: e.target.value });
                      if (q.name === "I") syncYearDates(q.year);
                    }} />
                  </TableCell>
                  <TableCell>
                    <Input type="date" value={q.end_date} onChange={(e) => {
                      updateItem("quarters", q.id, { end_date: e.target.value });
                      if (q.name === "IV") syncYearDates(q.year);
                    }} />
                  </TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <select value={newQuarter.year} onChange={(e) => setNewQuarter({ ...newQuarter, year: e.target.value })}>
                    <option value="">Выберите год</option>
                    {years.map((y) => (
                      <option key={y.id} value={y.id}>{y.name}</option>
                    ))}
                  </select>
                </TableCell>
                <TableCell>
                  <select value={newQuarter.name} onChange={(e) => setNewQuarter({ ...newQuarter, name: e.target.value })}>
                    <option value="">Выберите</option>
                    {quarterNameOptions.map((q) => <option key={q}>{q}</option>)}
                  </select>
                </TableCell>
                <TableCell>
                  <Input type="date" value={newQuarter.start_date} onChange={(e) => setNewQuarter({ ...newQuarter, start_date: e.target.value })} />
                </TableCell>
                <TableCell>
                  <Input type="date" value={newQuarter.end_date} onChange={(e) => setNewQuarter({ ...newQuarter, end_date: e.target.value })} />
                  <Button className="mt-2" onClick={() => createItem("quarters", newQuarter, () => setNewQuarter({ year: "", name: "", start_date: "", end_date: "" }))}>➕</Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="holidays">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Дата</TableHead>
                <TableHead>Название</TableHead>
                <TableHead>Тип</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {holidays.map((h) => (
                <TableRow key={h.id}>
                  <TableCell>
                    <Input type="date" value={h.date} onChange={(e) => updateItem("holidays", h.id, { date: e.target.value })} />
                  </TableCell>
                  <TableCell>
                    <Input value={h.name} onChange={(e) => updateItem("holidays", h.id, { name: e.target.value })} />
                  </TableCell>
                  <TableCell>
                    <select value={h.type} onChange={(e) => updateItem("holidays", h.id, { type: e.target.value })}>
                      <option value="official">Официальный</option>
                      <option value="custom">Особый день</option>
                    </select>
                  </TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <Input type="date" value={newHoliday.date} onChange={(e) => setNewHoliday({ ...newHoliday, date: e.target.value })} />
                </TableCell>
                <TableCell>
                  <Input value={newHoliday.name} onChange={(e) => setNewHoliday({ ...newHoliday, name: e.target.value })} />
                </TableCell>
                <TableCell>
                  <select value={newHoliday.type} onChange={(e) => setNewHoliday({ ...newHoliday, type: e.target.value })}>
                    <option value="official">Официальный</option>
                    <option value="custom">Особый день</option>
                  </select>
                  <Button className="mt-2" onClick={() => createItem("holidays", newHoliday, () => setNewHoliday({ date: "", name: "", type: "official" }))}>➕</Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </div>
  );
}
