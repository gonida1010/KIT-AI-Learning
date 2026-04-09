import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Calendar,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  Info,
  RefreshCw,
  Trash2,
  User,
} from "lucide-react";

const WEEKDAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];
const DEFAULT_START_HOUR = "09:00";
const DEFAULT_END_HOUR = "22:00";

function fmt(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function getMonthDays(year, month) {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const startDay = first.getDay();
  const totalDays = last.getDate();
  const cells = [];
  for (let index = 0; index < startDay; index += 1) cells.push(null);
  for (let day = 1; day <= totalDays; day += 1) cells.push(day);
  return cells;
}

function slotStatus(slot) {
  if (slot.booked_by) return "booked";
  if (slot.slot_type === "blocked") return "blocked";
  return "available";
}

function BriefingPanel({ slot }) {
  if (!slot.briefing_report) {
    return (
      <p className="mt-3 text-xs text-slate-400">브리핑 리포트가 없습니다.</p>
    );
  }

  return (
    <div className="mt-3 space-y-2 rounded-xl bg-primary-50 p-3">
      <p className="text-xs font-semibold text-primary-700">LLM 요약</p>
      <div className="rounded-lg bg-white p-3 text-xs text-slate-600">
        <p className="font-medium text-slate-700">예약자</p>
        <p className="mt-1">{slot.booked_by_name || "수강생"}</p>
      </div>
      <div className="rounded-lg bg-white p-3 text-xs text-slate-600">
        <p className="font-medium text-slate-700">공부 내용</p>
        <p className="mt-1 break-words">
          {slot.booking_description || "내용 없음"}
        </p>
      </div>
      <div className="rounded-lg bg-white p-3 text-xs text-slate-600">
        <p className="font-medium text-slate-700">핵심 필요 내용</p>
        <p className="mt-1 break-words">{slot.briefing_report.core_need}</p>
      </div>
      <div className="rounded-lg bg-white p-3 text-xs text-slate-600">
        <p className="font-medium text-slate-700">추천 지도 방향</p>
        <p className="mt-1 break-words">
          {slot.briefing_report.ai_recommendation}
        </p>
      </div>
    </div>
  );
}

export default function TADashboard() {
  const { user } = useAuth();
  const detailSectionRef = useRef(null);
  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [notice, setNotice] = useState("");
  const [noticeType, setNoticeType] = useState("info");
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const nextMonthDate = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const lastNextMonthDate = new Date(
    today.getFullYear(),
    today.getMonth() + 2,
    0,
  );
  const [startDate, setStartDate] = useState(
    fmt(
      nextMonthDate.getFullYear(),
      nextMonthDate.getMonth(),
      nextMonthDate.getDate(),
    ),
  );
  const [endDate, setEndDate] = useState(
    fmt(
      lastNextMonthDate.getFullYear(),
      lastNextMonthDate.getMonth(),
      lastNextMonthDate.getDate(),
    ),
  );
  const [selectedWeekdays, setSelectedWeekdays] = useState([1, 2, 3, 4, 5]);
  const [unavailableStartDate, setUnavailableStartDate] = useState(
    fmt(
      nextMonthDate.getFullYear(),
      nextMonthDate.getMonth(),
      nextMonthDate.getDate(),
    ),
  );
  const [unavailableEndDate, setUnavailableEndDate] = useState(
    fmt(
      lastNextMonthDate.getFullYear(),
      lastNextMonthDate.getMonth(),
      lastNextMonthDate.getDate(),
    ),
  );
  const [unavailableWeekdays, setUnavailableWeekdays] = useState([0, 6]);
  const [breakStartTime, setBreakStartTime] = useState("12:00");
  const [breakEndTime, setBreakEndTime] = useState("13:00");
  const [saving, setSaving] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [showBaseScheduleForm, setShowBaseScheduleForm] = useState(false);
  const [showUnavailableForm, setShowUnavailableForm] = useState(false);
  const [unavailableMode, setUnavailableMode] = useState("holiday");

  const hourOptions = useMemo(
    () =>
      Array.from(
        { length: 14 },
        (_, index) => `${String(9 + index).padStart(2, "0")}:00`,
      ),
    [],
  );

  const setMessage = useCallback((message, type = "info") => {
    setNotice(message);
    setNoticeType(type);
  }, []);

  const fetchSlots = useCallback(async () => {
    const res = await fetch("/api/ta/slots").catch(() => null);
    if (res?.ok) {
      setSlots(await res.json());
      return;
    }
    setMessage("스케줄을 불러오지 못했습니다.", "error");
  }, [setMessage]);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  const visibleSlots = useMemo(
    () => slots.filter((slot) => slot.ta_id === user?.id),
    [slots, user?.id],
  );

  const slotsByDate = useMemo(() => {
    const grouped = {};
    visibleSlots.forEach((slot) => {
      if (!grouped[slot.date]) grouped[slot.date] = [];
      grouped[slot.date].push(slot);
    });
    return grouped;
  }, [visibleSlots]);

  const selectedDateSlots = selectedDate ? slotsByDate[selectedDate] || [] : [];

  const currentMonthSlots = useMemo(
    () =>
      visibleSlots.filter((slot) => {
        const slotDate = new Date(`${slot.date}T00:00:00`);
        return (
          slotDate.getFullYear() === viewYear &&
          slotDate.getMonth() === viewMonth
        );
      }),
    [visibleSlots, viewMonth, viewYear],
  );

  const summary = useMemo(
    () => ({
      blocked: currentMonthSlots.filter(
        (slot) => slotStatus(slot) === "blocked",
      ).length,
      booked: currentMonthSlots.filter((slot) => slotStatus(slot) === "booked")
        .length,
    }),
    [currentMonthSlots],
  );

  const cells = getMonthDays(viewYear, viewMonth);
  const selectedDateHasBlocked = selectedDateSlots.some(
    (slot) => slotStatus(slot) === "blocked",
  );

  const removeSlotsLocally = useCallback((slotIds) => {
    setSlots((prev) => prev.filter((slot) => !slotIds.includes(slot.id)));
  }, []);

  const initializeBaseSchedule = async () => {
    if (!selectedWeekdays.length || !user?.id) return;
    setInitializing(true);
    setMessage("");
    const res = await fetch("/api/ta/slots/base-template", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ta_id: user.id,
        ta_name: user.name,
        start_date: startDate,
        end_date: endDate,
        weekdays: selectedWeekdays.map((value) => (value + 6) % 7),
      }),
    }).catch(() => null);
    setInitializing(false);
    if (!res?.ok) {
      setMessage("기본 가능시간 초기 설정에 실패했습니다.", "error");
      return;
    }
    const data = await res.json().catch(() => ({}));
    setMessage(
      data.created_count
        ? `기본 가능시간 ${data.created_count}개를 생성했습니다.`
        : "이미 동일한 기본 가능시간이 등록되어 있습니다.",
      "success",
    );
    setShowBaseScheduleForm(false);
    fetchSlots();
  };

  const saveUnavailable = async () => {
    if (!unavailableWeekdays.length || !user?.id) return;
    if (unavailableMode === "break" && breakEndTime <= breakStartTime) {
      setMessage("휴식 시간 종료는 시작보다 늦어야 합니다.", "error");
      return;
    }

    setSaving(true);
    setMessage("");
    const startHour =
      unavailableMode === "holiday" ? 9 : Number(breakStartTime.slice(0, 2));
    const endHourExclusive =
      unavailableMode === "holiday" ? 22 : Number(breakEndTime.slice(0, 2));
    const requests = Array.from(
      { length: Math.max(0, endHourExclusive - startHour) },
      (_, index) => {
        const hour = startHour + index;
        return fetch("/api/ta/slots/bulk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ta_id: user.id,
            ta_name: user.name,
            start_date: unavailableStartDate,
            end_date: unavailableEndDate,
            weekdays: unavailableWeekdays.map((value) => (value + 6) % 7),
            start_time: `${String(hour).padStart(2, "0")}:00`,
            end_time: `${String(hour + 1).padStart(2, "0")}:00`,
            slot_type: "blocked",
            unavailable_reason: null,
          }),
        }).catch(() => null);
      },
    );

    const results = await Promise.all(requests);
    setSaving(false);
    const succeeded = results.filter((response) => response?.ok).length;
    if (!succeeded) {
      setMessage("불가 시간 등록에 실패했습니다.", "error");
      return;
    }
    setMessage(
      unavailableMode === "holiday"
        ? "선택한 기간에 휴무 시간을 등록했습니다."
        : "선택한 기간에 휴식 시간을 등록했습니다.",
      "success",
    );
    setShowUnavailableForm(false);
    fetchSlots();
  };

  const clearBlockedForDate = async () => {
    if (!selectedDate) return;
    const blockedSlots = (slotsByDate[selectedDate] || []).filter(
      (slot) => slotStatus(slot) === "blocked",
    );
    if (!blockedSlots.length) {
      setMessage("선택한 날짜에 취소할 불가 시간이 없습니다.", "info");
      return;
    }

    const results = await Promise.all(
      blockedSlots.map((slot) =>
        fetch(`/api/ta/slots/${slot.id}`, { method: "DELETE" }).catch(
          () => null,
        ),
      ),
    );
    if (results.some((response) => !response?.ok)) {
      setMessage("일부 불가 시간 취소에 실패했습니다.", "error");
      fetchSlots();
      return;
    }
    removeSlotsLocally(blockedSlots.map((slot) => slot.id));
    setMessage("선택한 날짜의 불가 시간을 취소했습니다.", "success");
    fetchSlots();
  };

  const deleteSlot = async (slotId) => {
    const res = await fetch(`/api/ta/slots/${slotId}`, {
      method: "DELETE",
    }).catch(() => null);
    if (!res?.ok) {
      const data = res ? await res.json().catch(() => ({})) : {};
      setMessage(data?.detail || "삭제에 실패했습니다.", "error");
      return;
    }
    removeSlotsLocally([slotId]);
    setMessage("선택한 시간을 삭제했습니다.", "success");
    fetchSlots();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800">조교 스케줄</h1>
          <p className="text-sm text-slate-500">
            기본 가능시간은 09:00-22:00, 1시간 단위로 일괄 생성하고 휴무와 휴식
            시간을 간단히 설정합니다.
          </p>
        </div>
        <button
          onClick={fetchSlots}
          className="rounded-lg border border-slate-200 bg-white p-2 text-slate-400 transition-colors hover:border-primary-300 hover:text-primary-600"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      {notice && (
        <div
          className={`rounded-2xl border px-4 py-3 text-sm ${noticeType === "error" ? "border-red-200 bg-red-50 text-red-700" : noticeType === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 bg-white text-slate-600"}`}
        >
          {notice}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
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
              className="rounded-lg border border-slate-200 p-2 text-slate-500"
            >
              <ChevronLeft size={18} />
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
              className="rounded-lg border border-slate-200 p-2 text-slate-500"
            >
              <ChevronRight size={18} />
            </button>
          </div>
          <div className="mb-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-amber-50 p-4 text-center">
              <p className="text-2xl font-bold text-amber-700">
                {summary.blocked}
              </p>
              <p className="mt-1 text-xs text-amber-700">휴무 / 불가</p>
            </div>
            <div className="rounded-xl bg-primary-50 p-4 text-center">
              <p className="text-2xl font-bold text-primary-700">
                {summary.booked}
              </p>
              <p className="mt-1 text-xs text-primary-700">예약 완료</p>
            </div>
          </div>
          <div className="mb-2 grid grid-cols-7 gap-2 text-center text-xs text-slate-400">
            {WEEKDAY_NAMES.map((day) => (
              <div key={day}>{day}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {cells.map((day, index) => {
              if (!day) {
                return (
                  <div
                    key={`blank-${index}`}
                    className="h-24 rounded-xl bg-slate-50"
                  />
                );
              }
              const dateKey = fmt(viewYear, viewMonth, day);
              const daySlots = slotsByDate[dateKey] || [];
              const booked = daySlots.filter(
                (slot) => slotStatus(slot) === "booked",
              ).length;
              const blocked = daySlots.filter(
                (slot) => slotStatus(slot) === "blocked",
              ).length;
              const available = daySlots.filter(
                (slot) => slotStatus(slot) === "available",
              ).length;
              const baseClass =
                selectedDate === dateKey
                  ? "border-primary-400 bg-primary-50"
                  : blocked > 0
                    ? "border-amber-200 bg-amber-50/70 hover:border-amber-300"
                    : available > 0
                      ? "border-emerald-200 bg-emerald-50/50 hover:border-emerald-300"
                      : "border-slate-200 bg-slate-50 hover:border-primary-200 hover:bg-white";

              return (
                <button
                  key={dateKey}
                  onClick={() => {
                    setSelectedDate(dateKey);
                    window.requestAnimationFrame(() => {
                      detailSectionRef.current?.scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                      });
                    });
                  }}
                  className={`h-24 rounded-xl border p-3 text-left transition-colors ${baseClass}`}
                >
                  <div className="text-sm font-semibold text-slate-700">
                    {day}
                  </div>
                  <div className="mt-2 text-[11px] text-slate-500">
                    {blocked > 0
                      ? `불가 ${blocked}`
                      : booked > 0
                        ? `예약 ${booked}`
                        : available > 0
                          ? `가능 ${available}`
                          : "등록 없음"}
                  </div>
                  <div className="mt-3 flex gap-1">
                    {available > 0 && (
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    )}
                    {blocked > 0 && (
                      <span className="h-2 w-2 rounded-full bg-amber-400" />
                    )}
                    {booked > 0 && (
                      <span className="h-2 w-2 rounded-full bg-primary-500" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <button
              onClick={() => setShowBaseScheduleForm((prev) => !prev)}
              className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition-colors hover:border-slate-300"
            >
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  기본 가능시간 초기 설정
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {DEFAULT_START_HOUR}-{DEFAULT_END_HOUR}, 1시간 단위 기본
                  시간표 생성
                </p>
              </div>
              {showBaseScheduleForm ? (
                <ChevronUp size={18} className="text-slate-400" />
              ) : (
                <ChevronDown size={18} className="text-slate-400" />
              )}
            </button>
            {showBaseScheduleForm && (
              <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 text-xs text-slate-500">시작 날짜</p>
                    <input
                      type="date"
                      min={today.toISOString().slice(0, 10)}
                      value={startDate}
                      onChange={(event) => setStartDate(event.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm outline-none"
                    />
                  </div>
                  <div>
                    <p className="mb-1 text-xs text-slate-500">종료 날짜</p>
                    <input
                      type="date"
                      min={startDate}
                      value={endDate}
                      onChange={(event) => setEndDate(event.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm outline-none"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <p className="mb-2 text-xs text-slate-500">기본 등록 요일</p>
                  <div className="flex flex-wrap gap-2">
                    {WEEKDAY_NAMES.map((day, index) => (
                      <button
                        key={day}
                        onClick={() =>
                          setSelectedWeekdays((prev) =>
                            prev.includes(index)
                              ? prev.filter((value) => value !== index)
                              : [...prev, index],
                          )
                        }
                        className={`rounded-full px-4 py-2 text-sm transition-colors ${selectedWeekdays.includes(index) ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={initializeBaseSchedule}
                  disabled={initializing || !selectedWeekdays.length}
                  className="mt-4 w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40"
                >
                  {initializing ? "초기 설정 중..." : "기본 가능시간 초기 설정"}
                </button>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-amber-200 bg-amber-50/60 p-5">
            <button
              onClick={() => setShowUnavailableForm((prev) => !prev)}
              className="flex w-full items-center justify-between rounded-xl border border-amber-200 bg-white/70 px-4 py-3 text-left transition-colors hover:border-amber-300"
            >
              <div>
                <p className="text-sm font-semibold text-amber-900">
                  휴무 / 불가 시간 설정
                </p>
                <p className="mt-1 text-xs text-amber-800">
                  전체 휴무 또는 짧은 휴식 시간을 토글로 설정합니다.
                </p>
              </div>
              {showUnavailableForm ? (
                <ChevronUp size={18} className="text-amber-700" />
              ) : (
                <ChevronDown size={18} className="text-amber-700" />
              )}
            </button>
            {showUnavailableForm && (
              <div className="mt-4 rounded-2xl border border-amber-200 bg-white p-4">
                <div className="grid gap-2 sm:grid-cols-2">
                  <button
                    onClick={() => setUnavailableMode("holiday")}
                    className={`rounded-xl px-4 py-3 text-sm font-medium ${unavailableMode === "holiday" ? "bg-amber-500 text-white" : "bg-amber-50 text-amber-900"}`}
                  >
                    휴무
                  </button>
                  <button
                    onClick={() => setUnavailableMode("break")}
                    className={`rounded-xl px-4 py-3 text-sm font-medium ${unavailableMode === "break" ? "bg-amber-500 text-white" : "bg-amber-50 text-amber-900"}`}
                  >
                    휴식 시간
                  </button>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 text-xs text-amber-800">시작 날짜</p>
                    <input
                      type="date"
                      min={today.toISOString().slice(0, 10)}
                      value={unavailableStartDate}
                      onChange={(event) =>
                        setUnavailableStartDate(event.target.value)
                      }
                      className="w-full rounded-xl border border-amber-200 bg-white px-3 py-3 text-sm outline-none"
                    />
                  </div>
                  <div>
                    <p className="mb-1 text-xs text-amber-800">종료 날짜</p>
                    <input
                      type="date"
                      min={unavailableStartDate}
                      value={unavailableEndDate}
                      onChange={(event) =>
                        setUnavailableEndDate(event.target.value)
                      }
                      className="w-full rounded-xl border border-amber-200 bg-white px-3 py-3 text-sm outline-none"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <p className="mb-2 text-xs text-amber-800">적용 요일</p>
                  <div className="flex flex-wrap gap-2">
                    {WEEKDAY_NAMES.map((day, index) => (
                      <button
                        key={`unavailable-${day}`}
                        onClick={() =>
                          setUnavailableWeekdays((prev) =>
                            prev.includes(index)
                              ? prev.filter((value) => value !== index)
                              : [...prev, index],
                          )
                        }
                        className={`rounded-full px-4 py-2 text-sm transition-colors ${unavailableWeekdays.includes(index) ? "bg-amber-500 text-white" : "bg-white text-amber-800"}`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
                {unavailableMode === "break" && (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="mb-1 text-xs text-amber-800">휴식 시작</p>
                      <select
                        value={breakStartTime}
                        onChange={(event) =>
                          setBreakStartTime(event.target.value)
                        }
                        className="w-full rounded-xl border border-amber-200 bg-white px-3 py-3 text-sm outline-none"
                      >
                        {hourOptions.slice(0, -1).map((time) => (
                          <option key={`start-${time}`} value={time}>
                            {time}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <p className="mb-1 text-xs text-amber-800">휴식 종료</p>
                      <select
                        value={breakEndTime}
                        onChange={(event) =>
                          setBreakEndTime(event.target.value)
                        }
                        className="w-full rounded-xl border border-amber-200 bg-white px-3 py-3 text-sm outline-none"
                      >
                        {hourOptions.slice(1).map((time) => (
                          <option key={`end-${time}`} value={time}>
                            {time}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
                <button
                  onClick={saveUnavailable}
                  disabled={saving || !unavailableWeekdays.length}
                  className="mt-4 w-full rounded-xl bg-amber-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-40"
                >
                  {saving
                    ? "저장 중..."
                    : unavailableMode === "holiday"
                      ? "휴무 등록"
                      : "휴식 시간 등록"}
                </button>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-start gap-3">
              <Info size={18} className="mt-0.5 text-primary-500" />
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  향후 확장 가능성
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  나중에는 수강생이 조교를 직접 선택하거나, 챗봇이 보충 요청
                  내용을 분석해 조교별 가능 영역에 맞춰 최적 조교를 자동
                  배정하는 흐름으로 확장할 수 있습니다.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>

      <section
        ref={detailSectionRef}
        className="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Calendar size={16} className="text-primary-500" />
            {selectedDate || "날짜를 선택하세요"}
          </div>
          {selectedDate && (
            <button
              onClick={clearBlockedForDate}
              disabled={!selectedDateHasBlocked}
              className="rounded-lg border border-amber-200 px-3 py-2 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              선택 날짜 불가 시간 취소
            </button>
          )}
        </div>
        {selectedDate ? (
          selectedDateSlots.length ? (
            <div className="space-y-3">
              {selectedDateSlots.map((slot) => {
                const status = slotStatus(slot);
                return (
                  <div
                    key={slot.id}
                    className={`rounded-xl border p-4 ${status === "booked" ? "border-primary-200 bg-primary-50/40" : status === "blocked" ? "border-amber-200 bg-amber-50/40" : "border-slate-200 bg-slate-50"}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                          <Clock size={14} className="text-slate-400" />
                          {slot.start_time} - {slot.end_time}
                        </p>
                        {status === "booked" && (
                          <div className="mt-2 space-y-1 text-xs text-slate-600">
                            <p className="flex items-center gap-1">
                              <User size={12} className="text-slate-400" />
                              예약자: {slot.booked_by_name || "수강생"}
                            </p>
                            <p>
                              공부 내용:{" "}
                              {slot.booking_description || "내용 없음"}
                            </p>
                          </div>
                        )}
                        {status === "blocked" && (
                          <p className="mt-2 text-xs text-amber-700">
                            설정된 불가 시간
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2 py-1 text-[11px] ${status === "booked" ? "bg-primary-100 text-primary-700" : status === "blocked" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}
                        >
                          {status === "booked"
                            ? "예약 완료"
                            : status === "blocked"
                              ? "불가"
                              : "예약 가능"}
                        </span>
                        {status !== "booked" && (
                          <button
                            onClick={() => deleteSlot(slot.id)}
                            className="rounded-lg border border-slate-200 p-2 text-slate-400 hover:text-red-500"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                    {status === "booked" && <BriefingPanel slot={slot} />}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-400">
              선택한 날짜에 등록된 시간이 없습니다.
            </div>
          )
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-400">
            달력에서 날짜를 선택하세요.
          </div>
        )}
      </section>
    </div>
  );
}
