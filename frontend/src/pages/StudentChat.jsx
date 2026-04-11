import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Send,
  Bot,
  User,
  AlertTriangle,
  Newspaper,
  LogOut,
  UserCircle,
  FileText,
  ExternalLink,
  Download,
  Calendar,
  Clock,
  BookOpen,
  Handshake,
  Search,
  Menu,
  ChevronLeft,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const KAKAO_PROFILE = "🏫";
const KAKAO_BOT_NAME = "코리아IT-AI챗봇";

const AGENT_BADGES = {
  agent_a: {
    label: "행정·커리어",
    color: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  },
  agent_b: {
    label: "학습·조교",
    color: "bg-blue-50 text-blue-700 border border-blue-200",
  },
  human_handoff: {
    label: "멘토 연결",
    color: "bg-amber-50 text-amber-700 border border-amber-200",
  },
};

function CurationCard({ item }) {
  return (
    <div className="mt-2 p-3 bg-[#f7f7f7] border border-[#e5e5e5] rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <Newspaper size={14} className="text-[#555]" />
        <span className="text-xs text-[#888] font-medium">
          {item.category} · {item.date}
        </span>
      </div>
      <p className="text-[13px] text-[#333] font-medium">{item.title}</p>
      {item.summary && (
        <p className="text-xs text-[#777] mt-1">{item.summary}</p>
      )}
      {item.attachment_url && (
        <a
          href={item.attachment_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-2 text-xs text-[#4A90D9] hover:text-[#3570B0] font-medium"
        >
          <ExternalLink size={12} /> 원문 보기
        </a>
      )}
    </div>
  );
}

function MentorDocCard({ doc }) {
  const isLink = doc.source_kind === "link";
  return (
    <div className="mt-2 p-3 bg-[#f7f7f7] border border-[#e5e5e5] rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <FileText size={14} className="text-[#555]" />
        <span className="text-xs text-[#888] font-medium">멘토 자료</span>
      </div>
      <p className="text-[13px] text-[#333] font-medium">
        {doc.title || doc.digest_title}
      </p>
      {(doc.summary || doc.digest_summary) && (
        <p className="text-xs text-[#777] mt-1">
          {doc.summary || doc.digest_summary}
        </p>
      )}
      {doc.attachment_url && (
        <div className="flex items-center gap-3 mt-2">
          <a
            href={doc.attachment_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-[#4A90D9] hover:text-[#3570B0] font-medium"
          >
            <ExternalLink size={12} /> {isLink ? "링크 열기" : "원문 보기"}
          </a>
          {!isLink && (
            <a
              href={doc.attachment_url}
              download
              className="inline-flex items-center gap-1 text-xs text-[#4A90D9] hover:text-[#3570B0] font-medium"
            >
              <Download size={12} /> 다운로드
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function ChoiceButtons({ choices, onSelect }) {
  if (!choices?.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {choices.map((c, i) => (
        <button
          key={i}
          onClick={() => onSelect(c.label || c.description || c, c)}
          className="px-3.5 py-2 text-[13px] bg-white text-[#3b1e1e] border border-[#ddd] rounded-full shadow-sm hover:bg-[#f5f0e8] transition-colors"
        >
          {c.label || c}
        </button>
      ))}
    </div>
  );
}

function WelcomeActions({ onAction, disabled }) {
  const actions = [
    {
      key: "curation",
      label: "📰 오늘의 큐레이션",
      desc: "학원 공지 · 뉴스 · 채용",
    },
    {
      key: "ta",
      label: "📅 조교 연결",
      desc: "보충수업 예약 · 학습 질문",
    },
    {
      key: "tips",
      label: "📚 학습 팁",
      desc: "담당 멘토 최신 자료",
    },
    {
      key: "mentor",
      label: "🙋‍♂️ 멘토 연결",
      desc: "1:1 상담 요청",
    },
  ];
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {actions.map((a) => (
        <button
          key={a.key}
          onClick={() => onAction(a.key)}
          disabled={disabled}
          className="px-3.5 py-2 text-[13px] bg-white text-[#3b1e1e] border border-[#ddd] rounded-full shadow-sm hover:bg-[#f5f0e8] transition-colors disabled:opacity-40"
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

function KakaoTime() {
  const now = new Date();
  const h = now.getHours();
  const m = String(now.getMinutes()).padStart(2, "0");
  const ampm = h < 12 ? "오전" : "오후";
  const h12 = h % 12 || 12;
  return (
    <span className="text-[10px] text-[#999] whitespace-nowrap">
      {ampm} {h12}:{m}
    </span>
  );
}

function ChatMessage({ msg, onSelect, onQuickAction, sending }) {
  const isUser = msg.role === "user";

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end items-end gap-1.5 mb-2"
      >
        <KakaoTime />
        <div className="max-w-[70%] px-3 py-2 rounded-xl text-[13.5px] leading-[1.55] whitespace-pre-wrap bg-[#FEE500] text-[#3b1e1e] rounded-tr-[4px] shadow-sm">
          {msg.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start gap-2 mb-2"
    >
      {/* 프로필 */}
      <div className="shrink-0 w-10 h-10 rounded-xl bg-[#4A90D9] flex items-center justify-center text-white text-lg shadow-sm overflow-hidden">
        <span className="leading-none font-bold text-[11px]">IT<br/>KOREA</span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-medium text-[#333] mb-1">{KAKAO_BOT_NAME}</p>
        <div className="flex items-end gap-1.5">
          <div className="max-w-[85%]">
            <div className="px-3 py-2.5 rounded-xl text-[13.5px] leading-[1.55] whitespace-pre-wrap bg-white text-[#333] rounded-tl-[4px] shadow-sm">
              {msg.content}
            </div>
            {msg.curation_items?.map((item, i) => (
              <CurationCard key={i} item={item} />
            ))}
            {msg.mentor_docs?.map((doc, i) => (
              <MentorDocCard key={`md-${i}`} doc={doc} />
            ))}
            {(() => {
              const shownIds = new Set(msg.mentor_docs?.map((d) => d.id) || []);
              const unique = (msg.related_materials || []).filter(
                (d) => !shownIds.has(d.id),
              );
              const seen = new Set();
              return unique
                .filter((d) => {
                  if (seen.has(d.id)) return false;
                  seen.add(d.id);
                  return true;
                })
                .map((doc, i) => <MentorDocCard key={`rm-${i}`} doc={doc} />);
            })()}
            <ChoiceButtons choices={msg.choices} onSelect={onSelect} />
            {msg.isWelcome && (
              <WelcomeActions onAction={onQuickAction} disabled={sending} />
            )}
            {msg.agent_type === "human_handoff" && (
              <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-600">
                <AlertTriangle size={12} />
                멘토에게 상담이 접수되었습니다
              </div>
            )}
          </div>
          <KakaoTime />
        </div>
      </div>
    </motion.div>
  );
}

export default function StudentChat() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [handoffSending, setHandoffSending] = useState(false);
  const [bookingPhase, setBookingPhase] = useState(null); // null | "dates" | "slots" | "description"
  const [pendingSlot, setPendingSlot] = useState(null); // { slotId, label }
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content: `안녕하세요 ${user?.name || ""}님!\n아래 메뉴를 선택하거나, 궁금한 점을 바로 입력해 주세요.`,
        agent_type: null,
        isWelcome: true,
      },
    ]);
  }, [user]);

  /* ── 퀵 액션: 오늘의 큐레이션 ── */
  const fetchTodayCuration = async () => {
    if (sending) return;
    setSending(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: "오늘의 큐레이션" },
    ]);
    try {
      const res = await fetch("/api/curation/today");
      const data = await res.json();
      const items = data.items || [];
      if (items.length === 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `오늘(${data.date}) 등록된 큐레이션이 아직 없습니다.\n관리자가 콘텐츠를 준비 중이에요!`,
            agent_type: "agent_a",
          },
        ]);
      } else {
        const category = data.category || "공지";
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `오늘의 큐레이션 [${category}]\n총 ${items.length}건의 콘텐츠가 있습니다.`,
            agent_type: "agent_a",
            curation_items: items,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "큐레이션 정보를 불러오지 못했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  /* ── 퀵 액션: 학습 팁 (선택지 표시) ── */
  const fetchLearningTips = async () => {
    if (sending) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: "학습 팁" },
      {
        role: "assistant",
        content: "어떤 자료를 보고 싶으신가요?",
        agent_type: "agent_a",
        choices: [
          {
            label: "최신 자료",
            description: "멘토님이 최근 올린 자료",
            _action: "tips_type",
            _type: "latest",
          },
          {
            label: "기초 자료",
            description: "기본 학습 자료",
            _action: "tips_type",
            _type: "basic",
          },
        ],
      },
    ]);
  };

  const fetchTipsByType = async (type) => {
    if (sending) return;
    setSending(true);
    const label = type === "basic" ? "기초 자료" : "최신 자료";
    setMessages((prev) => [...prev, { role: "user", content: label }]);
    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch("/api/chat/tips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: user?.id, token, type }),
      });
      const data = await res.json();
      const docs = data.mentor_docs || [];
      const typeLabel = type === "basic" ? "기초" : "최신";
      const text =
        data.mentor_name && docs.length > 0
          ? `${data.mentor_name} 멘토님의 ${typeLabel} 자료 (${docs.length}건)`
          : `아직 멘토님이 올린 ${typeLabel} 자료가 없습니다.`;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: text,
          agent_type: "agent_a",
          mentor_docs: docs,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "학습 팁을 불러오지 못했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || sending) return;
    setInput("");

    // 예약 설명 입력 대기 중 → 바로 예약 확정
    if (bookingPhase === "description" && pendingSlot) {
      finalizeBooking(msg);
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setSending(true);

    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, token }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply || data.content || "응답을 받지 못했습니다.",
          agent_type: data.agent_type,
          choices: data.choices,
          curation_items: data.curation_items,
          related_materials: data.related_materials,
          metadata: data.metadata,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "네트워크 오류가 발생했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const requestMentorHandoff = async () => {
    if (handoffSending) return;
    setHandoffSending(true);
    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch("/api/chat/handoff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: user?.id, token }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data.message ||
            "멘토 상담이 접수되었습니다. 담당 멘토님이 곧 연락드리겠습니다.",
          agent_type: "human_handoff",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "멘토 연결 요청 중 오류가 발생했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setHandoffSending(false);
    }
  };

  /* ── 조교 예약 플로우: 예약/취소 선택 → 날짜 → 시간 → 확정 ── */
  const startBookingFlow = () => {
    if (sending) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: "조교 연결" },
      {
        role: "assistant",
        content: "원하시는 메뉴를 선택해 주세요.",
        agent_type: "agent_b",
        choices: [
          {
            label: "예약하기",
            description: "조교 보충수업 새로 예약",
            _action: "booking_new",
          },
          {
            label: "취소하기",
            description: "기존 예약 취소",
            _action: "booking_cancel",
          },
        ],
      },
    ]);
  };

  const fetchBookingDates = async () => {
    if (sending) return;
    setSending(true);
    try {
      const res = await fetch("/api/chat/booking/dates");
      const dates = await res.json();
      if (!dates.length) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "현재 예약 가능한 시간이 없습니다.\n조교 선생님이 일정을 등록하면 안내해 드릴게요.",
            agent_type: "agent_b",
          },
        ]);
        return;
      }
      const WEEKDAY = ["일", "월", "화", "수", "목", "금", "토"];
      const choices = dates.map((d) => {
        const dt = new Date(d.date + "T00:00:00");
        const wd = WEEKDAY[dt.getDay()];
        return {
          label: `${d.date} (${wd})`,
          description: `${d.count}개 시간대 가능`,
          _action: "pick_date",
          _date: d.date,
        };
      });
      setBookingPhase("dates");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "예약 가능한 날짜를 선택해 주세요.",
          agent_type: "agent_b",
          choices,
          isBookingDates: true,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "예약 정보를 불러오지 못했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const startCancelFlow = async () => {
    if (sending) return;
    setSending(true);
    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch(
        `/api/chat/booking/my?token=${encodeURIComponent(token || "")}&student_id=${encodeURIComponent(user?.id || "")}`,
      );
      const slots = await res.json();
      if (!slots.length) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "현재 예약된 보충수업이 없습니다.",
            agent_type: "agent_b",
          },
        ]);
        return;
      }
      const choices = slots.map((s) => ({
        label: `${s.date} ${s.start_time}~${s.end_time} (${s.ta_name})`,
        description: s.booking_description || "",
        _action: "cancel_slot",
        _slotId: s.id,
      }));
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "취소할 예약을 선택해 주세요.",
          agent_type: "agent_b",
          choices,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "예약 목록을 불러오지 못했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const cancelBooking = async (slotId, label) => {
    if (sending) return;
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: label }]);
    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch("/api/chat/booking/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot_id: slotId, token, student_id: user?.id }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message || "예약이 취소되었습니다.",
          agent_type: "agent_b",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "예약 취소 중 오류가 발생했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const pickBookingDate = async (date) => {
    if (sending) return;
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: date }]);
    try {
      const res = await fetch(`/api/chat/booking/slots?date=${date}`);
      const slots = await res.json();
      if (!slots.length) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `${date}에는 가능한 시간대가 없습니다. 다른 날짜를 선택해 주세요.`,
            agent_type: "agent_b",
          },
        ]);
        setBookingPhase(null);
        return;
      }
      const choices = slots.map((s) => ({
        label: `${s.start_time}~${s.end_time} (${s.ta_name})`,
        description: `${s.ta_name} 조교`,
        _action: "pick_slot",
        _slotId: s.id,
        _date: date,
      }));
      setBookingPhase("slots");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `${date} 예약 가능 시간을 선택해 주세요.`,
          agent_type: "agent_b",
          choices,
          isBookingSlots: true,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "시간대 조회 중 오류가 발생했습니다.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const confirmBookingSlot = async (slotId, label) => {
    if (sending) return;
    // 시간대 선택 → 필요 내용 입력 요청 (아직 예약 확정 안 함)
    setPendingSlot({ slotId, label });
    setBookingPhase("description");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: label },
      {
        role: "assistant",
        content:
          "어떤 내용을 보충받고 싶으신지 간단히 적어 주세요.\n(예: 파이썬 클래스에서 self가 뭔지 모르겠어요)",
        agent_type: "agent_b",
      },
    ]);
  };

  const finalizeBooking = async (description) => {
    if (sending || !pendingSlot) return;
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: description }]);
    try {
      const token = localStorage.getItem("edu_sync_token");
      const res = await fetch("/api/chat/booking/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: pendingSlot.slotId,
          token,
          description,
        }),
      });
      const data = await res.json();
      setBookingPhase(null);
      setPendingSlot(null);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message || "예약이 완료되었습니다!",
          agent_type: "agent_b",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "예약 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
          agent_type: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  /* ── 웰컴 버튼 디스패처 ── */
  const handleQuickAction = (key) => {
    if (key === "curation") fetchTodayCuration();
    else if (key === "ta") startBookingFlow();
    else if (key === "tips") fetchLearningTips();
    else if (key === "mentor") requestMentorHandoff();
  };

  return (
    <div className="flex flex-col h-full bg-[#B2C7D9]">
      {/* ── KakaoTalk Header ── */}
      <header className="shrink-0 flex items-center justify-between px-3 py-2.5 bg-[#B2C7D9]">
        <button
          onClick={logout}
          className="p-1 text-[#555] hover:text-[#222] transition-colors"
          title="나가기"
        >
          <ChevronLeft size={22} />
        </button>
        <h1 className="text-[15px] font-semibold text-[#333]">{KAKAO_BOT_NAME}</h1>
        <div className="flex items-center gap-2">
          <Search size={18} className="text-[#555]" />
          <Menu size={18} className="text-[#555]" />
        </div>
      </header>

      {/* ── 수강생 카카오톡 화면 라벨 ── */}
      <div className="text-center py-1">
        <span className="inline-block px-3 py-0.5 bg-[#00000018] text-[11px] text-[#555] rounded-full">수강생 카카오톡 화면 (데모)</span>
      </div>

      {/* ── Messages ── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              msg={msg}
              onSelect={(text, choiceData) => {
                if (choiceData?._action === "booking_new") {
                  setMessages((prev) => [
                    ...prev,
                    { role: "user", content: text },
                  ]);
                  fetchBookingDates();
                } else if (choiceData?._action === "booking_cancel") {
                  setMessages((prev) => [
                    ...prev,
                    { role: "user", content: text },
                  ]);
                  startCancelFlow();
                } else if (choiceData?._action === "cancel_slot") {
                  cancelBooking(choiceData._slotId, text);
                } else if (choiceData?._action === "pick_date") {
                  pickBookingDate(choiceData._date);
                } else if (choiceData?._action === "pick_slot") {
                  confirmBookingSlot(choiceData._slotId, text);
                } else if (choiceData?._action === "tips_type") {
                  fetchTipsByType(choiceData._type);
                } else {
                  send(text);
                }
              }}
              onQuickAction={handleQuickAction}
              sending={sending}
            />
          ))}
        </AnimatePresence>
        {sending && (
          <div className="flex items-start gap-2 mb-2">
            <div className="shrink-0 w-10 h-10 rounded-xl bg-[#4A90D9] flex items-center justify-center text-white overflow-hidden shadow-sm">
              <span className="leading-none font-bold text-[11px]">IT<br/>KOREA</span>
            </div>
            <div>
              <p className="text-[12px] font-medium text-[#333] mb-1">{KAKAO_BOT_NAME}</p>
              <div className="px-3 py-2.5 bg-white rounded-xl rounded-tl-[4px] shadow-sm">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-[#999] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-[#999] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-[#999] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Bottom: mentor button + input ── */}
      <div className="shrink-0 bg-white border-t border-[#e0e0e0]">
        <div className="px-3 pt-2">
          <button
            onClick={requestMentorHandoff}
            disabled={handoffSending}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-[#FEE500] hover:bg-[#f5dd00] text-[#3b1e1e] rounded-lg text-[13px] font-medium transition-colors disabled:opacity-40"
          >
            <UserCircle size={15} />
            {handoffSending ? "연결 중..." : "🙋‍♂️ 1:1 멘토 상담 연결"}
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex items-center gap-2 p-2.5"
        >
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요"
            className="flex-1 px-3 py-2 bg-[#f5f5f5] border border-[#e0e0e0] rounded-full text-[13.5px] text-[#333] placeholder:text-[#aaa] focus:outline-none focus:border-[#ccc]"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={!input.trim() || sending}
            className="shrink-0 px-3.5 py-2 bg-[#FEE500] hover:bg-[#f5dd00] text-[#3b1e1e] text-[13px] font-semibold rounded-full disabled:opacity-30 transition-colors"
          >
            전송
          </button>
        </form>
      </div>
    </div>
  );
}
