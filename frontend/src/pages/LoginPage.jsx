import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
  const { login, demoLogin } = useAuth();
  const [error, setError] = useState("");
  const [kakaoUrl, setKakaoUrl] = useState("");
  const [processing, setProcessing] = useState(false);

  // 카카오 로그인 URL 가져오기
  useEffect(() => {
    fetch("/api/auth/kakao/login-url")
      .then((r) => r.json())
      .then((data) => setKakaoUrl(data.login_url || ""))
      .catch(() => {});
  }, []);

  // OAuth 콜백 처리 (URL에 code 파라미터가 있을 때)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && !processing) {
      setProcessing(true);
      // URL 정리
      window.history.replaceState({}, document.title, window.location.pathname);
      login(code).catch((err) => {
        setError(err.message || "로그인에 실패했습니다.");
        setProcessing(false);
      });
    }
  }, []);

  const handleKakaoLogin = () => {
    if (kakaoUrl) {
      window.location.href = kakaoUrl;
    } else {
      setError(
        "카카오 API 키가 설정되지 않았습니다. 데모 모드를 이용해 주세요.",
      );
    }
  };

  if (processing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
        <div className="text-center">
          <div className="w-10 h-10 border-3 border-indigo-200 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">카카오 로그인 처리 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight">
            <span className="text-indigo-500">Edu</span>-Sync
            <span className="text-xs ml-1 font-medium text-indigo-400 bg-indigo-50 px-1.5 py-0.5 rounded">
              AI
            </span>
          </h1>
          <p className="text-sm text-gray-400 mt-2">
            KDT 하이브리드 관리 플랫폼
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 space-y-4">
          <h2 className="text-lg font-bold text-gray-700 text-center">
            로그인
          </h2>

          {/* 카카오 로그인 */}
          <button
            onClick={handleKakaoLogin}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-colors"
            style={{ backgroundColor: "#FEE500", color: "#191919" }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M9 0.5C4.029 0.5 0 3.694 0 7.618c0 2.523 1.675 4.74 4.196 5.987-.186.69-.671 2.497-.768 2.884-.12.482.177.474.372.345.153-.101 2.434-1.654 3.417-2.326.254.037.513.056.783.056 4.971 0 9-3.194 9-7.118S13.971 0.5 9 0.5Z"
                fill="#191919"
              />
            </svg>
            카카오 로그인
          </button>

          {/* 구분선 */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-300">또는 데모 모드</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          {/* 데모 역할 선택 */}
          <div className="space-y-2">
            <p className="text-xs text-gray-400 text-center">
              카카오 API 키 없이 테스트할 수 있습니다
            </p>
            <div className="grid grid-cols-3 gap-2">
              {[
                {
                  role: "student",
                  label: "🎓 수강생",
                  color: "bg-blue-50 hover:bg-blue-100 text-blue-600",
                },
                {
                  role: "mentor",
                  label: "👨‍🏫 멘토",
                  color: "bg-green-50 hover:bg-green-100 text-green-600",
                },
                {
                  role: "ta",
                  label: "📋 조교",
                  color: "bg-purple-50 hover:bg-purple-100 text-purple-600",
                },
              ].map(({ role, label, color }) => (
                <button
                  key={role}
                  onClick={() => demoLogin(role)}
                  className={`py-2.5 rounded-xl text-xs font-semibold transition-colors ${color}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="text-xs text-red-500 bg-red-50 rounded-lg p-2.5 text-center">
              {error}
            </div>
          )}
        </div>

        <p className="text-center text-[10px] text-gray-300 mt-6">
          © 2026 KIT · Edu-Sync AI
        </p>
      </div>
    </div>
  );
}
