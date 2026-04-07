import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, User, Bot, PhoneForwarded } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

export default function StudentChat() {
  const { user } = useAuth();
  const studentId = user?.id || "student_1";
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  // 대화 이력 로드
  useEffect(() => {
    fetch(`/api/chat/history/${studentId}`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setMessages(data);
      })
      .catch(() => {});
  }, [studentId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || sending) return;
    const msg = text.trim();
    setInput("");
    setSending(true);

    // 낙관적 UI
    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: msg,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, message: msg }),
      });
      const data = await res.json();
      if (data.reply) {
        setMessages((prev) => [...prev, data.reply]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: "err",
          role: "assistant",
          content: "네트워크 오류가 발생했습니다. 다시 시도해 주세요.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleHandoff = async () => {
    try {
      await fetch("/api/chat/handoff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId }),
      });
      setMessages((prev) => [
        ...prev,
        {
          id: "handoff_" + Date.now(),
          role: "assistant",
          content:
            "✅ 멘토 상담 대기열에 등록되었습니다. 담당 멘토님이 최대한 빠르게 연락드리겠습니다.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch {
      // ignore
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="shrink-0 pb-4 border-b border-gray-100 mb-4">
        <h2 className="text-xl font-bold text-gray-800">💬 AI 멘토 데스크</h2>
        <p className="text-sm text-gray-400 mt-1">
          궁금한 내용을 자유롭게 물어보세요. AI가 24시간 답변합니다.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pb-4 pr-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-300">
            <Bot size={40} className="mb-3 text-gray-200" />
            <p className="text-sm">대화를 시작해 보세요!</p>
            <p className="text-xs mt-1">
              수업 내용, 취업, 일정 등 무엇이든 물어보세요.
            </p>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-1">
                  <Bot size={16} className="text-indigo-500" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-500 text-white rounded-br-md"
                    : "bg-white border border-gray-100 text-gray-700 rounded-bl-md shadow-sm"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* 선택지 버튼 */}
                {msg.role === "assistant" &&
                  msg.choices &&
                  msg.choices.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      {msg.choices.map((c, i) => (
                        <button
                          key={i}
                          onClick={() => sendMessage(c.label)}
                          className="w-full text-left px-3 py-2 bg-indigo-50 hover:bg-indigo-100 rounded-lg text-xs transition-colors"
                        >
                          <span className="font-semibold text-indigo-600">
                            {c.label}
                          </span>
                          {c.description && (
                            <span className="text-gray-400 ml-1.5">
                              {c.description}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}

                <p className="text-[10px] mt-1.5 opacity-50">
                  {msg.timestamp &&
                    new Date(msg.timestamp).toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                </p>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center shrink-0 mt-1">
                  <User size={16} className="text-gray-400" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {sending && (
          <div className="flex gap-2.5">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
              <Bot size={16} className="text-indigo-500" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 rounded-full bg-indigo-300"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Handoff + Input */}
      <div className="shrink-0 border-t border-gray-100 pt-3 space-y-2">
        <button
          onClick={handleHandoff}
          className="w-full flex items-center justify-center gap-2 py-2 text-xs text-orange-500 bg-orange-50 hover:bg-orange-100 rounded-xl transition-colors font-medium"
        >
          <PhoneForwarded size={14} />
          🙋‍♂️ 멘토님과 직접 상담하기
        </button>

        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            rows={1}
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-50"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || sending}
            className="px-4 py-2.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 disabled:opacity-40 transition-colors"
          >
            {sending ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
