import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Calendar,
  Clock,
  User,
  FileText,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Plus,
  Trash2,
  X,
} from "lucide-react";

const WEEKDAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];

function getMonthDays(year, month) {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const startDay = first.getDay();
  const totalDays = last.getDate();
  const cells = [];
  for (let i = 0; i < startDay; i++) cells.push(null);
  for (let d = 1; d <= totalDays; d++) cells.push(d);
  return cells;
}

function fmt(y, m, d) {
  return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function BriefingPanel({ booking }) {
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!booking?.id) return;
    setLoading(true);
    fetch(`/api/ta/briefing/${booking.id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setBriefing(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [booking]);

  if (loading)
    return (
      <div className="flex items-center justify-center py-6">
        <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  if (!briefing)
    return (
      <p className="text-sm text-slate-400 py-4">브리핑 리포트가 없습니다.</p>
    );

  return (
    <div className="space-y-2 mt-3">
      <h4 className="text-xs font-semibold text-primary-600">
        AI 브리핑 리포트
      </h4>
      {[
        { label: "수강생", value: briefing.student_name },
        { label: "검색 이력", value: briefing.search_history || "이력 없음" },
        { label: "핵심 필요 내용", value: briefing.core_need },
      ].map(({ label, value }) => (
        <div
          key={label}
          className="p-2 bg-slate-50 rounded-lg border border-slate-100"
        >
          <p className="text-[10px] text-slate-400 mb-0.5">{label}</p>
          <p className="text-xs text-slate-700">{value}</p>
        </div>
      ))}
      <div className="p-2 bg-primary-50 rounded-lg border border-primary-200">
        <p className="text-[10px] text-primary-600 mb-0.5">AI 추천 지도 방향</p>
        <p className="text-xs text-slate-700">{briefing.ai_recommendation}</p>
      </div>
    </div>
  );
}

export default function TADashboard() {
  const { user } = useAuth();
  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [showRecurring, setShowRecurring] = useState(false);

  // Calendar navigation
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  // Recurring form
  const [recurWeekdays, setRecurWeekdays] = useState([]);
  const [recurStart, setRecurStart] = useState("14:00");
  const [recurEnd, setRecurEnd] = useState("15:00");
  const [recurWeeks, setRecurWeeks] = useState(4);
  const [recurSaving, setRecurSaving] = useState(false);

  const todayStr = fmt(today.getFullYear(), today.getMonth(), today.getDate());
  const tomorrowD = new Date(today);
  tomorrowD.setDate(tomorrowD.getDate() + 1);
  const tomorrowStr = fmt(
    tomorrowD.getFullYear(),
    tomorrowD.getMonth(),
    tomorrowD.getDate(),
  );

  const fetchSlots = useCallback(async () => {
    try {
      const res = await fetch("/api/ta/slots");
      if (res.ok) setSlots(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  // Group slots by date
  const slotsByDate = {};
  slots.forEach((s) => {
    if (!slotsByDate[s.date]) slotsByDate[s.date] = [];
    slotsByDate[s.date].push(s);
  });

  const cells = getMonthDays(viewYear, viewMonth);
  const selectedDateSlots = selectedDate ? slotsByDate[selectedDate] || [] : [];
  const todaySlots = slotsByDate[todayStr] || [];
  const tomorrowSlots = slotsByDate[tomorrowStr] || [];
  const todayBooked = todaySlots.filter((s) => s.status === "booked");
  const tomorrowBooked = tomorrowSlots.filter((s) => s.status === "booked");

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewYear(viewYear - 1);
      setViewMonth(11);
    } else setViewMonth(viewMonth - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewYear(viewYear + 1);
      setViewMonth(0);
    } else setViewMonth(viewMonth + 1);
  };

  const toggleWeekday = (d) => {
    setRecurWeekdays((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d],
    );
  };

  const saveRecurring = async () => {
    if (!recurWeekdays.length) return;
    setRecurSaving(true);
    try {
      await fetch("/api/ta/slots/recurring", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ta_id: user.id,
          ta_name: user.name,
          weekdays: recurWeekdays,
          start_time: recurStart,
          end_time: recurEnd,
          weeks: recurWeeks,
        }),
      });
      fetchSlots();
      setShowRecurring(false);
    } catch {
    } finally {
      setRecurSaving(false);
    }
  };

  const deleteSlot = async (slotId) => {
    await fetch(`/api/ta/slots/${slotId}`, { method: "DELETE" });
    setSlots((prev) => prev.filter((s) => s.id !== slotId));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">TA 스케줄</h1>
          <p className="text-sm text-slate-500">{user.name} 조교</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowRecurring(!showRecurring)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            <Plus size={14} /> 반복 슬롯
          </button>
          <button
            onClick={fetchSlots}
            className="p-2 text-slate-400 hover:text-primary-600 transition-colors"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Today & Tomorrow Quick View */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs font-medium text-slate-500 mb-1">
            오늘 ({todayStr})
          </p>
          <p className="text-2xl font-bold text-slate-800">
            {todayBooked.length}
            <span className="text-sm font-normal text-slate-400 ml-1">
              / {todaySlots.length} 슬롯
            </span>
          </p>
          {todayBooked.length > 0 && (
            <div className="mt-2 space-y-1">
              {todayBooked.map((s, i) => (
                <p key={i} className="text-xs text-slate-600">
                  <span className="font-mono text-primary-600">
                    {s.start_time}
                  </span>{" "}
                  {s.student_name || "수강생"}
                </p>
              ))}
            </div>
          )}
        </div>
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs font-medium text-slate-500 mb-1">
            내일 ({tomorrowStr})
          </p>
          <p className="text-2xl font-bold text-slate-800">
            {tomorrowBooked.length}
            <span className="text-sm font-normal text-slate-400 ml-1">
              / {tomorrowSlots.length} 슬롯
            </span>
          </p>
          {tomorrowBooked.length > 0 && (
            <div className="mt-2 space-y-1">
              {tomorrowBooked.map((s, i) => (
                <p key={i} className="text-xs text-slate-600">
                  <span className="font-mono text-primary-600">
                    {s.start_time}
                  </span>{" "}
                  {s.student_name || "수강생"}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recurring Slot Form */}
      {showRecurring && (
        <div className="bg-white rounded-xl p-5 border border-primary-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-700">
              반복 슬롯 설정
            </h2>
            <button
              onClick={() => setShowRecurring(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X size={16} />
            </button>
          </div>
          <div className="space-y-4">
            {/* Weekday Picker */}
            <div>
              <p className="text-xs text-slate-500 mb-2">요일 선택</p>
              <div className="flex gap-1.5">
                {WEEKDAY_NAMES.map((name, idx) => (
                  <button
                    key={idx}
                    onClick={() => toggleWeekday(idx)}
                    className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${recurWeekdays.includes(idx) ? "bg-primary-500 text-white" : "bg-slate-100 text-slate-600 hover:bg-primary-50"}`}
                  >
                    {name}
                  </button>
                ))}
              </div>
            </div>
            {/* Time */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-slate-500 mb-1">시작 시간</p>
                <input
                  type="time"
                  value={recurStart}
                  onChange={(e) => setRecurStart(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-primary-400"
                />
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">종료 시간</p>
                <input
                  type="time"
                  value={recurEnd}
                  onChange={(e) => setRecurEnd(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-primary-400"
                />
              </div>
            </div>
            {/* Weeks */}
            <div>
              <p className="text-xs text-slate-500 mb-1">반복 주 수</p>
              <select
                value={recurWeeks}
                onChange={(e) => setRecurWeeks(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-primary-400"
              >
                {[1, 2, 3, 4, 6, 8].map((w) => (
                  <option key={w} value={w}>
                    {w}주
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={saveRecurring}
              disabled={!recurWeekdays.length || recurSaving}
              className="w-full py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
            >
              {recurSaving
                ? "저장 중..."
                : `${recurWeekdays.length}개 요일 × ${recurWeeks}주 슬롯 생성`}
            </button>
          </div>
        </div>
      )}

      {/* Calendar + Detail Side Panel */}
      <div className="grid lg:grid-cols-5 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-slate-200 p-4">
          {/* Month Navigation */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={prevMonth}
              className="p-2 text-slate-400 hover:text-primary-600"
            >
              <ChevronLeft size={20} />
            </button>
            <h2 className="text-lg font-bold text-slate-800">
              {viewYear}년 {viewMonth + 1}월
            </h2>
            <button
              onClick={nextMonth}
              className="p-2 text-slate-400 hover:text-primary-600"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          {/* Weekday Headers */}
          <div className="grid grid-cols-7 mb-1">
            {WEEKDAY_NAMES.map((n) => (
              <div
                key={n}
                className="text-center text-xs font-medium text-slate-400 py-1"
              >
                {n}
              </div>
            ))}
          </div>

          {/* Day Cells */}
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, i) => {
              if (!day) return <div key={i} />;
              const dateStr = fmt(viewYear, viewMonth, day);
              const daySlots = slotsByDate[dateStr] || [];
              const bookedCount = daySlots.filter(
                (s) => s.status === "booked",
              ).length;
              const availCount = daySlots.length - bookedCount;
              const isToday = dateStr === todayStr;
              const isSelected = dateStr === selectedDate;

              return (
                <button
                  key={i}
                  onClick={() => {
                    setSelectedDate(dateStr);
                    setSelectedBooking(null);
                  }}
                  className={`relative p-1.5 rounded-lg text-center transition-colors min-h-[56px] ${
                    isSelected
                      ? "bg-primary-50 border-2 border-primary-400"
                      : isToday
                        ? "bg-primary-50/50 border border-primary-200"
                        : "hover:bg-slate-50 border border-transparent"
                  }`}
                >
                  <span
                    className={`text-sm ${isToday ? "font-bold text-primary-600" : "text-slate-700"}`}
                  >
                    {day}
                  </span>
                  {daySlots.length > 0 && (
                    <div className="flex justify-center gap-0.5 mt-0.5">
                      {bookedCount > 0 && (
                        <span className="w-1.5 h-1.5 rounded-full bg-primary-500" />
                      )}
                      {availCount > 0 && (
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="w-2 h-2 rounded-full bg-primary-500" />
              예약됨
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              가능
            </div>
          </div>
        </div>

        {/* Day Detail Panel */}
        <div className="lg:col-span-2 space-y-3">
          {selectedDate ? (
            <>
              <h3 className="text-sm font-semibold text-slate-700">
                {selectedDate} 스케줄
              </h3>
              {selectedDateSlots.length === 0 ? (
                <div className="py-8 text-center bg-white rounded-xl border border-slate-200">
                  <Calendar size={24} className="mx-auto mb-2 text-slate-300" />
                  <p className="text-sm text-slate-400">
                    등록된 슬롯이 없습니다
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {selectedDateSlots.map((slot) => {
                    const booked = slot.status === "booked";
                    return (
                      <div
                        key={slot.id}
                        onClick={() =>
                          booked &&
                          setSelectedBooking(
                            selectedBooking?.id === slot.id ? null : slot,
                          )
                        }
                        className={`p-3 rounded-lg border transition-colors ${
                          booked
                            ? selectedBooking?.id === slot.id
                              ? "bg-primary-50 border-primary-300 cursor-pointer"
                              : "bg-white border-primary-200 cursor-pointer hover:bg-primary-50/50"
                            : "bg-white border-slate-200"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Clock size={14} className="text-slate-400" />
                            <span className="text-sm font-mono text-slate-700">
                              {slot.start_time} ~ {slot.end_time}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {booked ? (
                              <span className="px-2 py-0.5 text-[10px] bg-primary-50 text-primary-700 border border-primary-200 rounded-full">
                                예약됨
                              </span>
                            ) : (
                              <>
                                <span className="px-2 py-0.5 text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
                                  가능
                                </span>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deleteSlot(slot.id);
                                  }}
                                  className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                                >
                                  <Trash2 size={12} />
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        {booked && (
                          <div className="mt-2">
                            <p className="text-sm text-slate-700 flex items-center gap-1.5">
                              <User size={12} className="text-slate-400" />
                              {slot.student_name || "수강생"}
                            </p>
                            {slot.topic && (
                              <p className="text-xs text-slate-400 mt-0.5 ml-5">
                                {slot.topic}
                              </p>
                            )}
                          </div>
                        )}
                        {selectedBooking?.id === slot.id && (
                          <BriefingPanel booking={slot} />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center bg-white rounded-xl border border-slate-200">
              <Calendar size={28} className="mx-auto mb-2 text-slate-300" />
              <p className="text-sm text-slate-400">
                달력에서 날짜를 선택하세요
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-lg p-3 text-center border border-slate-200">
          <p className="text-lg font-bold text-primary-600">{slots.length}</p>
          <p className="text-xs text-slate-500">전체 슬롯</p>
        </div>
        <div className="bg-white rounded-lg p-3 text-center border border-slate-200">
          <p className="text-lg font-bold text-emerald-600">
            {slots.filter((s) => s.status === "booked").length}
          </p>
          <p className="text-xs text-slate-500">예약됨</p>
        </div>
        <div className="bg-white rounded-lg p-3 text-center border border-slate-200">
          <p className="text-lg font-bold text-slate-500">
            {slots.filter((s) => s.status !== "booked").length}
          </p>
          <p className="text-xs text-slate-500">가능</p>
        </div>
      </div>
    </div>
  );
}
