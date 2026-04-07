import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CalendarDays, Clock, Loader2, CheckCircle2 } from "lucide-react";
import BriefingReport from "../components/BriefingReport";

export default function TADashboard() {
  const [slots, setSlots] = useState([]);
  const [briefings, setBriefings] = useState([]);
  const [bookingSlot, setBookingSlot] = useState(null);
  const [bookingDesc, setBookingDesc] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingDone, setBookingDone] = useState(null);

  const reload = () => {
    fetch("/api/ta/slots")
      .then((r) => r.json())
      .then(setSlots)
      .catch(() => {});
    fetch("/api/ta/briefings")
      .then((r) => r.json())
      .then(setBriefings)
      .catch(() => {});
  };

  useEffect(() => {
    reload();
  }, []);

  const handleBook = async () => {
    if (!bookingSlot || !bookingDesc.trim()) return;
    setBookingLoading(true);
    try {
      const res = await fetch("/api/ta/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: bookingSlot.id,
          student_id: "student_1",
          student_name: "김민수",
          description: bookingDesc,
        }),
      });
      const data = await res.json();
      setBookingDone(data.briefing);
      setBookingSlot(null);
      setBookingDesc("");
      reload();
    } catch {
      // ignore
    } finally {
      setBookingLoading(false);
    }
  };

  // 날짜별 그룹
  const slotsByDate = {};
  slots.forEach((s) => {
    if (!slotsByDate[s.date]) slotsByDate[s.date] = [];
    slotsByDate[s.date].push(s);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-800">
          📅 조교 스마트 스케줄링
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          빈 시간에 예약하고, 수강생의 요청을 AI가 브리핑 리포트로 정리해
          드립니다.
        </p>
      </div>

      {/* 예약 완료 알림 */}
      <AnimatePresence>
        {bookingDone && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-green-50 border border-green-200 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 size={18} className="text-green-500" />
              <span className="text-sm font-bold text-green-700">
                예약 완료! AI 브리핑 리포트가 생성되었습니다.
              </span>
              <button
                onClick={() => setBookingDone(null)}
                className="ml-auto text-xs text-green-400 hover:text-green-600"
              >
                닫기
              </button>
            </div>
            <BriefingReport report={bookingDone} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 스케줄 캘린더 */}
        <div>
          <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
            <CalendarDays size={16} className="text-indigo-500" />
            예약 가능 시간표
          </h3>

          {Object.entries(slotsByDate).map(([date, dateSlots]) => (
            <div key={date} className="mb-4">
              <p className="text-xs font-semibold text-gray-500 mb-2">
                📆{" "}
                {new Date(date).toLocaleDateString("ko-KR", {
                  month: "long",
                  day: "numeric",
                  weekday: "short",
                })}
              </p>
              <div className="space-y-2">
                {dateSlots.map((slot) => (
                  <motion.div
                    key={slot.id}
                    layout
                    className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all ${
                      slot.is_available
                        ? "bg-white border-gray-100 hover:border-indigo-200 hover:shadow-sm cursor-pointer"
                        : "bg-gray-50 border-gray-100 opacity-60"
                    } ${bookingSlot?.id === slot.id ? "ring-2 ring-indigo-300 border-indigo-300" : ""}`}
                    onClick={() => slot.is_available && setBookingSlot(slot)}
                  >
                    <div className="flex items-center gap-3">
                      <Clock
                        size={14}
                        className={
                          slot.is_available
                            ? "text-indigo-400"
                            : "text-gray-300"
                        }
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-700">
                          {slot.start_time} - {slot.end_time}
                        </p>
                        <p className="text-[10px] text-gray-400">
                          {slot.ta_name}
                        </p>
                      </div>
                    </div>
                    {slot.is_available ? (
                      <span className="text-[10px] px-2 py-0.5 bg-green-50 text-green-500 rounded-full font-bold">
                        예약 가능
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 bg-gray-100 text-gray-400 rounded-full">
                        {slot.booked_by_name || "예약됨"}
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 예약 폼 + 브리핑 목록 */}
        <div className="space-y-6">
          {/* 예약 폼 */}
          <AnimatePresence>
            {bookingSlot && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-white border border-indigo-100 rounded-xl p-5 shadow-sm"
              >
                <h4 className="text-sm font-bold text-gray-700 mb-1">
                  🎯 보충 수업 예약
                </h4>
                <p className="text-xs text-gray-400 mb-3">
                  {bookingSlot.date} · {bookingSlot.start_time}-
                  {bookingSlot.end_time} · {bookingSlot.ta_name}
                </p>

                <label className="text-xs text-gray-500 font-medium block mb-1">
                  어떤 부분이 어려운가요? (편하게 입력하세요)
                </label>
                <textarea
                  value={bookingDesc}
                  onChange={(e) => setBookingDesc(e.target.value)}
                  placeholder="예: 파이썬 클래스에서 self가 뭔지 모르겠어요, C언어 포인터 멘붕..."
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm resize-none h-24 focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-50"
                />

                <div className="flex gap-2 mt-3">
                  <button
                    onClick={handleBook}
                    disabled={bookingLoading || !bookingDesc.trim()}
                    className="flex-1 py-2.5 bg-indigo-500 text-white text-sm font-semibold rounded-lg hover:bg-indigo-600 disabled:opacity-40 transition-colors flex items-center justify-center gap-2"
                  >
                    {bookingLoading ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : null}
                    {bookingLoading ? "AI 브리핑 생성 중..." : "예약하기"}
                  </button>
                  <button
                    onClick={() => setBookingSlot(null)}
                    className="px-4 py-2.5 text-sm text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    취소
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 기존 브리핑 리포트 */}
          <div>
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              📋 조교 브리핑 리포트
            </h3>
            {briefings.length === 0 ? (
              <div className="bg-white border border-gray-100 rounded-xl p-8 text-center text-gray-300 text-sm">
                예약된 보충 수업이 없습니다
              </div>
            ) : (
              <div className="space-y-3">
                {briefings.map((slot) => (
                  <div
                    key={slot.id}
                    className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm"
                  >
                    <div className="flex items-center gap-2 mb-3 text-xs text-gray-400">
                      <CalendarDays size={12} />
                      {slot.date} {slot.start_time}-{slot.end_time} ·{" "}
                      {slot.ta_name}
                    </div>
                    <BriefingReport report={slot.briefing_report} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
