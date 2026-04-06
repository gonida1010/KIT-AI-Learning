import { useState } from "react";
import { Compass } from "lucide-react";
import DropZone from "./components/DropZone";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `서버 오류 (${res.status})`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="w-full border-b border-indigo-100 bg-white/70 backdrop-blur-md">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600">
            <Compass size={22} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-800 tracking-tight">
              AI 커리큘럼 내비게이터
            </h1>
            <p className="text-xs text-gray-400">
              내가 배우는 코드, 지금 어디쯤일까?
            </p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-5xl px-6 py-10">
        {!result ? (
          <DropZone
            onFileUpload={handleFileUpload}
            loading={loading}
            error={error}
          />
        ) : (
          <Dashboard data={result} onReset={handleReset} />
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-xs text-gray-300">
        © 2026 KIT AI Learning · 학습의 지도를 밝혀주는 AI
      </footer>
    </div>
  );
}
