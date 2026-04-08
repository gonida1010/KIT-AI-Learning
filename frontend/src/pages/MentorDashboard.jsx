import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Users,
  AlertTriangle,
  Copy,
  Check,
  ChevronRight,
  FileText,
  TrendingUp,
  Link2,
  RefreshCw,
  Newspaper,
  Upload,
  Search,
  Trash2,
  AlertCircle,
} from "lucide-react";

/* ─── Sub Components ─── */
function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}
        >
          <Icon size={20} />
        </div>
        <div>
          <p className="text-2xl font-bold text-slate-800">{value}</p>
          <p className="text-xs text-slate-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

function HandoffCard({ item, onResolve }) {
  return (
    <div className="p-4 bg-white rounded-lg border border-amber-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-800">
            {item.student_name || "수강생"}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {item.created_at?.slice(0, 16) || ""}
          </p>
          <p className="text-sm text-slate-600 mt-2">{item.message}</p>
          {item.reason && (
            <p className="text-xs text-amber-600 mt-1">
              분류 사유: {item.reason}
            </p>
          )}
        </div>
        <button
          onClick={() => onResolve(item.id)}
          className="shrink-0 px-3 py-1.5 text-xs bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg transition-colors"
        >
          해결
        </button>
      </div>
    </div>
  );
}

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
          {student.career_pref || "미설정"}
        </p>
      </div>
      <ChevronRight size={16} className="text-slate-400" />
    </button>
  );
}

function TimelineView({ events }) {
  if (!events?.length)
    return <p className="text-sm text-slate-400">활동 이력이 없습니다.</p>;
  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {events
        .slice()
        .reverse()
        .map((ev, i) => (
          <div key={i} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5" />
              {i < events.length - 1 && (
                <div className="w-px flex-1 bg-slate-200" />
              )}
            </div>
            <div className="pb-3">
              <p className="text-xs text-slate-400">
                {ev.timestamp?.slice(0, 16)}
              </p>
              <p className="text-sm text-slate-700">{ev.content}</p>
              {ev.detail && (
                <p className="text-xs text-slate-400">{ev.detail}</p>
              )}
            </div>
          </div>
        ))}
    </div>
  );
}

/* ─── Main Component ─── */
export default function MentorDashboard() {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [curationToday, setCurationToday] = useState([]);
  const [inviteCode, setInviteCode] = useState("");
  const [copied, setCopied] = useState(false);
  // File upload state
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const token = localStorage.getItem("edu_sync_token");

  const fetchData = useCallback(async () => {
    const [qRes, sRes, cRes, dRes] = await Promise.all([
      fetch(`/api/mentor/queue?token=${token}`).catch(() => null),
      fetch(`/api/mentor/students/by-mentor/${user.id}`).catch(() => null),
      fetch("/api/curation/today").catch(() => null),
      fetch("/api/knowledge/documents").catch(() => null),
    ]);
    if (qRes?.ok) setQueue(await qRes.json());
    if (sRes?.ok) setStudents(await sRes.json());
    if (cRes?.ok) setCurationToday(await cRes.json());
    if (dRes?.ok) setDocs(await dRes.json());
  }, [token, user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const selectStudent = async (s) => {
    setSelectedStudent(s);
    try {
      const r = await fetch(`/api/mentor/student/${s.id}/timeline`);
      if (r.ok) setTimeline(await r.json());
    } catch {}
  };

  const handleResolve = async (id) => {
    await fetch(`/api/mentor/queue/${id}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    setQueue((prev) => prev.filter((q) => q.id !== id));
  };

  const generateInvite = async () => {
    const res = await fetch(`/api/mentor/invite?token=${token}`, {
      method: "POST",
    });
    if (res.ok) {
      const data = await res.json();
      setInviteCode(data.invite_code);
    }
  };

  const copyInviteLink = () => {
    const link = `${window.location.origin}/?invite=${inviteCode}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".pdf")) {
      setUploadError("PDF 파일만 업로드 가능합니다.");
      return;
    }
    setUploading(true);
    setUploadError("");
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch("/api/knowledge/upload", {
        method: "POST",
        body: fd,
      });
      if (res.ok) {
        const dRes = await fetch("/api/knowledge/documents");
        if (dRes.ok) setDocs(await dRes.json());
      } else {
        const d = await res.json().catch(() => ({}));
        setUploadError(d.detail || "업로드 실패");
      }
    } catch {
      setUploadError("네트워크 오류");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDeleteDoc = async (docId) => {
    await fetch(`/api/knowledge/documents/${docId}`, { method: "DELETE" });
    setDocs((prev) => prev.filter((d) => d.id !== docId));
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">멘토 대시보드</h1>
          <p className="text-sm text-slate-500">안녕하세요, {user.name}님</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2 text-slate-400 hover:text-primary-600 transition-colors"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={Users}
          label="수강생"
          value={students.length}
          color="bg-primary-50 text-primary-600"
        />
        <StatCard
          icon={AlertTriangle}
          label="상담 대기"
          value={queue.length}
          color="bg-amber-50 text-amber-600"
        />
        <StatCard
          icon={Newspaper}
          label="오늘 큐레이션"
          value={curationToday.length}
          color="bg-emerald-50 text-emerald-600"
        />
        <StatCard
          icon={TrendingUp}
          label="이번 주 상담"
          value={queue.length}
          color="bg-purple-50 text-purple-600"
        />
      </div>

      {/* 2-Column: Handoff Queue + Today's Curation */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Handoff Queue */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-500" /> 상담 대기 큐
          </h2>
          {queue.length === 0 ? (
            <div className="p-4 bg-white rounded-lg border border-slate-200 text-sm text-slate-400">
              대기 중인 상담이 없습니다
            </div>
          ) : (
            <div className="space-y-2">
              {queue.map((q) => (
                <HandoffCard key={q.id} item={q} onResolve={handleResolve} />
              ))}
            </div>
          )}
        </div>

        {/* Today's Curation */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Newspaper size={16} className="text-primary-500" /> 오늘의 큐레이션
          </h2>
          {!curationToday?.length ? (
            <div className="p-4 bg-white rounded-lg border border-slate-200 text-sm text-slate-400">
              오늘의 큐레이션이 없습니다.
            </div>
          ) : (
            <div className="space-y-2">
              {curationToday.map((item, i) => (
                <div
                  key={i}
                  className="p-3 bg-white rounded-lg border border-slate-200"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Newspaper size={14} className="text-primary-500" />
                    <span className="text-xs text-primary-600">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-sm text-slate-800">{item.title}</p>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {item.summary}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Student List + Detail */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Users size={16} className="text-primary-500" /> 수강생 관리
        </h2>
        <div className="grid lg:grid-cols-5 gap-4">
          <div className="lg:col-span-2 space-y-2">
            {students.map((s) => (
              <StudentRow
                key={s.id}
                student={s}
                selected={selectedStudent?.id === s.id}
                onClick={() => selectStudent(s)}
              />
            ))}
            {students.length === 0 && (
              <p className="text-sm text-slate-400">
                등록된 수강생이 없습니다.
              </p>
            )}
          </div>
          <div className="lg:col-span-3">
            {selectedStudent ? (
              <div className="bg-white rounded-xl p-5 border border-slate-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-lg font-bold text-primary-700">
                    {selectedStudent.name?.[0]}
                  </div>
                  <div>
                    <p className="text-lg font-bold text-slate-800">
                      {selectedStudent.name}
                    </p>
                    <p className="text-sm text-slate-500">
                      희망 직무: {selectedStudent.career_pref || "미설정"}
                    </p>
                  </div>
                </div>
                <h3 className="text-sm font-medium text-slate-600 mb-3">
                  활동 타임라인
                </h3>
                <TimelineView events={timeline} />
              </div>
            ) : (
              <div className="flex items-center justify-center h-48 bg-white rounded-xl border border-slate-200">
                <p className="text-sm text-slate-400">수강생을 선택하세요</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2-Column: File Upload + Invite */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* File Upload Section */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <FileText size={16} className="text-primary-500" /> 지식 베이스 (PDF
            업로드)
          </h2>
          <div className="bg-white rounded-xl p-5 border border-slate-200 space-y-4">
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1.5 px-3 py-2 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors cursor-pointer">
                <Upload size={14} /> PDF 업로드
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleUpload}
                  className="hidden"
                />
              </label>
              {uploading && (
                <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full" />
              )}
            </div>
            {uploadError && (
              <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                <AlertCircle size={14} /> {uploadError}
              </div>
            )}
            {docs.length === 0 ? (
              <p className="text-sm text-slate-400">
                업로드된 문서가 없습니다.
              </p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {docs.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText size={16} className="text-red-500 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm text-slate-700 truncate">
                          {doc.filename}
                        </p>
                        <p className="text-xs text-slate-400">
                          {doc.chunks || 0}개 청크
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Invite Section */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Link2 size={16} className="text-primary-500" /> 수강생 초대
          </h2>
          <div className="bg-white rounded-xl p-5 border border-slate-200 text-center">
            <p className="text-sm text-slate-500 mb-4">
              고유 초대 코드를 생성하여 수강생에게 공유하세요.
            </p>
            {!inviteCode ? (
              <button
                onClick={generateInvite}
                className="px-6 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                초대 코드 생성
              </button>
            ) : (
              <div className="space-y-3">
                <div className="px-4 py-3 bg-slate-50 rounded-lg font-mono text-lg text-primary-700 border border-slate-200">
                  {inviteCode}
                </div>
                <button
                  onClick={copyInviteLink}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm transition-colors"
                >
                  {copied ? (
                    <>
                      <Check size={16} className="text-emerald-500" /> 복사됨!
                    </>
                  ) : (
                    <>
                      <Copy size={16} /> 초대 링크 복사
                    </>
                  )}
                </button>
                <p className="text-xs text-slate-400">
                  링크: {window.location.origin}/?invite={inviteCode}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
