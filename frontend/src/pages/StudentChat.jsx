import { useState, useRef, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Send,
  Bot,
  User,
  AlertTriangle,
  Newspaper,
  LogOut,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
    <div className="mt-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <Newspaper size={14} className="text-primary-500" />
        <span className="text-xs text-primary-600 font-medium">
          {item.category} · {item.date}
        </span>
      </div>
      <p className="text-sm text-slate-800 font-medium">{item.title}</p>
      {item.summary && (
        <p className="text-xs text-slate-500 mt-1">{item.summary}</p>
      )}
    </div>
  );
}

function ChoiceButtons({ choices, onSelect }) {
  if (!choices?.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {choices.map((c, i) => (
        <button
          key={i}
          onClick={() => onSelect(c.label || c.description || c)}
          className="px-3 py-1.5 text-xs bg-slate-100 hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 hover:border-primary-300 rounded-full transition-colors"
        >
          {c.label || c}
        </button>
      ))}
    </div>
  );
}

function ChatMessage({ msg, onSelect }) {
  const isUser = msg.role === "user";
  const badge = AGENT_BADGES[msg.agent_type];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      <div
        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-primary-500 text-white" : "bg-slate-200 text-slate-600"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className={`max-w-[80%] ${isUser ? "text-right" : ""}`}>
        {badge && (
          <span
            className={`inline-block px-2 py-0.5 text-[10px] rounded-full mb-1 ${badge.color}`}
          >
            {badge.label}
          </span>
        )}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-primary-500 text-white rounded-br-md"
              : "bg-white text-slate-700 border border-slate-200 rounded-bl-md shadow-sm"
          }`}
        >
          {msg.content}
        </div>
        {msg.curation_items?.map((item, i) => (
          <CurationCard key={i} item={item} />
        ))}
        <ChoiceButtons choices={msg.choices} onSelect={onSelect} />
        {msg.agent_type === "human_handoff" && (
          <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-600">
            <AlertTriangle size={12} />
            멘토에게 상담이 접수되었습니다
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function StudentChat() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
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
        content: `안녕하세요 ${user?.name || ""}님! 😊\n무엇이든 물어보세요.\n• 취업·채용 정보, IT 뉴스\n• 프로그래밍 학습 질문\n• 조교 보충수업 예약\n• 자격증·공모전 정보`,
        agent_type: null,
      },
    ]);
  }, [user]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || sending) return;
    setInput("");
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

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center">
            <Bot size={18} className="text-primary-600" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-800">Edu-Sync AI</h1>
            <p className="text-[11px] text-slate-400">멀티 에이전트 챗봇</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="p-2 text-slate-400 hover:text-red-500 transition-colors"
        >
          <LogOut size={18} />
        </button>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <ChatMessage key={i} msg={msg} onSelect={(text) => send(text)} />
          ))}
        </AnimatePresence>
        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600">
              <Bot size={16} />
            </div>
            <div className="px-4 py-2.5 bg-white border border-slate-200 rounded-2xl rounded-bl-md shadow-sm">
              <div className="flex gap-1">
                <span
                  className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 p-3 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2"
        >
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="질문을 입력하세요..."
            className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-100"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={!input.trim() || sending}
            className="px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white disabled:opacity-40 rounded-xl transition-colors"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
