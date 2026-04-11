import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Bot,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  Phone,
  RefreshCw,
  Send,
  User,
} from "lucide-react";

const WEEKDAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];
const WORKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"];
const FULL_DAY_HOURS = 13;
const TIME_OPTIONS = Array.from(
  { length: 14 },
  (_, index) => `${String(9 + index).padStart(2, "0")}:00`,
);

function fmt(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function formatMonthValue(year, month) {
  return `${year}-${String(month + 1).padStart(2, "0")}`;
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

function maskName(name) {
  const trimmed = (name || "").trim();
  if (!trimmed) return "수강생";
  if (trimmed.length === 1) return `${trimmed}*`;
  if (trimmed.length === 2) return `${trimmed[0]}*`;
  return `${trimmed[0]}${"*".repeat(trimmed.length - 2)}${trimmed.at(-1)}`;
}

function isFullHoliday(daySlots) {
  if (!daySlots.length) return false;
  const blocked = daySlots.filter(
    (slot) => slotStatus(slot) === "blocked",
  ).length;
  const hasBooked = daySlots.some((slot) => slotStatus(slot) === "booked");
  const hasAvailable = daySlots.some(
    (slot) => slotStatus(slot) === "available",
  );
  return !hasBooked && !hasAvailable && blocked >= FULL_DAY_HOURS;
}

function defaultManualRow() {
  return {
    mode: "none",
    startTime: "09:00",
    endTime: "16:00",
    breakEnabled: false,
    breakStart: "12:00",
    breakEnd: "13:00",
  };
}

function nextHour(time) {
  const hour = Number(time.slice(0, 2));
  return `${String(Math.min(hour + 1, 22)).padStart(2, "0")}:00`;
}

function previousHour(time) {
  const hour = Number(time.slice(0, 2));
  return `${String(Math.max(hour - 1, 9)).padStart(2, "0")}:00`;
}

function buildRangeLabels(hours) {
  if (!hours.length) return [];
  const sorted = [...new Set(hours)].sort((left, right) => left - right);
  const labels = [];
  let start = sorted[0];
  let end = sorted[0];

  for (let index = 1; index < sorted.length; index += 1) {
    const hour = sorted[index];
    if (hour === end + 1) {
      end = hour;
      continue;
    }
    labels.push(
      `${String(start).padStart(2, "0")}:00-${String(end + 1).padStart(2, "0")}:00`,
    );
    start = hour;
    end = hour;
  }

  labels.push(
    `${String(start).padStart(2, "0")}:00-${String(end + 1).padStart(2, "0")}:00`,
  );
  return labels;
}

function getDayScheduleLines(daySlots) {
  if (!daySlots.length) return [];
  if (isFullHoliday(daySlots)) return ["(휴무)"];
  const workingHours = daySlots
    .filter((slot) => ["available", "booked"].includes(slotStatus(slot)))
    .map((slot) => Number(slot.start_time.slice(0, 2)));
  return buildRangeLabels(workingHours);
}

function summarizeManualDraft(draft) {
  const parts = draft
    .map((row, weekday) => {
      if (row.mode === "off") return `${WORKDAY_NAMES[weekday]} 휴무`;
      if (row.mode !== "available") return null;
      const base = `${WORKDAY_NAMES[weekday]} ${row.startTime}-${row.endTime}`;
      if (row.breakEnabled && row.breakEnd > row.breakStart) {
        return `${base}, ${row.breakStart}-${row.breakEnd} 휴식`;
      }
      return base;
    })
    .filter(Boolean);

  return parts.length ? parts.join(" / ") : "설정된 수동 스케줄이 없습니다.";
}

function buildManualDraftFromPlan(plan) {
  const draft = Array.from({ length: 7 }, () => defaultManualRow());

  (plan?.available_rules || []).forEach((rule) => {
    (rule.weekdays || []).forEach((weekday) => {
      if (weekday < 0 || weekday > 6) return;
      draft[weekday] = {
        ...draft[weekday],
        mode: "available",
        startTime: rule.start_time || draft[weekday].startTime,
        endTime: rule.end_time || draft[weekday].endTime,
      };
    });
  });

  (plan?.full_day_off_rules || []).forEach((rule) => {
    (rule.weekdays || []).forEach((weekday) => {
      if (weekday < 0 || weekday > 6) return;
      draft[weekday] = { ...draft[weekday], mode: "off" };
    });
  });

  (plan?.partial_unavailable_rules || []).forEach((rule) => {
    (rule.weekdays || []).forEach((weekday) => {
      if (weekday < 0 || weekday > 6) return;
      draft[weekday] = {
        ...draft[weekday],
        breakEnabled: true,
        breakStart: rule.start_time || draft[weekday].breakStart,
        breakEnd: rule.end_time || draft[weekday].breakEnd,
      };
    });
  });

  return draft;
}

function draftToManualPlan(draft) {
  const available_rules = [];
  const full_day_off_rules = [];
  const partial_unavailable_rules = [];

  draft.forEach((row, weekday) => {
    if (row.mode === "available") {
      available_rules.push({
        weekdays: [weekday],
        dates: [],
        start_time: row.startTime,
        end_time: row.endTime,
      });
      if (row.breakEnabled && row.breakEnd > row.breakStart) {
        partial_unavailable_rules.push({
          weekdays: [weekday],
          dates: [],
          start_time: row.breakStart,
          end_time: row.breakEnd,
        });
      }
      return;
    }

    if (row.mode === "off") {
      full_day_off_rules.push({
        weekdays: [weekday],
        dates: [],
        start_time: "09:00",
        end_time: "22:00",
      });
    }
  });

  return {
    available_rules,
    full_day_off_rules,
    partial_unavailable_rules,
  };
}

function dateDraftToManualPlan(dateDraft) {
  const available_rules = [];
  const full_day_off_rules = [];
  const partial_unavailable_rules = [];

  Object.entries(dateDraft).forEach(([dateKey, row]) => {
    if (row.mode === "available") {
      available_rules.push({
        weekdays: [],
        dates: [dateKey],
        start_time: row.startTime,
        end_time: row.endTime,
      });
      if (row.breakEnabled && row.breakEnd > row.breakStart) {
        partial_unavailable_rules.push({
          weekdays: [],
          dates: [dateKey],
          start_time: row.breakStart,
          end_time: row.breakEnd,
        });
      }
    } else if (row.mode === "off") {
      full_day_off_rules.push({
        weekdays: [],
        dates: [dateKey],
        start_time: "09:00",
        end_time: "22:00",
      });
    }
  });

  return {
    mode: "date_override",
    available_rules,
    full_day_off_rules,
    partial_unavailable_rules,
  };
}

function buildDateDraftFromSlots(visibleSlots, monthValue) {
  const draft = {};
  const monthSlots = visibleSlots.filter((s) => s.date.startsWith(monthValue));
  const byDate = {};
  monthSlots.forEach((slot) => {
    if (!byDate[slot.date]) byDate[slot.date] = [];
    byDate[slot.date].push(slot);
  });

  Object.entries(byDate).forEach(([dateKey, daySlots]) => {
    if (isFullHoliday(daySlots)) {
      draft[dateKey] = { ...defaultManualRow(), mode: "off" };
      return;
    }
    const workingHours = new Set();
    const blockedHours = new Set();
    daySlots.forEach((slot) => {
      const hour = Number(slot.start_time.slice(0, 2));
      const st = slotStatus(slot);
      if (["available", "booked"].includes(st)) workingHours.add(hour);
      if (st === "blocked") blockedHours.add(hour);
    });
    if (workingHours.size) {
      const sorted = [...workingHours].sort((a, b) => a - b);
      const row = {
        ...defaultManualRow(),
        mode: "available",
        startTime: `${String(sorted[0]).padStart(2, "0")}:00`,
        endTime: `${String(sorted[sorted.length - 1] + 1).padStart(2, "0")}:00`,
      };
      const onlyBlocked = [...blockedHours].filter((h) => !workingHours.has(h));
      if (onlyBlocked.length) {
        const bs = [...onlyBlocked].sort((a, b) => a - b);
        row.breakEnabled = true;
        row.breakStart = `${String(bs[0]).padStart(2, "0")}:00`;
        row.breakEnd = `${String(bs[bs.length - 1] + 1).padStart(2, "0")}:00`;
      }
      draft[dateKey] = row;
    }
  });
  return draft;
}

function buildDraftFromSlots(visibleSlots, monthValue) {
  const draft = Array.from({ length: 7 }, () => defaultManualRow());
  const monthSlots = visibleSlots.filter((slot) =>
    slot.date.startsWith(monthValue),
  );
  const datesByWeekday = new Map();

  monthSlots.forEach((slot) => {
    const weekday = new Date(`${slot.date}T00:00:00`).getDay();
    const workdayIndex = (weekday + 6) % 7;
    if (!datesByWeekday.has(workdayIndex)) {
      datesByWeekday.set(workdayIndex, new Map());
    }
    const perDate = datesByWeekday.get(workdayIndex);
    if (!perDate.has(slot.date)) {
      perDate.set(slot.date, []);
    }
    perDate.get(slot.date).push(slot);
  });

  datesByWeekday.forEach((perDate, weekday) => {
    const workingHours = new Set();
    const blockedHours = new Set();
    let allHoliday = perDate.size > 0;

    [...perDate.values()].forEach((daySlots) => {
      const holiday = isFullHoliday(daySlots);
      if (!holiday) allHoliday = false;
      daySlots.forEach((slot) => {
        const hour = Number(slot.start_time.slice(0, 2));
        if (["available", "booked"].includes(slotStatus(slot))) {
          workingHours.add(hour);
        }
        if (slotStatus(slot) === "blocked" && !holiday) {
          blockedHours.add(hour);
        }
      });
    });

    if (allHoliday) {
      draft[weekday] = { ...draft[weekday], mode: "off" };
      return;
    }

    if (workingHours.size) {
      const sorted = [...workingHours].sort((left, right) => left - right);
      draft[weekday] = {
        ...draft[weekday],
        mode: "available",
        startTime: `${String(sorted[0]).padStart(2, "0")}:00`,
        endTime: `${String(sorted[sorted.length - 1] + 1).padStart(2, "0")}:00`,
      };
    }

    if (blockedHours.size) {
      const sorted = [...blockedHours].sort((left, right) => left - right);
      draft[weekday] = {
        ...draft[weekday],
        breakEnabled: true,
        breakStart: `${String(sorted[0]).padStart(2, "0")}:00`,
        breakEnd: `${String(sorted[sorted.length - 1] + 1).padStart(2, "0")}:00`,
      };
    }
  });

  return draft;
}

function BriefingPanel({ slot }) {
  if (!slot.briefing_report) return null;

  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2">
      <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
        <p className="font-medium text-slate-700">핵심 필요 내용</p>
        <p className="mt-1 break-words">{slot.briefing_report.core_need}</p>
      </div>
      <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
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
  const today = new Date();
  const todayKey = fmt(today.getFullYear(), today.getMonth(), today.getDate());

  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState(todayKey);
  const [notice, setNotice] = useState("");
  const [noticeType, setNoticeType] = useState("info");
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [assistantMonth, setAssistantMonth] = useState(
    formatMonthValue(today.getFullYear(), today.getMonth()),
  );
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantMessages, setAssistantMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "월을 고른 뒤 자연어로 보내면 제가 바로 이해한 내용을 짧게 정리하고 적용 여부를 먼저 확인합니다.",
    },
  ]);
  const [pendingRequest, setPendingRequest] = useState(null);
  const [loadingAssistant, setLoadingAssistant] = useState(false);
  const [manualDraft, setManualDraft] = useState(
    Array.from({ length: 7 }, () => defaultManualRow()),
  );
  const [manualEditorOpen, setManualEditorOpen] = useState(false);
  const [dateEditorOpen, setDateEditorOpen] = useState(false);
  const [dateDraft, setDateDraft] = useState({});
  const [editingDate, setEditingDate] = useState(null);

  const setMessage = useCallback((message, type = "info") => {
    setNotice(message);
    setNoticeType(type);
  }, []);

  const fetchSlots = useCallback(async () => {
    const res = await fetch("/api/ta/slots").catch(() => null);
    if (!res?.ok) {
      setMessage("스케줄을 불러오지 못했습니다.", "error");
      return;
    }
    setSlots(await res.json());
  }, [setMessage]);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  useEffect(() => {
    const [year, month] = assistantMonth.split("-").map(Number);
    if (!year || !month) return;
    setViewYear(year);
    setViewMonth(month - 1);
  }, [assistantMonth]);

  const visibleSlots = useMemo(
    () => slots.filter((slot) => slot.ta_id === user?.id),
    [slots, user?.id],
  );

  useEffect(() => {
    if (!pendingRequest) {
      setManualDraft(buildDraftFromSlots(visibleSlots, assistantMonth));
    }
  }, [assistantMonth, pendingRequest, visibleSlots]);

  const slotsByDate = useMemo(() => {
    const grouped = {};
    visibleSlots.forEach((slot) => {
      if (!grouped[slot.date]) grouped[slot.date] = [];
      grouped[slot.date].push(slot);
    });
    return grouped;
  }, [visibleSlots]);

  const currentMonthSlots = useMemo(
    () =>
      visibleSlots.filter((slot) => {
        const slotDate = new Date(`${slot.date}T00:00:00`);
        return (
          slotDate.getFullYear() === viewYear &&
          slotDate.getMonth() === viewMonth
        );
      }),
    [viewMonth, viewYear, visibleSlots],
  );

  const summary = useMemo(
    () => ({
      booked: currentMonthSlots.filter((slot) => slotStatus(slot) === "booked")
        .length,
    }),
    [currentMonthSlots],
  );

  const selectedBookedSlots = useMemo(
    () =>
      (slotsByDate[selectedDate] || [])
        .filter((slot) => slotStatus(slot) === "booked")
        .sort((left, right) => left.start_time.localeCompare(right.start_time)),
    [selectedDate, slotsByDate],
  );

  const manualSummary = useMemo(
    () => summarizeManualDraft(manualDraft),
    [manualDraft],
  );

  const cells = getMonthDays(viewYear, viewMonth);

  const previewScheduleRequest = async (
    message,
    manualPlan = null,
    targetMonth = assistantMonth,
  ) => {
    if (!user?.id || loadingAssistant) return null;
    setLoadingAssistant(true);
    const res = await fetch("/api/ta/schedule-assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ta_id: user.id,
        ta_name: user.name,
        target_month: targetMonth,
        message,
        manual_plan: manualPlan,
        apply: false,
      }),
    }).catch(() => null);
    setLoadingAssistant(false);

    if (!res?.ok) {
      const data = res ? await res.json().catch(() => ({})) : {};
      setMessage(data?.detail || "스케줄 해석에 실패했습니다.", "error");
      return null;
    }

    return res.json();
  };

  const applyScheduleRequest = async ({ message, manualPlan, targetMonth }) => {
    if (!user?.id || loadingAssistant) return;

    setLoadingAssistant(true);
    const res = await fetch("/api/ta/schedule-assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ta_id: user.id,
        ta_name: user.name,
        target_month: targetMonth,
        message,
        manual_plan: manualPlan,
        apply: true,
      }),
    }).catch(() => null);
    setLoadingAssistant(false);

    if (!res?.ok) {
      const data = res ? await res.json().catch(() => ({})) : {};
      setMessage(data?.detail || "적용에 실패했습니다.", "error");
      return;
    }

    const data = await res.json();
    setPendingRequest(null);
    setMessage(
      "월간 스케줄을 적용했습니다. 기존 예약 기록은 유지됩니다.",
      "success",
    );
    setAssistantMessages((prev) => [
      ...prev,
      {
        id: `assistant-apply-${Date.now()}`,
        role: "assistant",
        content: `${data.summary}\n적용 완료`,
      },
    ]);
    fetchSlots();
  };

  const submitAssistantMessage = async () => {
    const message = assistantInput.trim();
    if (!message) return;

    setAssistantMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: message },
    ]);

    const data = await previewScheduleRequest(message, null, assistantMonth);
    if (!data) return;

    setPendingRequest({
      targetMonth: assistantMonth,
      message,
      manualPlan: data.plan,
      summary: data.summary,
    });
    setManualDraft(buildManualDraftFromPlan(data.plan));
    setAssistantMessages((prev) => [
      ...prev,
      {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: `${data.summary}\n적용하시겠습니까?`,
      },
    ]);
    setAssistantInput("");
  };

  const previewManualDraft = async () => {
    const manualPlan = draftToManualPlan(manualDraft);
    const data = await previewScheduleRequest(
      "manual",
      manualPlan,
      assistantMonth,
    );
    if (!data) return;

    setPendingRequest({
      targetMonth: assistantMonth,
      message: "manual",
      manualPlan,
      summary: data.summary,
    });
    setAssistantMessages((prev) => [
      ...prev,
      {
        id: `assistant-manual-${Date.now()}`,
        role: "assistant",
        content: `${data.summary}\n수정안입니다. 적용하시겠습니까?`,
      },
    ]);
  };

  const applyPendingRequest = async () => {
    if (!pendingRequest) return;
    await applyScheduleRequest({
      message: pendingRequest.message,
      manualPlan: pendingRequest.manualPlan,
      targetMonth: pendingRequest.targetMonth,
    });
  };

  const applyManualDraftDirectly = async () => {
    const manualPlan = draftToManualPlan(manualDraft);
    await applyScheduleRequest({
      message: "manual",
      manualPlan,
      targetMonth: assistantMonth,
    });
  };

  const applyDateDraft = async () => {
    const entries = Object.entries(dateDraft).filter(
      ([, row]) => row.mode !== "none",
    );
    if (!entries.length) {
      setMessage("날짜별로 설정된 항목이 없습니다.", "error");
      return;
    }
    const manualPlan = dateDraftToManualPlan(dateDraft);
    await applyScheduleRequest({
      message: "date_manual",
      manualPlan,
      targetMonth: assistantMonth,
    });
    setDateDraft({});
    setEditingDate(null);
  };

  const updateDateRow = (dateKey, updates) => {
    setDateDraft((prev) => ({
      ...prev,
      [dateKey]: { ...(prev[dateKey] || defaultManualRow()), ...updates },
    }));
  };

  const removeDateRow = (dateKey) => {
    setDateDraft((prev) => {
      const next = { ...prev };
      delete next[dateKey];
      return next;
    });
    if (editingDate === dateKey) setEditingDate(null);
  };

  const updateManualRow = (weekday, nextRow) => {
    setManualDraft((prev) =>
      prev.map((row, index) =>
        index === weekday ? { ...row, ...nextRow } : row,
      ),
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800">조교 스케줄</h1>
          <p className="text-sm text-slate-500">
            챗봇은 먼저 이해한 내용을 확인받고, 수동 스케줄 설정은 별도로 접어둘
            수 있습니다.
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

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="space-y-6 rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
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

          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs font-medium text-slate-500">
              이번 달 예약 완료
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {summary.booked}
            </p>
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
              const bookedCount = daySlots.filter(
                (slot) => slotStatus(slot) === "booked",
              ).length;
              const scheduleLines = getDayScheduleLines(daySlots);
              const fullHoliday = isFullHoliday(daySlots);
              const hoverLines = fullHoliday
                ? ["종일 휴무"]
                : [
                    ...scheduleLines.map((line) => `예약 가능 ${line}`),
                    ...(bookedCount > 0 ? [`예약 ${bookedCount}건`] : []),
                  ];
              const isToday = dateKey === todayKey;
              const isSelected = selectedDate === dateKey;

              const baseClass = isSelected
                ? "border-primary-500 bg-primary-50"
                : fullHoliday
                  ? "border-amber-300 bg-amber-50 text-amber-900"
                  : bookedCount > 0
                    ? "border-primary-300 bg-primary-100"
                    : isToday
                      ? "border-slate-800 bg-slate-100"
                      : "border-slate-200 bg-white hover:border-slate-300";

              return (
                <div key={dateKey} className="group relative">
                  <button
                    onClick={() => {
                      setSelectedDate(dateKey);
                      window.requestAnimationFrame(() => {
                        detailSectionRef.current?.scrollIntoView({
                          behavior: "smooth",
                          block: "start",
                        });
                      });
                    }}
                    className={`h-24 w-full overflow-hidden rounded-xl border p-3 text-left transition-colors ${baseClass}`}
                  >
                    <div className="text-sm font-semibold text-slate-700">
                      {day}
                    </div>
                    <div className="mt-2 space-y-1 overflow-hidden text-[10px] leading-3 text-slate-500">
                      {fullHoliday ? (
                        <p className="truncate">(휴무)</p>
                      ) : scheduleLines.length ? (
                        <>
                          {scheduleLines.slice(0, 2).map((line) => (
                            <p key={`${dateKey}-${line}`} className="truncate">
                              {line}
                            </p>
                          ))}
                          {scheduleLines.length > 2 && (
                            <p className="truncate text-[9px] text-slate-400">
                              +{scheduleLines.length - 2}개 더 보기
                            </p>
                          )}
                        </>
                      ) : bookedCount > 0 ? (
                        <p className="truncate">예약 {bookedCount}</p>
                      ) : null}
                    </div>
                  </button>

                  {hoverLines.length > 0 && (
                    <div className="pointer-events-none absolute left-1/2 top-0 z-20 hidden w-44 -translate-x-1/2 -translate-y-[calc(100%+8px)] rounded-xl border border-slate-200 bg-slate-950/95 px-3 py-2 text-[11px] leading-4 text-white opacity-0 shadow-2xl transition-all duration-150 group-hover:opacity-100 md:block">
                      <p className="mb-1 font-semibold text-slate-200">
                        {viewMonth + 1}월 {day}일
                      </p>
                      <div className="space-y-1">
                        {hoverLines.map((line) => (
                          <p
                            key={`${dateKey}-hover-${line}`}
                            className="break-words"
                          >
                            {line}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Bot size={16} className="text-primary-500" />
              월간 스케줄 챗봇
            </div>
            <input
              type="month"
              value={assistantMonth}
              onChange={(event) => {
                setAssistantMonth(event.target.value);
                setPendingRequest(null);
              }}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none"
            />
          </div>

          <div className="max-h-[200px] space-y-3 overflow-y-auto rounded-2xl bg-slate-50 p-4">
            {assistantMessages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-slate-900 text-white" : "border border-slate-200 bg-white text-slate-700"}`}
                  style={{
                    display: "-webkit-box",
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {message.content}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <button
              onClick={() =>
                setAssistantInput(
                  `나 ${Number(assistantMonth.slice(5))}월에 토일 휴무, 나머지 요일은 09시부터 16시까지 예약가능`,
                )
              }
              className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-primary-300 hover:text-primary-700"
            >
              예시 넣기
            </button>
            <textarea
              value={assistantInput}
              onChange={(event) => setAssistantInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submitAssistantMessage();
                }
              }}
              placeholder="예: 나 4월에 토일 휴무, 나머지 요일은 09시부터 16시까지 예약가능"
              className="mt-3 min-h-[110px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none"
            />
            <button
              onClick={submitAssistantMessage}
              disabled={!assistantInput.trim() || loadingAssistant}
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-primary-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-600 disabled:opacity-40"
            >
              <Send size={16} />
              {loadingAssistant ? "이해 중..." : "챗봇에게 보내기"}
            </button>
          </div>

          {pendingRequest && (
            <div className="rounded-2xl border border-primary-200 bg-primary-50 p-4 text-sm text-primary-800">
              <div className="flex items-start gap-2">
                <CheckCircle2 size={16} className="mt-0.5" />
                <p>{pendingRequest.summary}</p>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={applyPendingRequest}
                  disabled={loadingAssistant}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40"
                >
                  적용
                </button>
                <button
                  onClick={() => setPendingRequest(null)}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300"
                >
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="rounded-2xl border border-primary-200 bg-primary-50 p-4 shadow-[0_18px_45px_-35px_rgba(59,130,246,0.65)] transition-shadow hover:shadow-[0_24px_50px_-32px_rgba(59,130,246,0.8)]">
            <button
              onClick={() => setManualEditorOpen((prev) => !prev)}
              className="group flex w-full items-center justify-between gap-4 rounded-2xl text-left"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-primary-800">
                  수동 스케줄 설정
                </p>
                <p className="mt-1 text-xs leading-5 text-primary-700">
                  {manualSummary}
                </p>
                <p className="mt-2 text-[11px] font-medium text-primary-500">
                  카드 전체를 눌러 펼치고 접을 수 있습니다.
                </p>
              </div>
              <div className="inline-flex shrink-0 items-center gap-2 rounded-full border border-primary-200 bg-white px-3 py-2 text-xs font-semibold text-primary-700 shadow-sm transition-all group-hover:border-primary-300 group-hover:bg-white/95">
                <span>{manualEditorOpen ? "접기" : "펼쳐보기"}</span>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${manualEditorOpen ? "rotate-180" : "rotate-0"}`}
                />
              </div>
            </button>

            {manualEditorOpen && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-xs leading-5 text-slate-500">
                    요일별로 직접 수정하고, 미리보기 또는 바로 적용을
                    선택하세요.
                  </p>
                  <button
                    onClick={() => {
                      setPendingRequest(null);
                      setManualDraft(
                        buildDraftFromSlots(visibleSlots, assistantMonth),
                      );
                    }}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300"
                  >
                    현재 적용값 불러오기
                  </button>
                </div>

                <div className="space-y-3">
                  {manualDraft.map((row, weekday) => (
                    <div
                      key={WORKDAY_NAMES[weekday]}
                      className="rounded-2xl border border-slate-200 bg-white p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-700">
                          {WORKDAY_NAMES[weekday]}
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={() =>
                              updateManualRow(weekday, { mode: "none" })
                            }
                            className={`rounded-full px-3 py-1.5 text-xs font-medium ${row.mode === "none" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
                          >
                            설정 없음
                          </button>
                          <button
                            onClick={() =>
                              updateManualRow(weekday, { mode: "available" })
                            }
                            className={`rounded-full px-3 py-1.5 text-xs font-medium ${row.mode === "available" ? "bg-primary-500 text-white" : "bg-slate-100 text-slate-600"}`}
                          >
                            예약 가능
                          </button>
                          <button
                            onClick={() =>
                              updateManualRow(weekday, { mode: "off" })
                            }
                            className={`rounded-full px-3 py-1.5 text-xs font-medium ${row.mode === "off" ? "bg-amber-500 text-white" : "bg-slate-100 text-slate-600"}`}
                          >
                            전체 휴무
                          </button>
                        </div>
                      </div>

                      {row.mode === "available" && (
                        <div className="mt-4 space-y-3">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <label className="text-xs text-slate-500">
                              시작 시간
                              <select
                                value={row.startTime}
                                onChange={(event) => {
                                  const nextStart = event.target.value;
                                  updateManualRow(weekday, {
                                    startTime: nextStart,
                                    endTime:
                                      row.endTime <= nextStart
                                        ? nextHour(nextStart)
                                        : row.endTime,
                                  });
                                }}
                                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 outline-none"
                              >
                                {TIME_OPTIONS.slice(0, -1).map((time) => (
                                  <option
                                    key={`${WORKDAY_NAMES[weekday]}-start-${time}`}
                                    value={time}
                                  >
                                    {time}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <label className="text-xs text-slate-500">
                              종료 시간
                              <select
                                value={row.endTime}
                                onChange={(event) => {
                                  const nextEnd = event.target.value;
                                  updateManualRow(weekday, {
                                    endTime: nextEnd,
                                    startTime:
                                      nextEnd <= row.startTime
                                        ? previousHour(nextEnd)
                                        : row.startTime,
                                  });
                                }}
                                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 outline-none"
                              >
                                {TIME_OPTIONS.slice(1).map((time) => (
                                  <option
                                    key={`${WORKDAY_NAMES[weekday]}-end-${time}`}
                                    value={time}
                                  >
                                    {time}
                                  </option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                            <div className="flex items-center justify-between gap-3">
                              <p className="text-xs font-medium text-slate-600">
                                휴식 시간
                              </p>
                              <button
                                onClick={() =>
                                  updateManualRow(weekday, {
                                    breakEnabled: !row.breakEnabled,
                                  })
                                }
                                className={`rounded-full px-3 py-1.5 text-xs font-medium ${row.breakEnabled ? "bg-amber-500 text-white" : "border border-slate-200 bg-white text-slate-600"}`}
                              >
                                {row.breakEnabled ? "사용 중" : "없음"}
                              </button>
                            </div>
                            {row.breakEnabled && (
                              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                                <label className="text-xs text-slate-500">
                                  휴식 시작
                                  <select
                                    value={row.breakStart}
                                    onChange={(event) => {
                                      const nextStart = event.target.value;
                                      updateManualRow(weekday, {
                                        breakStart: nextStart,
                                        breakEnd:
                                          row.breakEnd <= nextStart
                                            ? nextHour(nextStart)
                                            : row.breakEnd,
                                      });
                                    }}
                                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 outline-none"
                                  >
                                    {TIME_OPTIONS.slice(0, -1).map((time) => (
                                      <option
                                        key={`${WORKDAY_NAMES[weekday]}-break-start-${time}`}
                                        value={time}
                                      >
                                        {time}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                                <label className="text-xs text-slate-500">
                                  휴식 종료
                                  <select
                                    value={row.breakEnd}
                                    onChange={(event) => {
                                      const nextEnd = event.target.value;
                                      updateManualRow(weekday, {
                                        breakEnd: nextEnd,
                                        breakStart:
                                          nextEnd <= row.breakStart
                                            ? previousHour(nextEnd)
                                            : row.breakStart,
                                      });
                                    }}
                                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 outline-none"
                                  >
                                    {TIME_OPTIONS.slice(1).map((time) => (
                                      <option
                                        key={`${WORKDAY_NAMES[weekday]}-break-end-${time}`}
                                        value={time}
                                      >
                                        {time}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={previewManualDraft}
                    disabled={loadingAssistant}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 disabled:opacity-40"
                  >
                    수정안 미리보기
                  </button>
                  <button
                    onClick={applyManualDraftDirectly}
                    disabled={loadingAssistant}
                    className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-40"
                  >
                    바로 적용
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* ── 날짜별 설정 ── */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-[0_18px_45px_-35px_rgba(16,185,129,0.55)] transition-shadow hover:shadow-[0_24px_50px_-32px_rgba(16,185,129,0.7)]">
            <button
              onClick={() => setDateEditorOpen((prev) => !prev)}
              className="group flex w-full items-center justify-between gap-4 rounded-2xl text-left"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-emerald-800">
                  날짜별 개별 설정
                </p>
                <p className="mt-1 text-xs leading-5 text-emerald-700">
                  {Object.keys(dateDraft).length
                    ? `${Object.keys(dateDraft).length}개 날짜 설정 중`
                    : "달력에서 날짜를 클릭하여 개별 휴무/시간 설정"}
                </p>
                <p className="mt-2 text-[11px] font-medium text-emerald-500">
                  기존 요일 스케줄을 유지하면서 특정 날짜만 변경합니다.
                </p>
              </div>
              <div className="inline-flex shrink-0 items-center gap-2 rounded-full border border-emerald-200 bg-white px-3 py-2 text-xs font-semibold text-emerald-700 shadow-sm transition-all group-hover:border-emerald-300 group-hover:bg-white/95">
                <span>{dateEditorOpen ? "접기" : "펼쳐보기"}</span>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${dateEditorOpen ? "rotate-180" : "rotate-0"}`}
                />
              </div>
            </button>

            {dateEditorOpen && (
              <div className="mt-4 space-y-4">
                <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3">
                  <p className="text-xs leading-5 text-slate-500">
                    달력에서 날짜를 클릭 → 휴무/예약가능 설정 → 바로 적용
                  </p>
                  <button
                    onClick={() => {
                      setDateDraft(buildDateDraftFromSlots(visibleSlots, assistantMonth));
                    }}
                    className="shrink-0 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300"
                  >
                    현재값 불러오기
                  </button>
                </div>

                {/* 미니 캘린더 */}
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="mb-3 grid grid-cols-7 gap-1 text-center text-[10px] font-medium text-slate-400">
                    {WEEKDAY_NAMES.map((d) => (
                      <div key={`dh-${d}`}>{d}</div>
                    ))}
                  </div>
                  <div className="grid grid-cols-7 gap-1">
                    {(() => {
                      const [y, m] = assistantMonth.split("-").map(Number);
                      const miniCells = getMonthDays(y, m - 1);
                      return miniCells.map((day, idx) => {
                        if (!day)
                          return (
                            <div
                              key={`de-blank-${idx}`}
                              className="h-9 rounded-lg bg-slate-50"
                            />
                          );
                        const dk = fmt(y, m - 1, day);
                        const dr = dateDraft[dk];
                        const existingSlots = slotsByDate[dk] || [];
                        const existingHoliday = isFullHoliday(existingSlots);
                        const existingAvail = existingSlots.some(
                          (s) => slotStatus(s) === "available" || slotStatus(s) === "booked",
                        );
                        let bg = "bg-white border-slate-200 text-slate-700 hover:border-slate-400";
                        if (dr?.mode === "off")
                          bg = "bg-amber-100 border-amber-400 text-amber-800";
                        else if (dr?.mode === "available")
                          bg = "bg-primary-100 border-primary-400 text-primary-800";
                        else if (existingHoliday)
                          bg = "bg-amber-50 border-amber-200 text-amber-600";
                        else if (existingAvail)
                          bg = "bg-emerald-50 border-emerald-200 text-emerald-700";

                        return (
                          <button
                            key={dk}
                            onClick={() => {
                              if (editingDate === dk) {
                                setEditingDate(null);
                              } else {
                                setEditingDate(dk);
                                if (!dateDraft[dk]) {
                                  const existing = slotsByDate[dk] || [];
                                  if (isFullHoliday(existing)) {
                                    updateDateRow(dk, { mode: "off" });
                                  } else if (
                                    existing.some(
                                      (s) =>
                                        slotStatus(s) === "available" ||
                                        slotStatus(s) === "booked",
                                    )
                                  ) {
                                    const hours = existing
                                      .filter((s) =>
                                        ["available", "booked"].includes(slotStatus(s)),
                                      )
                                      .map((s) => Number(s.start_time.slice(0, 2)));
                                    const sorted = [...new Set(hours)].sort(
                                      (a, b) => a - b,
                                    );
                                    updateDateRow(dk, {
                                      mode: "available",
                                      startTime: `${String(sorted[0]).padStart(2, "0")}:00`,
                                      endTime: `${String(sorted[sorted.length - 1] + 1).padStart(2, "0")}:00`,
                                    });
                                  }
                                }
                              }
                            }}
                            className={`h-9 rounded-lg border text-xs font-medium transition-colors ${bg} ${editingDate === dk ? "ring-2 ring-emerald-500 ring-offset-1" : ""}`}
                          >
                            {day}
                          </button>
                        );
                      });
                    })()}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-slate-400">
                    <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-100 border border-amber-400" /> 편집: 휴무</span>
                    <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-primary-100 border border-primary-400" /> 편집: 가능</span>
                    <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-50 border border-amber-200" /> 기존 휴무</span>
                    <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-50 border border-emerald-200" /> 기존 가능</span>
                  </div>
                </div>

                {/* 선택된 날짜 설정 패널 */}
                {editingDate && (
                  <div className="rounded-2xl border border-emerald-300 bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-700">
                        📅 {editingDate} 설정
                      </p>
                      <button
                        onClick={() => removeDateRow(editingDate)}
                        className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:border-red-300"
                      >
                        설정 해제
                      </button>
                    </div>
                    <div className="mt-3 flex gap-2">
                      {[
                        { mode: "none", label: "설정 없음", cls: "bg-slate-900 text-white", off: "bg-slate-100 text-slate-600" },
                        { mode: "available", label: "예약 가능", cls: "bg-primary-500 text-white", off: "bg-slate-100 text-slate-600" },
                        { mode: "off", label: "전체 휴무", cls: "bg-amber-500 text-white", off: "bg-slate-100 text-slate-600" },
                      ].map((opt) => (
                        <button
                          key={`${editingDate}-${opt.mode}`}
                          onClick={() => updateDateRow(editingDate, { mode: opt.mode })}
                          className={`rounded-full px-3 py-1.5 text-xs font-medium ${(dateDraft[editingDate]?.mode || "none") === opt.mode ? opt.cls : opt.off}`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>

                    {dateDraft[editingDate]?.mode === "available" && (
                      <div className="mt-4 space-y-3">
                        <div className="grid gap-3 sm:grid-cols-2">
                          <label className="text-xs text-slate-500">
                            시작 시간
                            <select
                              value={dateDraft[editingDate]?.startTime || "09:00"}
                              onChange={(e) =>
                                updateDateRow(editingDate, {
                                  startTime: e.target.value,
                                  endTime:
                                    (dateDraft[editingDate]?.endTime || "16:00") <= e.target.value
                                      ? nextHour(e.target.value)
                                      : dateDraft[editingDate]?.endTime || "16:00",
                                })
                              }
                              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none"
                            >
                              {TIME_OPTIONS.slice(0, -1).map((t) => (
                                <option key={`${editingDate}-ds-${t}`} value={t}>
                                  {t}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="text-xs text-slate-500">
                            종료 시간
                            <select
                              value={dateDraft[editingDate]?.endTime || "16:00"}
                              onChange={(e) =>
                                updateDateRow(editingDate, {
                                  endTime: e.target.value,
                                  startTime:
                                    e.target.value <= (dateDraft[editingDate]?.startTime || "09:00")
                                      ? previousHour(e.target.value)
                                      : dateDraft[editingDate]?.startTime || "09:00",
                                })
                              }
                              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none"
                            >
                              {TIME_OPTIONS.slice(1).map((t) => (
                                <option key={`${editingDate}-de-${t}`} value={t}>
                                  {t}
                                </option>
                              ))}
                            </select>
                          </label>
                        </div>
                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-xs font-medium text-slate-600">
                              휴식 시간
                            </p>
                            <button
                              onClick={() =>
                                updateDateRow(editingDate, {
                                  breakEnabled: !dateDraft[editingDate]?.breakEnabled,
                                })
                              }
                              className={`rounded-full px-3 py-1.5 text-xs font-medium ${dateDraft[editingDate]?.breakEnabled ? "bg-amber-500 text-white" : "border border-slate-200 bg-white text-slate-600"}`}
                            >
                              {dateDraft[editingDate]?.breakEnabled ? "사용 중" : "없음"}
                            </button>
                          </div>
                          {dateDraft[editingDate]?.breakEnabled && (
                            <div className="mt-3 grid gap-3 sm:grid-cols-2">
                              <label className="text-xs text-slate-500">
                                휴식 시작
                                <select
                                  value={dateDraft[editingDate]?.breakStart || "12:00"}
                                  onChange={(e) =>
                                    updateDateRow(editingDate, {
                                      breakStart: e.target.value,
                                      breakEnd:
                                        (dateDraft[editingDate]?.breakEnd || "13:00") <= e.target.value
                                          ? nextHour(e.target.value)
                                          : dateDraft[editingDate]?.breakEnd || "13:00",
                                    })
                                  }
                                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none"
                                >
                                  {TIME_OPTIONS.slice(0, -1).map((t) => (
                                    <option key={`${editingDate}-dbs-${t}`} value={t}>
                                      {t}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="text-xs text-slate-500">
                                휴식 종료
                                <select
                                  value={dateDraft[editingDate]?.breakEnd || "13:00"}
                                  onChange={(e) =>
                                    updateDateRow(editingDate, {
                                      breakEnd: e.target.value,
                                      breakStart:
                                        e.target.value <= (dateDraft[editingDate]?.breakStart || "12:00")
                                          ? previousHour(e.target.value)
                                          : dateDraft[editingDate]?.breakStart || "12:00",
                                    })
                                  }
                                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none"
                                >
                                  {TIME_OPTIONS.slice(1).map((t) => (
                                    <option key={`${editingDate}-dbe-${t}`} value={t}>
                                      {t}
                                    </option>
                                  ))}
                                </select>
                              </label>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 설정된 날짜 목록 */}
                {Object.keys(dateDraft).length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-500">
                      설정된 날짜 ({Object.keys(dateDraft).length}건)
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(dateDraft)
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([dk, row]) => (
                          <button
                            key={`tag-${dk}`}
                            onClick={() => setEditingDate(dk)}
                            className={`rounded-full px-3 py-1.5 text-[11px] font-medium ${row.mode === "off" ? "bg-amber-100 text-amber-700" : row.mode === "available" ? "bg-primary-100 text-primary-700" : "bg-slate-100 text-slate-500"}`}
                          >
                            {dk.slice(5)}{" "}
                            {row.mode === "off"
                              ? "휴무"
                              : row.mode === "available"
                                ? `${row.startTime}-${row.endTime}`
                                : "미설정"}
                          </button>
                        ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={applyDateDraft}
                  disabled={loadingAssistant || !Object.keys(dateDraft).length}
                  className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-40"
                >
                  날짜별 설정 적용 (기존 스케줄 유지)
                </button>
              </div>
            )}
          </div>
        </section>
      </div>

      <section
        ref={detailSectionRef}
        className="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Calendar size={16} className="text-primary-500" />
          {selectedDate || "날짜를 선택하세요"}
        </div>

        {selectedDate ? (
          selectedBookedSlots.length ? (
            <div className="space-y-3">
              {selectedBookedSlots.map((slot) => (
                <div
                  key={slot.id}
                  className="rounded-2xl border border-slate-200 bg-white p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2 text-sm text-slate-600">
                      <p className="flex items-center gap-2 font-semibold text-slate-800">
                        <Clock size={14} className="text-slate-400" />
                        {slot.start_time} - {slot.end_time}
                      </p>
                      <p className="flex items-center gap-2">
                        <User size={14} className="text-slate-400" />
                        {maskName(slot.booked_by_name)}
                      </p>
                      <p className="flex items-center gap-2">
                        <Phone size={14} className="text-slate-400" />
                        {slot.booking_phone || "번호 미입력"}
                      </p>
                    </div>
                    <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
                      예약 완료
                    </span>
                  </div>

                  <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                    <p className="text-xs font-medium text-slate-500">
                      요청 내용
                    </p>
                    <p className="mt-1 break-words">
                      {slot.booking_summary ||
                        slot.booking_description ||
                        "내용 없음"}
                    </p>
                  </div>

                  <BriefingPanel slot={slot} />
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-400">
              선택한 날짜에 예약된 학생이 없습니다.
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
