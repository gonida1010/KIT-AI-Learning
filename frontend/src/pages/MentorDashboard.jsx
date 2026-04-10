import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Bell,
  BookOpen,
  Calendar,
  ExternalLink,
  RefreshCw,
  Upload,
} from "lucide-react";

function UploadDropZone({ onFileSelect, uploading }) {
  const [dragging, setDragging] = useState(false);

  return (
    <label
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        const file = event.dataTransfer.files?.[0];
        if (file) onFileSelect(file);
      }}
      className={`flex min-h-[148px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-5 py-6 text-center transition-colors ${dragging ? "border-primary-400 bg-primary-50" : "border-slate-300 bg-slate-50"}`}
    >
      <Upload size={18} className="text-primary-500" />
      <p className="mt-3 text-sm font-semibold text-slate-700">
        대시보드에서 바로 자료 첨부
      </p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        올린 자료는 벡터 저장소에 들어가고, 챗봇이 요청한 학생에게 관련 자료로
        송부합니다.
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

function ActivityItem({ item }) {
  const ts = item.timestamp?.replace("T", " ")?.slice(0, 16) || "시간 없음";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="break-words text-sm font-semibold leading-6 text-slate-800">
        {item.question || "질문 기록 없음"} - {item.student_name}
      </p>
      <p className="mt-1 text-xs text-slate-400">{ts}</p>
      <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2">
        <p className="text-[11px] font-medium text-slate-500">송부 자료</p>
        {item.sent_materials?.length ? (
          <div className="mt-2 flex flex-wrap gap-2">
            {item.sent_materials.map((material, index) => (
              <span
                key={`${material}-${index}`}
                className="rounded-full border border-primary-200 bg-primary-50 px-2 py-1 text-[11px] leading-4 text-primary-700"
              >
                {material}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-xs text-slate-400">
            아직 송부된 자료가 없습니다.
          </p>
        )}
      </div>
    </div>
  );
}

function CurationItem({ item }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-primary-600">
        <Calendar size={12} />
        <span>{item.category}</span>
        <span className="text-slate-400">{item.date}</span>
      </div>
      <p className="break-words text-sm font-semibold leading-6 text-slate-800">
        {item.title}
      </p>
      <p className="mt-1 break-words text-xs leading-5 text-slate-500">
        {item.summary}
      </p>
      {item.attachment_url && (
        <a
          href={item.attachment_url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700"
        >
          첨부 열기 <ExternalLink size={12} />
        </a>
      )}
    </div>
  );
}

function RecentDocItem({ doc }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="break-words text-sm font-semibold leading-6 text-slate-800">
            {doc.digest_title || doc.filename}
          </p>
          <p className="mt-1 break-words text-xs leading-5 text-slate-500">
            {doc.digest_summary || "AI 정리 요약이 없습니다."}
          </p>
        </div>
        <a
          href={doc.attachment_url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-lg border border-slate-200 p-2 text-slate-500 transition-colors hover:border-primary-300 hover:text-primary-600"
        >
          <ExternalLink size={14} />
        </a>
      </div>
      <p className="mt-3 text-[11px] text-slate-400">
        {doc.uploaded_at?.slice(0, 10) || "날짜 없음"}
      </p>
    </div>
  );
}

export default function MentorDashboard() {
  const { user } = useAuth();
  const [todayCurations, setTodayCurations] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [taBookings, setTaBookings] = useState([]);
  const [recentDocs, setRecentDocs] = useState([]);
  const [recentBasicDocs, setRecentBasicDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [basicUploading, setBasicUploading] = useState(false);
  const [error, setError] = useState("");
  const token = localStorage.getItem("edu_sync_token");

  const fetchData = useCallback(async () => {
    const dashboardRes = await fetch(
      `/api/mentor/dashboard?token=${encodeURIComponent(token || "")}`,
    ).catch(() => null);

    if (dashboardRes?.ok) {
      const data = await dashboardRes.json();
      setTodayCurations(data.today_curations || []);
      setRecentActivity(data.recent_activity || []);
      setTaBookings(data.ta_bookings || []);
      setRecentDocs(data.recent_docs || []);
      setRecentBasicDocs(data.recent_basic_docs || []);
    }
  }, [token]);

  useEffect(() => {
    if (user?.role === "mentor") fetchData();
  }, [fetchData, user?.role]);

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
      await fetchData();
    } catch (uploadError) {
      setError(uploadError.message || "업로드에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const uploadBasicFile = async (file) => {
    if (!file) return;
    setBasicUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("token", token || "");
    formData.append("file", file);

    try {
      const res = await fetch("/api/mentor/basic/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "업로드에 실패했습니다.");
      }
      await fetchData();
    } catch (uploadError) {
      setError(uploadError.message || "업로드에 실패했습니다.");
    } finally {
      setBasicUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={fetchData}
          className="rounded-lg border border-slate-200 bg-white p-2 text-slate-400 transition-colors hover:border-primary-300 hover:text-primary-600"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="space-y-4">
          {taBookings.length > 0 && (
            <div className="rounded-2xl border border-primary-200 bg-primary-50 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-primary-700">
                <Bell size={16} className="text-primary-500" />
                예약 알림
              </div>
              <div className="space-y-2">
                {taBookings.map((b) => (
                  <div
                    key={b.slot_id}
                    className="rounded-xl border border-primary-200 bg-white p-3"
                  >
                    <p className="text-sm font-medium text-slate-800">
                      {b.student_name} → 조교 {b.ta_name}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {b.date} {b.start_time} - {b.end_time}
                    </p>
                    {(b.booking_summary || b.booking_description) && (
                      <p className="mt-1 text-xs text-slate-400">
                        {b.booking_summary || b.booking_description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <BookOpen size={16} className="text-primary-500" />
              최근 질문 기록
            </div>
            <div className="max-h-[720px] space-y-3 overflow-y-auto pr-1">
              {recentActivity.length ? (
                recentActivity.map((item, index) => (
                  <ActivityItem
                    key={`${item.student_id}-${item.timestamp}-${index}`}
                    item={item}
                  />
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
                  최근 질문 기록이 없습니다.
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Upload size={16} className="text-primary-500" />
              최신 자료 첨부
            </div>
            <UploadDropZone onFileSelect={uploadFile} uploading={uploading} />
          </div>

          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-blue-700">
              <Upload size={16} className="text-blue-500" />
              기초 자료 첨부
            </div>
            <UploadDropZone
              onFileSelect={uploadBasicFile}
              uploading={basicUploading}
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Calendar size={16} className="text-primary-500" />
              오늘 큐레이션
            </div>
            <div className="space-y-3">
              {todayCurations.length ? (
                todayCurations.map((item) => (
                  <CurationItem key={item.id || item.title} item={item} />
                ))
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-400">
                  관리자가 오늘 날짜로 등록한 큐레이션이 없습니다.
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <BookOpen size={16} className="text-primary-500" />내 최신 자료
              5개
            </div>
            <div className="space-y-3">
              {recentDocs.length ? (
                recentDocs.map((doc) => (
                  <RecentDocItem key={doc.id} doc={doc} />
                ))
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-400">
                  아직 업로드한 최신 자료가 없습니다.
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-700">
              <BookOpen size={16} className="text-blue-500" />내 기초 자료 5개
            </div>
            <div className="space-y-3">
              {recentBasicDocs.length ? (
                recentBasicDocs.map((doc) => (
                  <RecentDocItem key={doc.id} doc={doc} />
                ))
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-400">
                  아직 업로드한 기초 자료가 없습니다.
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
