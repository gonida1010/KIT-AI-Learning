import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  ExternalLink,
  FileText,
  Link2,
  Search,
  Trash2,
  Upload,
} from "lucide-react";

function DropZone({ onFileSelect, uploading }) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <label
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`flex min-h-[180px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition-colors ${dragging ? "border-primary-400 bg-primary-50" : "border-slate-300 bg-slate-50"}`}
    >
      <Upload size={20} className="text-primary-500" />
      <p className="mt-3 text-sm font-semibold text-slate-700">
        파일을 여기로 드래그하거나 클릭해서 업로드
      </p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        PDF, 이미지 등 멘토 자료를 바로 올리면 AI가 정리 후 벡터 저장소에
        반영합니다.
      </p>
      {uploading && (
        <p className="mt-3 text-xs text-slate-400">AI 정리 중입니다...</p>
      )}
      <input
        type="file"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFileSelect(file);
          event.target.value = "";
        }}
      />
    </label>
  );
}

function DocCard({ doc, onDelete }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] leading-4 text-slate-400">
            <span>
              {doc.source_kind === "link"
                ? "링크"
                : doc.source_kind === "image"
                  ? "이미지"
                  : "파일"}
            </span>
            <span>{doc.uploaded_at?.slice(0, 10) || "날짜 없음"}</span>
            {doc.is_stale && (
              <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
                오래된 자료
              </span>
            )}
          </div>
          <p className="break-words text-sm font-semibold leading-6 text-slate-800">
            {doc.digest_title || doc.filename}
          </p>
          <p className="mt-1 break-words text-xs leading-5 text-slate-500">
            {doc.digest_summary || "AI 요약을 준비하지 못했습니다."}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <a
            href={doc.attachment_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-200 p-2 text-slate-500 transition-colors hover:border-primary-300 hover:text-primary-600"
          >
            <ExternalLink size={14} />
          </a>
          <button
            onClick={() => onDelete(doc.id)}
            className="rounded-lg border border-slate-200 p-2 text-slate-400 transition-colors hover:border-red-200 hover:text-red-500"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function KnowledgeBase() {
  const { user } = useAuth();
  const token = localStorage.getItem("edu_sync_token");
  const [docs, setDocs] = useState([]);
  const [search, setSearch] = useState("");
  const [sourceLink, setSourceLink] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const fetchDocs = useCallback(async () => {
    const res = await fetch(
      `/api/mentor/knowledge?token=${encodeURIComponent(token || "")}&scope=all&q=${encodeURIComponent(search)}`,
    ).catch(() => null);
    if (res?.ok) {
      setDocs(await res.json());
    }
  }, [search, token]);

  useEffect(() => {
    if (user?.role === "mentor") {
      fetchDocs();
    }
  }, [fetchDocs, user?.role]);

  const latestDocs = useMemo(() => docs.filter((doc) => !doc.is_stale), [docs]);
  const staleDocs = useMemo(() => docs.filter((doc) => doc.is_stale), [docs]);

  const uploadFile = async (file) => {
    if (!file) return;
    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("token", token || "");
    formData.append("file", file);

    try {
      const res = await fetch("/api/mentor/knowledge/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "업로드에 실패했습니다.");
      }
      await fetchDocs();
    } catch (uploadError) {
      setError(uploadError.message || "업로드에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const uploadLink = async () => {
    if (!sourceLink.trim()) return;
    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("token", token || "");
    formData.append("source_link", sourceLink.trim());

    try {
      const res = await fetch("/api/mentor/knowledge/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "링크 등록에 실패했습니다.");
      }
      setSourceLink("");
      await fetchDocs();
    } catch (uploadError) {
      setError(uploadError.message || "링크 등록에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    await fetch(
      `/api/mentor/knowledge/${docId}?token=${encodeURIComponent(token || "")}`,
      {
        method: "DELETE",
      },
    ).catch(() => null);
    await fetchDocs();
  };

  if (user?.role !== "mentor") {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Upload size={16} className="text-primary-500" />
            담당 수강생 전용 자료 올리기
          </div>
          <DropZone onFileSelect={uploadFile} uploading={uploading} />
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
              <Link2 size={14} />
              링크 등록
            </div>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                value={sourceLink}
                onChange={(event) => setSourceLink(event.target.value)}
                placeholder="https://example.com"
                className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition-colors focus:border-primary-300"
              />
              <button
                onClick={uploadLink}
                disabled={uploading || !sourceLink.trim()}
                className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                링크 등록
              </button>
            </div>
            {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="relative">
            <Search
              size={16}
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="최신 자료 검색"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-12 pr-4 text-sm text-slate-800 outline-none transition-colors focus:border-primary-300"
            />
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-50 p-5 text-center">
              <p className="text-2xl font-bold text-slate-800">
                {latestDocs.length}
              </p>
              <p className="mt-1 text-xs text-slate-500">최신 자료</p>
            </div>
            <div className="rounded-2xl bg-amber-50 p-5 text-center">
              <p className="text-2xl font-bold text-amber-700">
                {staleDocs.length}
              </p>
              <p className="mt-1 text-xs leading-5 text-amber-700">
                정리 필요한 오래된 자료
              </p>
            </div>
          </div>
        </div>
      </div>

      <section>
        <div className="mb-3 text-sm font-semibold text-slate-700">
          최신 올린 자료
        </div>
        <div className="space-y-3">
          {latestDocs.length ? (
            latestDocs.map((doc) => (
              <DocCard key={doc.id} doc={doc} onDelete={handleDelete} />
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
              최신 자료가 없습니다.
            </div>
          )}
        </div>
      </section>

      <section>
        <div className="mb-3 text-sm font-semibold text-slate-700">
          오래된 자료
        </div>
        <div className="space-y-3">
          {staleDocs.length ? (
            staleDocs.map((doc) => (
              <DocCard key={doc.id} doc={doc} onDelete={handleDelete} />
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
              삭제가 필요한 오래된 자료가 없습니다.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
