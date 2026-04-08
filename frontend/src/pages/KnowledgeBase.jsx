import { useState, useEffect, useCallback } from "react";
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Search,
  AlertCircle,
} from "lucide-react";

export default function KnowledgeBase() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch("/api/knowledge/documents");
      if (res.ok) setDocs(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".pdf")) {
      setError("PDF 파일만 업로드 가능합니다.");
      return;
    }

    setUploading(true);
    setError("");
    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch("/api/knowledge/upload", {
        method: "POST",
        body: fd,
      });
      if (res.ok) {
        fetchDocs();
      } else {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || "업로드 실패");
      }
    } catch {
      setError("네트워크 오류");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (docId) => {
    try {
      await fetch(`/api/knowledge/documents/${docId}`, { method: "DELETE" });
      fetchDocs();
    } catch {}
  };

  const handleRebuild = async () => {
    setUploading(true);
    try {
      await fetch("/api/knowledge/rebuild", { method: "POST" });
    } catch {
    } finally {
      setUploading(false);
    }
  };

  const filtered = docs.filter(
    (d) => !search || d.filename?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">지식 베이스</h1>
          <p className="text-sm text-slate-500">RAG 파이프라인 문서 관리</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRebuild}
            disabled={uploading}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg transition-colors disabled:opacity-40"
          >
            <RefreshCw size={14} className={uploading ? "animate-spin" : ""} />{" "}
            재빌드
          </button>
          <label className="flex items-center gap-1.5 px-3 py-2 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors cursor-pointer">
            <Upload size={14} /> 업로드
            <input
              type="file"
              accept=".pdf"
              onChange={handleUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="문서 검색..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-100"
        />
      </div>

      {/* Document List */}
      {filtered.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <FileText size={32} className="mx-auto mb-3 text-slate-300" />
          <p className="text-sm text-slate-500">
            {docs.length === 0
              ? "문서가 없습니다. PDF를 업로드하세요."
              : "검색 결과가 없습니다."}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 bg-white rounded-lg border border-slate-200 hover:border-primary-300 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center shrink-0">
                  <FileText size={18} className="text-red-500" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {doc.filename}
                  </p>
                  <p className="text-xs text-slate-400">
                    {doc.chunks || 0}개 청크 ·{" "}
                    {doc.uploaded_at?.slice(0, 10) || ""}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="p-2 text-slate-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Footer Info */}
      <div className="text-xs text-slate-400 text-center">
        총 {docs.length}개 문서 · FAISS 벡터 인덱스 기반 검색
      </div>
    </div>
  );
}
