// frontend/src/components/admin/AdminRoleRequestsPage.tsx
import { useEffect, useMemo, useState } from "react";
import api from "@/api/axios";
import { Button, Input, Modal, Select, Table, Tag, message, Space, Typography } from "antd";

type Role = "STUDENT" | "PARENT" | "TEACHER" | "HEAD_TEACHER" | "DIRECTOR" | "ADMIN" | "AUDITOR";
type Status = "PENDING" | "APPROVED" | "REJECTED";

type RoleRequest = {
  id: number;
  username: string;
  current_role: Role | null;
  requested_role: Role;
  full_name?: string | null;
  additional_info?: string | null;
  status: Status;
  submitted_at: string; // ISO
};

const ROLE_LABEL: Record<Role, string> = {
  STUDENT: "Ученик",
  PARENT: "Родитель",
  TEACHER: "Учитель",
  HEAD_TEACHER: "Завуч",
  DIRECTOR: "Директор",
  ADMIN: "Администратор",
  AUDITOR: "Аудитор",
};

const STATUS_COLOR: Record<Status, string> = {
  PENDING: "gold",
  APPROVED: "green",
  REJECTED: "red",
};

export default function AdminRoleRequestsPage() {
  const [data, setData] = useState<RoleRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>("");

  // filters
  const [statusFilter, setStatusFilter] = useState<"ALL" | Status>("PENDING");
  const [roleFilter, setRoleFilter] = useState<"ALL" | "STUDENT" | "PARENT">("ALL");
  const [search, setSearch] = useState("");

  const fetchData = async () => {
    try {
      setError("");
      setLoading(true);
      const res = await api.get("/api/role-requests/");
      // поддержим и пагинацию DRF, и обычный список
      const items: RoleRequest[] = Array.isArray(res.data) ? res.data : (res.data.results ?? []);
      setData(items);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Не удалось загрузить заявки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refetch = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return data.filter((r) => {
      if (statusFilter !== "ALL" && r.status !== statusFilter) return false;
      if (roleFilter !== "ALL" && r.requested_role !== roleFilter) return false;
      if (!q) return true;
      const blob = [
        r.username,
        r.full_name || "",
        r.additional_info || "",
        ROLE_LABEL[r.requested_role],
        r.current_role ? ROLE_LABEL[r.current_role] : "",
      ]
        .join(" ")
        .toLowerCase();
      return blob.includes(q);
    });
  }, [data, statusFilter, roleFilter, search]);

  const approve = async (id: number) => {
    try {
      await api.post(`/api/role-requests/${id}/approve/`, {});
      message.success("Заявка одобрена");
      await refetch();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "Не удалось одобрить");
    }
  };

  const reject = async (id: number) => {
    try {
      await api.post(`/api/role-requests/${id}/reject/`, {});
      message.success("Заявка отклонена");
      await refetch();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "Не удалось отклонить");
    }
  };

  const confirmApprove = (row: RoleRequest) => {
    Modal.confirm({
      title: "Подтвердить назначение роли?",
      content: (
        <div>
          <div>
            Пользователь: <strong>{row.full_name || row.username}</strong>
          </div>
          <div>
            Запрошенная роль: <strong>{ROLE_LABEL[row.requested_role]}</strong>
          </div>
        </div>
      ),
      okText: "Одобрить",
      cancelText: "Отмена",
      onOk: () => approve(row.id),
    });
  };

  const confirmReject = (row: RoleRequest) => {
    Modal.confirm({
      title: "Отклонить заявку?",
      content: (
        <div>
          <div>
            Пользователь: <strong>{row.full_name || row.username}</strong>
          </div>
          <div>
            Запрошенная роль: <strong>{ROLE_LABEL[row.requested_role]}</strong>
          </div>
        </div>
      ),
      okText: "Отклонить",
      okButtonProps: { danger: true },
      cancelText: "Отмена",
      onOk: () => reject(row.id),
    });
  };

  const columns = [
    {
      title: "Пользователь",
      dataIndex: "username",
      key: "username",
      render: (_: any, row: RoleRequest) => (
        <Space direction="vertical" size={0}>
          <span className="font-medium">{row.full_name || "—"}</span>
          <span className="text-gray-500 text-xs">@{row.username}</span>
        </Space>
      ),
    },
    {
      title: "Роли",
      key: "roles",
      render: (_: any, row: RoleRequest) => (
        <Space direction="vertical" size={0}>
          <span className="text-xs text-gray-600">
            Текущая: {row.current_role ? ROLE_LABEL[row.current_role] : "—"}
          </span>
          <span>
            Запрошено: <Tag color="blue">{ROLE_LABEL[row.requested_role]}</Tag>
          </span>
        </Space>
      ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      render: (v: Status) => (
        <Tag color={STATUS_COLOR[v]}>
          {v === "PENDING" ? "Ожидает" : v === "APPROVED" ? "Одобрено" : "Отклонено"}
        </Tag>
      ),
      filters: [
        { text: "Ожидает", value: "PENDING" },
        { text: "Одобрено", value: "APPROVED" },
        { text: "Отклонено", value: "REJECTED" },
      ],
      onFilter: (val: any, rec: RoleRequest) => rec.status === val,
    },
    {
      title: "Отправлено",
      dataIndex: "submitted_at",
      key: "submitted_at",
      render: (v: string) => new Date(v).toLocaleString("ru-RU"),
      sorter: (a: RoleRequest, b: RoleRequest) =>
        new Date(a.submitted_at).getTime() - new Date(b.submitted_at).getTime(),
      defaultSortOrder: "descend" as const,
    },
    {
      title: "Действия",
      key: "actions",
      render: (_: any, row: RoleRequest) => (
        <Space>
          <Button
            size="small"
            onClick={() =>
              Modal.info({
                title: "Дополнительная информация",
                content: (
                  <pre style={{ whiteSpace: "pre-wrap" }}>
                    {row.additional_info?.trim() || "—"}
                  </pre>
                ),
                okText: "Закрыть",
              })
            }
          >
            Детали
          </Button>
          <Button
            size="small"
            type="primary"
            disabled={row.status !== "PENDING"}
            onClick={() => confirmApprove(row)}
          >
            Одобрить
          </Button>
          <Button
            size="small"
            danger
            disabled={row.status !== "PENDING"}
            onClick={() => confirmReject(row)}
          >
            Отклонить
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-4">
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        Заявки на роли
      </Typography.Title>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <Select
          value={statusFilter}
          onChange={(v) => setStatusFilter(v)}
          options={[
            { value: "ALL", label: "Все статусы" },
            { value: "PENDING", label: "Ожидают" },
            { value: "APPROVED", label: "Одобрены" },
            { value: "REJECTED", label: "Отклонены" },
          ]}
          style={{ width: 160 }}
        />
        <Select
          value={roleFilter}
          onChange={(v) => setRoleFilter(v)}
          options={[
            { value: "ALL", label: "Все роли" },
            { value: "STUDENT", label: ROLE_LABEL.STUDENT },
            { value: "PARENT", label: ROLE_LABEL.PARENT },
          ]}
          style={{ width: 160 }}
        />
        <Input.Search
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск (ФИО, логин, детали)"
          allowClear
          style={{ maxWidth: 320 }}
        />
        <Button onClick={refetch} loading={refreshing}>
          Обновить
        </Button>
      </div>

      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}

      <Table<RoleRequest>
        rowKey="id"
        columns={columns as any}
        dataSource={filtered}
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />
    </div>
  );
}
