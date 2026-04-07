import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  MessageSquare,
  TrendingUp,
  Users,
  Eye,
} from "lucide-react";
import QueueList from "../components/QueueList";
import StudentTimeline from "../components/StudentTimeline";

export default function MentorDashboard() {
  const [briefing, setBriefing] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [students, setStudents] = useState([]);

  useEffect(() => {
    fetch("/api/mentor/briefing")
      .then((r) => r.json())
      .then(setBriefing)
      .catch(() => {});
    fetch("/api/mentor/students")
      .then((r) => r.json())
      .then(setStudents)
      .catch(() => {});
  }, []);

  const handleViewStudent = async (studentId) => {
    setSelectedStudent(studentId);
    try {
      const res = await fetch(`/api/mentor/student/${studentId}/timeline`);
      const data = await res.json();
      setTimeline(data);
    } catch {
      setTimeline(null);
    }
  };

  const handleResolve = async (handoffId) => {
    try {
      await fetch(`/api/mentor/queue/${handoffId}/resolve`, { method: "POST" });
      // 새로고침
      const res = await fetch("/api/mentor/briefing");
      const data = await res.json();
      setBriefing(data);
    } catch {
      // ignore
    }
  };

  if (!briefing) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        브리핑 데이터를 불러오는 중...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-800">☀️ 출근 브리핑</h2>
        <p className="text-sm text-gray-400 mt-1">
          밤사이 AI 응대 내역과 멘토 직접 연결 대기열입니다.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "AI 총 대화",
            value: briefing.total_ai_conversations,
            icon: MessageSquare,
            color: "blue",
          },
          {
            label: "대기 중 상담",
            value: briefing.pending_handoffs,
            icon: AlertCircle,
            color: "orange",
          },
          {
            label: "해결 완료",
            value: briefing.resolved_last_24h,
            icon: CheckCircle2,
            color: "green",
          },
          {
            label: "등록 학생",
            value: students.length,
            icon: Users,
            color: "purple",
          },
        ].map(({ label, value, icon: Icon, color }) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className={`w-8 h-8 rounded-lg flex items-center justify-center bg-${color}-50`}
              >
                <Icon size={16} className={`text-${color}-500`} />
              </span>
              <span className="text-2xl font-extrabold text-gray-800">
                {value}
              </span>
            </div>
            <p className="text-xs text-gray-400">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* Top keywords */}
      {briefing.top_keywords.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-indigo-500" />
            <h3 className="text-sm font-bold text-gray-700">
              최근 인기 검색 키워드
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {briefing.top_keywords.map((kw) => (
              <span
                key={kw}
                className="px-3 py-1 bg-indigo-50 text-indigo-500 rounded-full text-xs font-medium"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Two columns: Queue + Timeline */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Queue */}
        <div>
          <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
            <Clock size={16} className="text-orange-500" />
            멘토 상담 대기열
          </h3>
          <QueueList
            queue={briefing.queue}
            onResolve={handleResolve}
            onViewStudent={handleViewStudent}
          />
        </div>

        {/* Student Timeline */}
        <div>
          <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
            <Eye size={16} className="text-purple-500" />
            원생별 히스토리
          </h3>

          {/* Student pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {students.map((s) => (
              <button
                key={s.id}
                onClick={() => handleViewStudent(s.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  selectedStudent === s.id
                    ? "bg-purple-500 text-white"
                    : "bg-gray-100 text-gray-500 hover:bg-purple-50 hover:text-purple-500"
                }`}
              >
                {s.name}
              </button>
            ))}
          </div>

          {timeline ? (
            <StudentTimeline data={timeline} />
          ) : (
            <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-300 text-sm">
              학생을 선택하면 타임라인이 표시됩니다
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
