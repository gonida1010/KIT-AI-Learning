import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Users,
  ChevronRight,
  Link2,
  Copy,
  Check,
  Activity,
} from "lucide-react";

function StudentRow({ student, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${selected ? "bg-primary-50 border border-primary-200" : "bg-white hover:bg-slate-50 border border-slate-200"}`}
    >
      <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-sm font-bold text-primary-700">
        {student.name?.[0] || "?"}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-800 truncate">
          {student.name}
        </p>
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
  const [inviteCode, setInviteCode] = useState("");
  const [copied, setCopied] = useState(false);
  const token = localStorage.getItem("edu_sync_token");

  useEffect(() => {
    fetch(`/api/mentor/students/by-mentor/${user.id}`)
      .then((res) => (res.ok ? res.json() : []))
      .then(setStudents)
      .catch(() => {});
  }, [user.id]);

  const selectStudent = async (student) => {
    setSelectedStudent(student);
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">수강생 관리</h1>
        <p className="text-sm text-slate-500">
          담당 수강생 활동 흐름과 초대 링크를 관리합니다.
        </p>
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
              <Activity size={16} className="text-primary-500" /> 활동 타임라인
            </div>
            {!selectedStudent ? (
              <div className="h-52 flex items-center justify-center text-sm text-slate-400">
                왼쪽에서 수강생을 선택하세요.
              </div>
            ) : timeline.length === 0 ? (
              <div className="h-52 flex items-center justify-center text-sm text-slate-400">
                최근 활동이 없습니다.
              </div>
            ) : (
              <div className="space-y-3 max-h-[420px] overflow-y-auto">
                {timeline
                  .slice()
                  .reverse()
                  .map((event, index) => (
                    <div
                      key={`${event.timestamp}-${index}`}
                      className="flex gap-3"
                    >
                      <div className="flex flex-col items-center">
                        <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5" />
                        {index < timeline.length - 1 && (
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
            )}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-slate-700">
              <Link2 size={16} className="text-primary-500" /> 수강생 초대 링크
            </div>
            {!inviteCode ? (
              <button
                onClick={generateInvite}
                className="px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm transition-colors"
              >
                초대 링크 생성
              </button>
            ) : (
              <div className="space-y-3">
                <div className="px-4 py-3 bg-slate-50 rounded-lg border border-slate-200 text-primary-700 font-mono text-lg">
                  {inviteCode}
                </div>
                <button
                  onClick={copyInviteLink}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm transition-colors"
                >
                  {copied ? (
                    <>
                      <Check size={16} className="text-emerald-500" /> 복사됨
                    </>
                  ) : (
                    <>
                      <Copy size={16} /> 초대 링크 복사
                    </>
                  )}
                </button>
                <p className="text-xs text-slate-400 break-all">
                  {window.location.origin}/?invite={inviteCode}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
