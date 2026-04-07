import { useState } from "react";
import DropZone from "../components/DropZone";
import Dashboard from "../components/Dashboard";

export default function CurriMap() {
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
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800">
          🧭 CurriMap AI — 진척도 나침반
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          코드 파일이나 스크린샷을 올리면 커리큘럼 상의 현재 위치를
          알려드립니다.
        </p>
      </div>

      {!result ? (
        <DropZone
          onFileUpload={handleFileUpload}
          loading={loading}
          error={error}
        />
      ) : (
        <Dashboard data={result} onReset={handleReset} />
      )}
    </div>
  );
}
