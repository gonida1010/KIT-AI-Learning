import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Users,
  ChevronRight,
  Link2,
  Copy,
  Check,
  Activity,
  Calendar,
} from "lucide-react";

function StudentRow({ student, selected, onClick }) {
  const hasHandoff = student.has_handoff;
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${selected ? "bg-primary-50 border border-primary-200" : hasHandoff ? "bg-amber-50 border border-amber-200 hover:bg-amber-100" : "bg-white hover:bg-slate-50 border border-slate-200"}`}
    >
      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${hasHandoff ? "bg-amber-200 text-amber-800" : "bg-primary-100 text-primary-700"}`}>
        {student.name?.[0] || "?"}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-slate-800 truncate">
            {student.name}
          </p>
          {hasHandoff && (
            <span className="shrink-0 rounded-full bg-amber-100 border border-amber-300 px-2 py-0.5 text-[10px] font-medium text-amber-700">
              1:1 요청
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400">
          {student.career_pref || "희망 직무 미설정"}
        </p>
      </div>
      <ChevronRight size={16} className="text-slate-400" />
    </button>
  );
}

export default function MentorStudents() {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [visibleTimelineCount, setVisibleTimelineCount] = useState(5);
  const [taBookings, setTaBookings] = useState([]);
  const [inviteCode, setInviteCode] = useState("");
  const [copied, setCopied] = useState(false);
  const token = localStorage.getItem("edu_sync_token");

  useEffect(() => {
    fetch(`/api/mentor/students/by-mentor/${user.id}`)
      .then((res) => (res.ok ? res.json() : []))
      .then(setStudents)
      .catch(() => {});

    fetch(`/api/mentor/dashboard?token=${encodeURIComponent(token || "")}`)
      .then((res) => (res.ok ? res.json() : {}))
      .then((data) => setTaBookings(data.ta_bookings || []))
      .catch(() => {});
  }, [token, user.id]);

  const visibleBookings = selectedStudent
    ? taBookings.filter((item) => item.student_id === selectedStudent.id)
    : taBookings;

  const selectStudent = async (student) => {
    setSelectedStudent(student);
    setVisibleTimelineCount(5);
    try {
      const res = await fetch(`/api/mentor/student/${student.id}/timeline`);
      const data = await res.json();
      setTimeline(data.events || []);
    } catch {
      setTimeline([]);
    }
  };

  const generateInvite = async () => {
    const res = await fetch(`/api/mentor/invite?token=${token}`, {
      method: "POST",
    });
    if (!res.ok) return;
    const data = await res.json();
    setInviteCode(data.invite_code);
  };

  const copyInviteLink = async () => {
    const link = `${window.location.origin}/?invite=${inviteCode}`;
    await navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const inviteLink = inviteCode
    ? `${window.location.origin}/?invite=${inviteCode}`
    : "";

  const limitedTimeline = timeline
    .filter((event) => {
      if (!event.timestamp) return true;
      const eventTime = new Date(event.timestamp);
      const monthAgo = new Date();
      monthAgo.setDate(monthAgo.getDate() - 30);
      return !Number.isNaN(eventTime.getTime()) && eventTime >= monthAgo;
    })
    .slice()
    .reverse();

  const visibleTimeline = limitedTimeline.slice(0, visibleTimelineCount);
  const canLoadMoreTimeline = visibleTimeline.length < limitedTimeline.length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">수강생 관리</h1>
          <p className="text-sm text-slate-500">
            담당 수강생 활동 흐름과 초대 링크를 관리합니다.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-3 py-3 shadow-sm lg:min-w-[420px] lg:max-w-[520px]">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Link2 size={14} className="text-primary-500" /> 수강생 초대 링크
          </div>
          {!inviteCode ? (
            <button
              onClick={generateInvite}
              className="mt-2 rounded-lg bg-primary-500 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-primary-600"
            >
              초대 링크 생성
            </button>
          ) : (
            <div className="mt-2 flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-3">
              <div className="rounded-lg bg-slate-50 px-3 py-2 font-mono text-xs text-primary-700 lg:shrink-0">
                {inviteCode}
              </div>
              <div className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] leading-4 text-slate-400 lg:truncate">
                {inviteLink}
              </div>
              <div className="flex gap-2 lg:shrink-0">
                <button
                  onClick={copyInviteLink}
                  className="inline-flex items-center justify-center gap-1 rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-200"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-emerald-500" /> 복사됨
                    </>
                  ) : (
                    <>
                      <Copy size={14} /> 링크 복사
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2 space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <Users size={16} className="text-primary-500" /> 담당 수강생
          </div>
          {students.map((student) => (
            <StudentRow
              key={student.id}
              student={student}
              selected={selectedStudent?.id === student.id}
              onClick={() => selectStudent(student)}
            />
          ))}
          {students.length === 0 && (
            <div className="p-4 bg-white rounded-lg border border-slate-200 text-sm text-slate-400">
              연결된 수강생이 없습니다.
            </div>
          )}
        </div>

        <div className="lg:col-span-3 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-slate-700">
              <Calendar size={16} className="text-primary-500" /> 조교 연결 현황
            </div>
            {!selectedStudent ? (
              visibleBookings.length ? (
                <div className="space-y-3">
                  {visibleBookings.map((item) => (
                    <div
                      key={item.slot_id}
                      className="rounded-lg border border-slate-200 bg-slate-50 p-4"
                    >
                      <p className="text-sm font-semibold text-slate-800">
                        조교:{item.ta_name} - {item.student_name}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        {item.date} {item.start_time} - {item.end_time}
                      </p>
                      <p className="mt-2 text-xs text-slate-500">
                        연락처: {item.booking_phone || "미입력"}
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        {item.booking_summary ||
                          item.booking_description ||
                          "요청 내용 없음"}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-32 flex items-center justify-center text-sm text-slate-400">
                  연결된 조교 예약이 없습니다.
                </div>
              )
            ) : visibleBookings.length ? (
              <div className="space-y-3">
                {visibleBookings.map((item) => (
                  <div
                    key={item.slot_id}
                    className="rounded-lg border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-sm font-semibold text-slate-800">
                      조교:{item.ta_name} - {item.student_name}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {item.date} {item.start_time} - {item.end_time}
                    </p>
                    <p className="mt-2 text-xs text-slate-500">
                      연락처: {item.booking_phone || "미입력"}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      {item.booking_summary ||
                        item.booking_description ||
                        "요청 내용 없음"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-sm text-slate-400">
                선택한 수강생의 조교 연결 이력이 없습니다.
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-slate-700">
              <Activity size={16} className="text-primary-500" /> 활동 타임라인
            </div>
            {!selectedStudent ? (
              <div className="h-52 flex items-center justify-center text-sm text-slate-400">
                왼쪽에서 수강생을 선택하세요.
              </div>
            ) : limitedTimeline.length === 0 ? (
              <div className="h-52 flex items-center justify-center text-sm text-slate-400">
                최근 한 달 활동이 없습니다.
              </div>
            ) : (
              <div>
                <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                  {visibleTimeline.map((event, index) => (
                    <div
                      key={`${event.timestamp}-${index}`}
                      className="flex gap-3"
                    >
                      <div className="flex flex-col items-center">
                        <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5" />
                        {index < visibleTimeline.length - 1 && (
                          <div className="w-px flex-1 bg-slate-200" />
                        )}
                      </div>
                      <div className="pb-3">
                        <p className="text-xs text-slate-400">
                          {event.timestamp?.slice(0, 16)}
                        </p>
                        <p className="text-sm text-slate-800">
                          {event.content}
                        </p>
                        {event.detail && (
                          <p className="text-xs text-slate-500 mt-0.5">
                            {event.detail}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {canLoadMoreTimeline && (
                  <button
                    onClick={() =>
                      setVisibleTimelineCount((prev) =>
                        Math.min(prev + 5, limitedTimeline.length),
                      )
                    }
                    className="mt-4 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:border-primary-300 hover:text-primary-700"
                  >
                    더보기
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
