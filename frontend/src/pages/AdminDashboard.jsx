import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Calendar, ExternalLink, Pencil, Trash2, Upload } from "lucide-react";

const CATEGORY_OPTIONS = [
  "채용정보",
  "IT뉴스",
  "AI타임스",
  "자격증·공모전",
  "개발트렌드",
  "학습자료",
];

function DropZone({ onFileSelect, uploading, disabled }) {
  const [dragging, setDragging] = useState(false);

  return (
    <label
      onDragOver={(event) => {
        if (disabled) return;
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        if (disabled) return;
        event.preventDefault();
        setDragging(false);
        const file = event.dataTransfer.files?.[0];
        if (file) onFileSelect(file);
      }}
      className={`flex min-h-[156px] flex-col items-center justify-center rounded-2xl border-2 border-dashed px-5 py-6 text-center transition-colors ${disabled ? "cursor-not-allowed border-slate-200 bg-slate-100" : dragging ? "cursor-pointer border-primary-400 bg-primary-50" : "cursor-pointer border-slate-300 bg-slate-50"}`}
    >
      <Upload size={18} className="text-primary-500" />
      <p className="mt-3 text-sm font-semibold text-slate-700">
        파일 드래그 업로드
      </p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        {disabled
          ? "이 날짜에는 이미 자료가 있습니다. 수정 또는 삭제 후 다시 등록할 수 있습니다."
          : "AI가 내용을 정리하고, 지정한 날짜에 멘토 대시보드와 카카오 챗봇에 노출합니다."}
      </p>
      {uploading && (
        <p className="mt-3 text-xs text-slate-400">AI 정리 중입니다...</p>
      )}
      <input
        type="file"
        className="hidden"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFileSelect(file);
          event.target.value = "";
        }}
      />
    </label>
  );
}

function monthMatrix(year, month) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startOffset = firstDay.getDay();
  const days = [];
  for (let i = 0; i < startOffset; i += 1) days.push(null);
  for (let day = 1; day <= lastDay.getDate(); day += 1) days.push(day);
  while (days.length % 7 !== 0) days.push(null);
  return days;
}

function fmt(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function isPastDate(dateString) {
  return (
    new Date(`${dateString}T00:00:00`) < new Date(new Date().toDateString())
  );
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const today = new Date();
  const [items, setItems] = useState([]);
  const [category, setCategory] = useState("채용정보");
  const [selectedDate, setSelectedDate] = useState(
    today.toISOString().slice(0, 10),
  );
  const [linkValue, setLinkValue] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [editingId, setEditingId] = useState("");
  const [editingCategory, setEditingCategory] = useState("채용정보");
  const [editingDate, setEditingDate] = useState(
    today.toISOString().slice(0, 10),
  );

  const fetchItems = useCallback(async () => {
    const res = await fetch("/api/curation/items").catch(() => null);
    if (res?.ok) setItems(await res.json());
  }, []);

  useEffect(() => {
    if (user?.role === "admin") fetchItems();
  }, [fetchItems, user?.role]);

  const uploadFile = async (file) => {
    if (!file) return;
    if (hasItemForSelectedDate) {
      setError(
        "하루에는 큐레이션 자료를 1개만 등록할 수 있습니다. 기존 자료를 수정하거나 삭제해 주세요.",
      );
      return;
    }
    setUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    formData.append("date", selectedDate);

    try {
      const res = await fetch("/api/curation/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "업로드에 실패했습니다.");
      }
      await fetchItems();
      setSelectedDate(selectedDate);
    } catch (uploadError) {
      setError(uploadError.message || "업로드에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const uploadLink = async () => {
    if (!linkValue.trim()) return;
    if (hasItemForSelectedDate) {
      setError(
        "하루에는 큐레이션 자료를 1개만 등록할 수 있습니다. 기존 자료를 수정하거나 삭제해 주세요.",
      );
      return;
    }
    setUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("category", category);
    formData.append("date", selectedDate);
    formData.append("source_link", linkValue.trim());
    try {
      const res = await fetch("/api/curation/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "링크 등록에 실패했습니다.");
      }
      setLinkValue("");
      await fetchItems();
      setSelectedDate(selectedDate);
    } catch (uploadError) {
      setError(uploadError.message || "링크 등록에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const updateItem = async (itemId) => {
    const res = await fetch(`/api/curation/items/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category: editingCategory, date: editingDate }),
    }).catch(() => null);
    if (res?.ok) {
      const updatedDate = editingDate;
      const updatedCategory = editingCategory;
      setItems((prev) =>
        prev.map((item) =>
          item.id === itemId
            ? {
                ...item,
                category: updatedCategory,
                date: updatedDate,
                weekday: new Date(`${updatedDate}T00:00:00`).getDay(),
              }
            : item,
        ),
      );
      setEditingId("");
      setSelectedDate(updatedDate);
      await fetchItems();
    }
  };

  const deleteItem = async (itemId) => {
    const res = await fetch(`/api/curation/items/${itemId}`, {
      method: "DELETE",
    }).catch(() => null);
    if (!res?.ok) {
      setError("삭제에 실패했습니다.");
      return;
    }
    setItems((prev) => prev.filter((item) => item.id !== itemId));
    await fetchItems();
  };

  const dateItems = useMemo(
    () => items.filter((item) => item.date === selectedDate),
    [items, selectedDate],
  );
  const selectedDateCount = dateItems.length;
  const hasItemForSelectedDate = selectedDateCount >= 1;
  const selectedDateIsPast = isPastDate(selectedDate);
  const calendarDays = monthMatrix(viewYear, viewMonth);
  const itemCountByDate = useMemo(() => {
    const map = {};
    items.forEach((item) => {
      map[item.date] = (map[item.date] || 0) + 1;
    });
    return map;
  }, [items]);

  if (user?.role !== "admin") return null;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap gap-2">
          {CATEGORY_OPTIONS.map((option) => (
            <button
              key={option}
              onClick={() => setCategory(option)}
              className={`rounded-full px-5 py-3 text-base font-semibold transition-colors ${category === option ? "bg-primary-500 text-white shadow-sm" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
            >
              {option}
            </button>
          ))}
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-2xl border border-primary-100 bg-primary-50/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary-500">
                  Selected Date
                </p>
                <p className="mt-2 text-2xl font-bold text-slate-800">
                  {selectedDate}
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  달력에서 날짜를 누르면 해당 날짜로 바로 업로드됩니다.
                </p>
              </div>
              <div className="rounded-2xl bg-white px-4 py-3 text-right shadow-sm">
                <p className="text-xs text-slate-400">등록 현황</p>
                <p className="mt-1 text-lg font-semibold text-slate-800">
                  {selectedDateCount
                    ? `${selectedDateCount}개 등록`
                    : "비어 있음"}
                </p>
              </div>
            </div>
            <div className="mt-4">
              <DropZone
                onFileSelect={uploadFile}
                uploading={uploading}
                disabled={hasItemForSelectedDate}
              />
            </div>
            <div className="mt-3 min-h-6 text-sm">
              {hasItemForSelectedDate ? (
                <p className="text-slate-500">
                  하루에 1개만 설정할 수 있습니다. 기존 자료를 수정하거나 삭제해
                  주세요.
                </p>
              ) : selectedDateIsPast ? (
                <p className="text-amber-700">
                  지난 날짜는 확인만 가능하고 새 업로드는 권장하지 않습니다.
                </p>
              ) : (
                <p className="opacity-0">
                  지난 날짜는 확인만 가능하고 새 업로드는 권장하지 않습니다.
                </p>
              )}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Calendar size={16} className="text-primary-500" />
              링크 등록
            </div>
            <input
              value={linkValue}
              onChange={(event) => setLinkValue(event.target.value)}
              placeholder="https://example.com"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none focus:border-primary-300"
            />
            <button
              onClick={uploadLink}
              disabled={
                uploading || !linkValue.trim() || hasItemForSelectedDate
              }
              className="mt-3 w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              링크 등록
            </button>
            <p className="mt-4 text-sm leading-6 text-slate-500">
              관리자 자료는 하루 1개만 설정할 수 있으며, 링크면 AI가 내용을
              요약하고 원문 링크를 유지합니다. 첨부파일이면 AI가 내용을 정리하고
              원문 첨부를 열어볼 수 있게 제공합니다.
            </p>
            {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_minmax(420px,0.9fr)] xl:items-start">
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <button
              onClick={() => {
                if (viewMonth === 0) {
                  setViewYear((prev) => prev - 1);
                  setViewMonth(11);
                } else {
                  setViewMonth((prev) => prev - 1);
                }
              }}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600"
            >
              이전달
            </button>
            <p className="text-lg font-semibold text-slate-800">
              {viewYear}년 {viewMonth + 1}월
            </p>
            <button
              onClick={() => {
                if (viewMonth === 11) {
                  setViewYear((prev) => prev + 1);
                  setViewMonth(0);
                } else {
                  setViewMonth((prev) => prev + 1);
                }
              }}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600"
            >
              다음달
            </button>
          </div>
          <div className="mb-2 grid grid-cols-7 gap-2 text-center text-xs text-slate-400">
            {["일", "월", "화", "수", "목", "금", "토"].map((day) => (
              <div key={day}>{day}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {calendarDays.map((day, index) => {
              if (!day)
                return (
                  <div
                    key={`blank-${index}`}
                    className="h-24 rounded-xl bg-slate-50"
                  />
                );
              const dateKey = fmt(viewYear, viewMonth, day);
              const count = itemCountByDate[dateKey] || 0;
              const selected = selectedDate === dateKey;
              const past = isPastDate(dateKey);
              const cellClass = selected
                ? "border-primary-400 bg-primary-50 ring-1 ring-primary-200"
                : count > 0
                  ? "border-primary-100 bg-primary-50/70 hover:border-primary-200"
                  : past
                    ? "border-slate-200 bg-slate-100/80 hover:border-slate-300"
                    : "border-slate-200 bg-slate-50 hover:border-primary-200 hover:bg-white";
              return (
                <button
                  key={dateKey}
                  onClick={() => {
                    setSelectedDate(dateKey);
                    setError("");
                  }}
                  className={`h-24 rounded-xl border p-3 text-left transition-colors ${cellClass}`}
                >
                  <div className="text-sm font-semibold text-slate-700">
                    {day}
                  </div>
                  <div
                    className={`mt-3 text-xs ${count ? "text-primary-700" : past ? "text-slate-400" : "text-slate-500"}`}
                  >
                    {count ? `${count}개 등록` : "비어 있음"}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 xl:min-h-[724px] xl:max-h-[724px] xl:overflow-hidden">
          <div className="mb-4 text-sm font-semibold text-slate-700">
            {selectedDate} 등록 내용
          </div>
          <div className="space-y-3 xl:h-[650px] xl:overflow-y-auto pr-1">
            {dateItems.length ? (
              dateItems.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                    <span className="rounded-full bg-primary-50 px-2 py-1 text-primary-700">
                      {item.category}
                    </span>
                    {item.attachment_kind && (
                      <span>{item.attachment_kind}</span>
                    )}
                  </div>
                  <p className="break-words text-sm font-semibold leading-6 text-slate-800">
                    {item.title}
                  </p>
                  <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                    {item.summary}
                  </p>
                  {item.attachment_url && (
                    <a
                      href={item.attachment_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700"
                    >
                      첨부 열기 <ExternalLink size={12} />
                    </a>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <select
                      value={
                        editingId === item.id ? editingCategory : item.category
                      }
                      onChange={(event) => {
                        setEditingId(item.id);
                        setEditingCategory(event.target.value);
                        setEditingDate(
                          editingId === item.id ? editingDate : item.date,
                        );
                      }}
                      className="min-w-[180px] flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none"
                    >
                      {CATEGORY_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                    <input
                      type="date"
                      min={today.toISOString().slice(0, 10)}
                      value={editingId === item.id ? editingDate : item.date}
                      onChange={(event) => {
                        setEditingId(item.id);
                        setEditingDate(event.target.value);
                        setEditingCategory(
                          editingId === item.id
                            ? editingCategory
                            : item.category,
                        );
                      }}
                      className="min-w-[180px] flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none"
                    />
                    <button
                      onClick={() => {
                        setEditingId(item.id);
                        setEditingCategory(
                          editingId === item.id
                            ? editingCategory
                            : item.category,
                        );
                        setEditingDate(
                          editingId === item.id ? editingDate : item.date,
                        );
                        updateItem(item.id);
                      }}
                      className="inline-flex min-w-[108px] items-center justify-center gap-1 whitespace-nowrap rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
                    >
                      <Pencil size={14} /> 수정
                    </button>
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="inline-flex min-w-[108px] items-center justify-center gap-1 whitespace-nowrap rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600"
                    >
                      <Trash2 size={14} /> 삭제
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-400">
                선택한 날짜에 등록된 큐레이션이 없습니다.
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
