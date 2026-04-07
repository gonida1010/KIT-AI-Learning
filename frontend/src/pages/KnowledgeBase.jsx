import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Upload, Trash2, RefreshCw, FileText, Loader2 } from "lucide-react";

const DOC_TYPES = ["커리큘럼", "규정", "공모전", "자소서", "취업", "기타"];

export default function KnowledgeBase() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [docType, setDocType] = useState("기타");

  const loadDocs = () => {
    fetch("/api/knowledge/documents")
      .then((r) => r.json())
      .then(setDocs)
      .catch(() => {});
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type", docType);
    try {
      await fetch("/api/knowledge/upload", { method: "POST", body: formData });
      loadDocs();
    } catch {
      // ignore
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await fetch(`/api/knowledge/documents/${docId}`, { method: "DELETE" });
      loadDocs();
    } catch {
      // ignore
    }
  };

  const handleRebuild = async () => {
    setRebuilding(true);
    try {
      await fetch("/api/knowledge/rebuild", { method: "POST" });
    } catch {
      // ignore
    } finally {
      setRebuilding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">📚 지식 베이스 관리</h2>
        <p className="text-sm text-gray-400 mt-1">
          학원 규정, 공모전 정보, 자소서 가이드 등 자료를 업로드하면 AI가
          자동으로 학습합니다.
        </p>
      </div>

      {/* Upload area */}
      <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1">
              문서 유형
            </label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-indigo-300"
            >
              {DOC_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 px-4 py-2 bg-indigo-500 text-white text-sm font-semibold rounded-lg hover:bg-indigo-600 cursor-pointer transition-colors">
            {uploading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Upload size={14} />
            )}
            {uploading ? "업로드 중..." : "파일 업로드"}
            <input
              type="file"
              className="hidden"
              onChange={handleUpload}
              disabled={uploading}
              accept=".pdf,.txt,.md,.docx"
            />
          </label>

          <button
            onClick={handleRebuild}
            disabled={rebuilding}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-sm text-gray-500 rounded-lg hover:border-indigo-300 hover:text-indigo-500 transition-colors disabled:opacity-40"
          >
            <RefreshCw size={14} className={rebuilding ? "animate-spin" : ""} />
            인덱스 재구축
          </button>
        </div>
      </div>

      {/* Document list */}
      <div>
        <h3 className="text-sm font-bold text-gray-700 mb-3">
          등록된 문서 ({docs.length}건)
        </h3>

        {docs.length === 0 ? (
          <div className="bg-white border border-gray-100 rounded-xl p-12 text-center">
            <FileText size={32} className="text-gray-200 mx-auto mb-3" />
            <p className="text-sm text-gray-400">등록된 문서가 없습니다.</p>
            <p className="text-xs text-gray-300 mt-1">
              PDF 파일을 업로드해 보세요.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map((doc, i) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center justify-between bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <FileText size={16} className="text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      {doc.filename}
                    </p>
                    <p className="text-[10px] text-gray-400">
                      {doc.doc_type} ·{" "}
                      {doc.chunk_count > 0
                        ? `${doc.chunk_count}개 청크`
                        : "비PDF"}{" "}
                      · {new Date(doc.uploaded_at).toLocaleDateString("ko-KR")}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-2 text-gray-300 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
