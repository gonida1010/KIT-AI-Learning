import { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";
import { MessageSquare, QrCode, Play } from "lucide-react";

function QRLogin({ onSuccess }) {
  const [qrUrl, setQrUrl] = useState(null);
  const [qrToken, setQrToken] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetch("/api/auth/qr/generate", { method: "POST" })
      .then((r) => r.json())
      .then((data) => {
        setQrUrl(data.qr_url);
        setQrToken(data.qr_token);
      })
      .catch(() => {});
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!qrToken) return;
    intervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/auth/qr/check?token=${qrToken}`);
        const data = await res.json();
        if (data.status === "approved" && data.token) {
          clearInterval(intervalRef.current);
          localStorage.setItem("edu_sync_token", data.token);
          onSuccess(data.user);
        }
      } catch {}
    }, 2000);
    return () => clearInterval(intervalRef.current);
  }, [qrToken, onSuccess]);

  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-sm text-slate-500">모바일에서 QR을 스캔하세요</p>
      {qrUrl ? (
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <img
            src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUrl)}`}
            alt="QR Code"
            className="w-48 h-48"
          />
        </div>
      ) : (
        <div className="w-48 h-48 bg-slate-100 rounded-xl animate-pulse" />
      )}
      <p className="text-xs text-slate-400">
        이미 모바일에서 로그인한 상태여야 합니다
      </p>
    </div>
  );
}

export default function LoginPage({ oauthCode }) {
  const { login, demoLogin } = useAuth();
  const [tab, setTab] = useState("kakao");
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (!oauthCode) return;
    setProcessing(true);
    const invite = localStorage.getItem("edu_sync_invite");
    login(oauthCode, invite)
      .then(() => {
        window.history.replaceState({}, "", "/");
        localStorage.removeItem("edu_sync_invite");
      })
      .catch((e) => {
        setError(e.message);
        setProcessing(false);
      });
  }, [oauthCode, login]);

  const handleKakaoLogin = () => {
    fetch("/api/auth/kakao/login-url")
      .then((r) => r.json())
      .then((d) => {
        window.location.href = d.login_url;
      })
      .catch(() => setError("카카오 로그인 URL을 가져올 수 없습니다."));
  };

  const handleQRSuccess = () => window.location.reload();

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

  const invite = localStorage.getItem("edu_sync_invite");

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

        {invite && (
          <div className="mb-4 px-4 py-3 bg-primary-50 border border-primary-200 rounded-lg text-center">
            <p className="text-sm text-primary-700">
              초대 코드: <span className="font-mono font-bold">{invite}</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              로그인 후 자동으로 멘토에 연결됩니다
            </p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1 mb-6">
          {[
            { key: "kakao", label: "카카오", Icon: MessageSquare },
            { key: "qr", label: "QR 로그인", Icon: QrCode },
            { key: "demo", label: "데모", Icon: Play },
          ].map(({ key, label, Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-sm rounded-md transition-colors ${
                tab === key
                  ? "bg-primary-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
          {error && (
            <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {error}
            </div>
          )}

          {processing && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin h-8 w-8 border-2 border-primary-500 border-t-transparent rounded-full" />
            </div>
          )}

          {!processing && tab === "kakao" && (
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm text-slate-500 text-center">
                카카오 계정으로 빠르게 시작하세요
              </p>
              <button
                onClick={handleKakaoLogin}
                className="w-full py-3 bg-[#FEE500] text-[#191919] font-bold rounded-lg hover:bg-[#FDD800] transition-colors flex items-center justify-center gap-2"
              >
                <svg width="18" height="18" viewBox="0 0 18 18">
                  <path
                    fill="#191919"
                    d="M9 1C4.58 1 1 3.79 1 7.21c0 2.17 1.45 4.08 3.64 5.18l-.93 3.42c-.08.3.26.54.52.37L8.14 13.6c.28.03.57.04.86.04 4.42 0 8-2.79 8-6.23S13.42 1 9 1"
                  />
                </svg>
                카카오 로그인
              </button>
            </div>
          )}

          {!processing && tab === "qr" && (
            <QRLogin onSuccess={handleQRSuccess} />
          )}

          {!processing && tab === "demo" && (
            <div className="space-y-3">
              <p className="text-sm text-slate-500 text-center mb-4">
                체험용 데모 계정으로 로그인
              </p>
              {[
                {
                  role: "student",
                  emoji: "🎓",
                  label: "수강생",
                  desc: "AI 챗봇 체험",
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

        <p className="text-center text-xs text-slate-400 mt-4">
          KDT AI Learning Platform &copy; 2026
        </p>
      </div>
    </div>
  );
}
