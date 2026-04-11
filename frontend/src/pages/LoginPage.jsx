import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { MessageSquare } from "lucide-react";

export default function LoginPage() {
  const { demoLogin } = useAuth();
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);

  const handleDemo = async (role) => {
    setProcessing(true);
    try {
      await demoLogin(role);
    } catch {
      setError("데모 로그인 실패");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-50 p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-2xl mb-4">
            <MessageSquare className="text-primary-600" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">Edu-Sync AI</h1>
          <p className="text-slate-500 text-sm mt-1">
            KDT 멀티 에이전트 멘토링 시스템
          </p>
        </div>

        {/* Demo Login */}
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
          {error && (
            <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {error}
            </div>
          )}

          {processing ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin h-8 w-8 border-2 border-primary-500 border-t-transparent rounded-full" />
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-slate-500 text-center mb-4">
                체험용 데모 계정으로 로그인
              </p>
              {[
                {
                  role: "student",
                  emoji: "🎓",
                  label: "수강생",
                  desc: "카카오톡 AI 챗봇",
                },
                {
                  role: "mentor",
                  emoji: "👨‍🏫",
                  label: "멘토",
                  desc: "대시보드 관리",
                },
                {
                  role: "ta",
                  emoji: "📋",
                  label: "TA (조교)",
                  desc: "스케줄 관리",
                },
                {
                  role: "admin",
                  emoji: "🛡️",
                  label: "관리자",
                  desc: "전체 시스템 관리",
                },
              ].map(({ role, emoji, label, desc }) => (
                <button
                  key={role}
                  onClick={() => handleDemo(role)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg bg-slate-50 hover:bg-primary-50 border border-slate-200 hover:border-primary-200 transition-colors text-left"
                >
                  <span className="text-2xl">{emoji}</span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {label}
                    </p>
                    <p className="text-xs text-slate-500">{desc}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Extensibility note */}
        <p className="text-center text-xs text-slate-400 mt-4">
          카카오 로그인 · QR 로그인 확장 가능
        </p>
        <p className="text-center text-xs text-slate-400 mt-1">
          KDT AI Learning Platform &copy; 2026
        </p>
      </div>
    </div>
  );
}
