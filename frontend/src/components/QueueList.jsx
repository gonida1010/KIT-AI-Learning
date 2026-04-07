import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Check, Eye } from "lucide-react";

const priorityConfig = {
  high: {
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-100 text-red-600",
    label: "긴급",
  },
  medium: {
    bg: "bg-orange-50",
    border: "border-orange-200",
    badge: "bg-orange-100 text-orange-600",
    label: "보통",
  },
  low: {
    bg: "bg-gray-50",
    border: "border-gray-200",
    badge: "bg-gray-100 text-gray-500",
    label: "낮음",
  },
};

export default function QueueList({ queue, onResolve, onViewStudent }) {
  if (!queue || queue.length === 0) {
    return (
      <div className="bg-green-50 border border-green-100 rounded-xl p-6 text-center">
        <Check size={24} className="text-green-400 mx-auto mb-2" />
        <p className="text-sm text-green-600 font-medium">
          대기열이 비어 있습니다!
        </p>
        <p className="text-xs text-green-400 mt-1">
          모든 상담이 처리되었습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {queue.map((item, i) => {
        const cfg = priorityConfig[item.priority] || priorityConfig.medium;
        return (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`${cfg.bg} border ${cfg.border} rounded-xl p-4`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">
                    {item.student_name}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${cfg.badge}`}
                  >
                    {cfg.label}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-1">{item.reason}</p>
                <p className="text-xs text-gray-400 italic truncate">
                  "{item.last_message}"
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => onViewStudent(item.student_id)}
                  className="p-2 rounded-lg hover:bg-white/70 text-gray-400 hover:text-purple-500 transition-colors"
                  title="히스토리 보기"
                >
                  <Eye size={14} />
                </button>
                <button
                  onClick={() => onResolve(item.id)}
                  className="p-2 rounded-lg hover:bg-white/70 text-gray-400 hover:text-green-500 transition-colors"
                  title="해결 완료"
                >
                  <Check size={14} />
                </button>
              </div>
            </div>
            <p className="text-[10px] text-gray-300 mt-2">
              {new Date(item.created_at).toLocaleString("ko-KR")}
            </p>
          </motion.div>
        );
      })}
    </div>
  );
}
