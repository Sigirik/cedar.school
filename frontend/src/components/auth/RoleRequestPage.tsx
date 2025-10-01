// frontend/src/components/auth/RoleRequestPage.tsx
import React, { useEffect, useMemo, useState } from "react";
import api from "@/api/axios";
import { useNavigate } from "react-router-dom";

type AllowedRole = "STUDENT" | "PARENT";

// по умолчанию 1–11 (если у вас 12-летняя система — увеличьте)
const GRADE_NUMBERS = Array.from({ length: 11 }, (_, i) => i + 1);

const STUDENT_NET_TYPES = [
  { value: "WIRED_WIFI", label: "Проводной / Wi-Fi" },
  { value: "MOBILE", label: "Мобильная сеть (SIM/4G/5G)" },
  { value: "SATELLITE", label: "Спутниковый" },
] as const;

const STUDENT_PRIMARY_DEVICE = [
  { value: "DESKTOP_LAPTOP", label: "Компьютер / ноутбук" },
  { value: "TABLET", label: "Планшет" },
  { value: "SMARTPHONE", label: "Смартфон" },
] as const;

const EQUIPMENT_OPTIONS = [
  { value: "WEBCAM", label: "Веб-камера" },
  { value: "HEADSET", label: "Гарнитура / микрофон" },
  { value: "GRAPHICS_TABLET", label: "Графический планшет" },
] as const;

const ALL_ROLE_OPTIONS: { value: AllowedRole; label: string }[] = [
  { value: "STUDENT", label: "Ученик" },
  { value: "PARENT", label: "Родитель" },
];

// В Москве круглый год UTC+3, считаем «МСК ±N» из локального часового пояса
function guessMskDelta(): { delta: number; iana?: string } {
  const iana = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const now = new Date();
  const localUtcOffsetHours = -now.getTimezoneOffset() / 60; // например, -(-120)/60 = 2 для UTC+2
  const MSK = 3; // UTC+3
  let delta = Math.round(localUtcOffsetHours - MSK);
  // ограничим разумный диапазон
  if (delta < -12) delta = -12;
  if (delta > 12) delta = 12;
  return { delta, iana };
}

const MSK_DELTA_OPTIONS = Array.from({ length: 25 }, (_, i) => i - 12); // −12..+12

export default function RoleRequestPage() {
  const [role, setRole] = useState<AllowedRole | "">("");
  const [allowedRoles, setAllowedRoles] = useState<AllowedRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  // Общие поля
  const [fullName, setFullName] = useState("");

  // Анкета ученика
  const [birthDate, setBirthDate] = useState("");
  const [gender, setGender] = useState<"" | "MALE" | "FEMALE">("");
  const [country, setCountry] = useState("");
  const [city, setCity] = useState("");
  const guessed = useMemo(() => guessMskDelta(), []);
  const [mskDelta, setMskDelta] = useState<number>(guessed.delta);
  const [ianaTz] = useState<string | undefined>(guessed.iana);
  const [gradeNumber, setGradeNumber] = useState<number | "">("");

  const [netType, setNetType] = useState<typeof STUDENT_NET_TYPES[number]["value"] | "">("");
  const [primaryDevice, setPrimaryDevice] = useState<typeof STUDENT_PRIMARY_DEVICE[number]["value"] | "">("");
  const [equipment, setEquipment] = useState<string[]>([]);
  const [additionalInfo, setAdditionalInfo] = useState("");

  const navigate = useNavigate();

  // если роль уже назначена — на дашборд
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const me = await api.get("/api/auth/users/me/");
        if (!mounted) return;
        if (me.data?.role) {
          navigate("/dashboard");
          return;
        }
      } catch {
        // no-op
      }
      try {
        const al = await api.get("/api/role-requests/allowed-roles/");
        if (!mounted) return;
        const list = (al.data?.allowed ?? []) as AllowedRole[];
        setAllowedRoles(list);
        if (list.length && role && !list.includes(role as AllowedRole)) {
          setRole("");
        }
      } catch {
        setAllowedRoles(["STUDENT", "PARENT"]);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [navigate]);

  const roleOptions = useMemo(
    () => ALL_ROLE_OPTIONS.filter((o) => allowedRoles.includes(o.value)),
    [allowedRoles]
  );

  const toggleEquipment = (val: string) => {
    setEquipment((prev) =>
      prev.includes(val) ? prev.filter((v) => v !== val) : [...prev, val]
    );
  };

  const submitStudent = async () => {
    // Собираем развернутый additional_info
    const eqList =
      equipment.length > 0
        ? equipment
            .map((e) => {
              const found = EQUIPMENT_OPTIONS.find((x) => x.value === e);
              return found ? found.label : e;
            })
            .join(", ")
        : "нет";

    const netLabel = STUDENT_NET_TYPES.find((x) => x.value === netType)?.label || "";
    const devLabel = STUDENT_PRIMARY_DEVICE.find((x) => x.value === primaryDevice)?.label || "";

    const tzLabel = `МСК ${mskDelta > 0 ? `+${mskDelta}` : mskDelta}`;
    const tzTail = ianaTz ? ` (${ianaTz})` : "";

    const lines: string[] = [
      `Дата рождения: ${birthDate || "-"}`,
      `Пол: ${gender === "MALE" ? "мужской" : gender === "FEMALE" ? "женский" : "-"}`,
      `Страна: ${country || "-"}`,
      `Город: ${city || "-"}`,
      `Часовой пояс: ${tzLabel}${tzTail}`,
      `Класс (без буквы): ${gradeNumber || "-"}`,
      `Тип подключения: ${netLabel || "-"}`,
      `Основное устройство: ${devLabel || "-"}`,
      `Доп. оборудование: ${eqList}`,
    ];

    if (additionalInfo.trim()) {
      lines.push("");
      lines.push("Дополнительная информация:");
      lines.push(additionalInfo.trim());
    }

    await api.post("/api/role-requests/", {
      requested_role: "STUDENT",
      full_name: fullName || undefined,
      additional_info: lines.join("\n"),
    });
  };

  const submitParent = async () => {
    await api.post("/api/role-requests/", {
      requested_role: "PARENT",
      full_name: fullName || undefined,
      additional_info: additionalInfo.trim() || undefined,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!role) {
      setError("Выберите роль");
      return;
    }
    if (!fullName.trim()) {
      setError("Укажите ФИО");
      return;
    }

    try {
      if (role === "STUDENT") {
        if (!gradeNumber) {
          setError("Выберите номер класса");
          return;
        }
        await submitStudent();
      } else {
        await submitParent();
      }
      setSubmitted(true);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.requested_role?.[0] ||
        "Ошибка при отправке заявки";
      setError(msg);
    }
  };

  const StudentForm = (
    <>
      <label className="text-sm text-gray-700">ФИО *</label>
      <input
        type="text"
        placeholder="Иванов Иван Иванович"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        required
        className="border px-3 py-2 rounded"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-sm text-gray-700">Дата рождения</label>
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
        </div>
        <div>
          <label className="text-sm text-gray-700">Пол</label>
          <div className="flex items-center gap-4 mt-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="gender"
                value="MALE"
                checked={gender === "MALE"}
                onChange={() => setGender("MALE")}
              />
              Мужской
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="gender"
                value="FEMALE"
                checked={gender === "FEMALE"}
                onChange={() => setGender("FEMALE")}
              />
              Женский
            </label>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-sm text-gray-700">Страна</label>
          <input
            type="text"
            placeholder="Россия"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
        </div>
        <div>
          <label className="text-sm text-gray-700">Город</label>
          <input
            type="text"
            placeholder="Москва"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-sm text-gray-700">Часовой пояс</label>
          <select
            value={mskDelta}
            onChange={(e) => setMskDelta(parseInt(e.target.value, 10))}
            className="border px-3 py-2 rounded w-full"
          >
            {MSK_DELTA_OPTIONS.map((d) => (
              <option key={d} value={d}>
                МСК {d > 0 ? `+${d}` : d}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Предложено автоматически{ianaTz ? ` по таймзоне ${ianaTz}` : ""}. При
            необходимости поправьте вручную.
          </p>
        </div>

        <div>
          <label className="text-sm text-gray-700">В какой класс поступаете?</label>
          <select
            value={gradeNumber === "" ? "" : String(gradeNumber)}
            onChange={(e) => setGradeNumber(e.target.value ? Number(e.target.value) : "")}
            required
            className="border px-3 py-2 rounded w-full"
          >
            <option value="">Выберите номер класса</option>
            {GRADE_NUMBERS.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="text-sm text-gray-700">Тип подключения к интернету</label>
        <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
          {STUDENT_NET_TYPES.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm border rounded px-3 py-2">
              <input
                type="radio"
                name="netType"
                value={opt.value}
                checked={netType === opt.value}
                onChange={() => setNetType(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="text-sm text-gray-700">Основное устройство</label>
        <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
          {STUDENT_PRIMARY_DEVICE.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm border rounded px-3 py-2">
              <input
                type="radio"
                name="primaryDevice"
                value={opt.value}
                checked={primaryDevice === opt.value}
                onChange={() => setPrimaryDevice(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="text-sm text-gray-700">Дополнительное оборудование (галочки)</label>
        <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
          {EQUIPMENT_OPTIONS.map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 text-sm border rounded px-3 py-2">
              <input
                type="checkbox"
                checked={equipment.includes(opt.value)}
                onChange={() => toggleEquipment(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="text-sm text-gray-700">Дополнительная информация</label>
        <textarea
          placeholder="Любые комментарии: расписание, особенности, пожелания..."
          value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}
          rows={3}
          className="border px-3 py-2 rounded w-full"
        />
      </div>
    </>
  );

  const ParentForm = (
    <>
      <label className="text-sm text-gray-700">ФИО *</label>
      <input
        type="text"
        placeholder="Иванова Мария Петровна"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        required
        className="border px-3 py-2 rounded"
      />
      <div>
        <label className="text-sm text-gray-700">Дети</label>
        <textarea
          placeholder="ФИО детей и № класса (без буквы), по одному в строку"
          value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}
          rows={3}
          className="border px-3 py-2 rounded w-full"
        />
      </div>
      <p className="text-xs text-gray-500">
        Завуч распределит по параллели при подтверждении заявки.
      </p>
    </>
  );

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white p-6 rounded shadow w-full max-w-md text-center">
          <h2 className="text-xl font-semibold mb-4">Заявка отправлена</h2>
          <p>После подтверждения администрацией вы получите доступ к платформе.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white p-6 rounded shadow w-full max-w-xl">
        <h2 className="text-2xl font-semibold mb-4">Заявка на роль</h2>

        {loading ? (
          <div className="text-sm text-gray-500">Загрузка…</div>
        ) : allowedRoles.length === 0 ? (
          <div className="text-sm text-gray-600">
            Для вашей учётной записи заявка не требуется. Обратитесь к администратору.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <p className="text-red-500 text-sm">{error}</p>}

            <label className="text-sm text-gray-700">Кем вы являетесь? *</label>
            <select
              name="requested_role"
              value={role}
              onChange={(e) => {
                setRole(e.target.value as AllowedRole);
                // сбрасываем поля анкеты при смене роли
                setFullName("");
                setBirthDate("");
                setGender("");
                setCountry("");
                setCity("");
                setMskDelta(guessed.delta);
                setGradeNumber("");
                setNetType("");
                setPrimaryDevice("");
                setEquipment([]);
                setAdditionalInfo("");
              }}
              required
              className="border px-3 py-2 rounded"
            >
              <option value="">Выберите роль</option>
              {roleOptions.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>

            {role === "STUDENT" ? StudentForm : role === "PARENT" ? ParentForm : null}

            <button
              type="submit"
              disabled={!role}
              className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-60"
            >
              Отправить заявку
            </button>

          </form>
        )}
      </div>
    </div>
  );
}
