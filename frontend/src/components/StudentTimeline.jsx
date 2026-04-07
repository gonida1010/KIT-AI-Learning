import { motion } from "framer-motion";
import { Search, FileText, MessageSquare, PhoneForwarded } from "lucide-react";

const eventIcons = {
  search: { icon: Search, color: "text-blue-500", bg: "bg-blue-50" },
  doc_access: { icon: FileText, color: "text-green-500", bg: "bg-green-50" },
  chat: { icon: MessageSquare, color: "text-indigo-500", bg: "bg-indigo-50" },
  handoff: {
    icon: PhoneForwarded,
    color: "text-orange-500",
    bg: "bg-orange-50",
  },
};

export default function StudentTimeline({ data }) {
  if (!data) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-sm font-bold text-purple-600">
          {data.name?.charAt(0)}
        </div>
        <div>
          <p className="font-bold text-gray-700 text-sm">{data.name}</p>
          {data.frequent_keywords?.length > 0 && (
            <div className="flex gap-1 mt-1 flex-wrap">
              {data.frequent_keywords.map((kw) => (
                <span
                  key={kw}
                  className="px-2 py-0.5 bg-purple-50 text-purple-400 rounded text-[10px]"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="relative border-l-2 border-gray-100 ml-4 space-y-4 pl-4">
        {data.events?.map((event, i) => {
          const cfg = eventIcons[event.event_type] || eventIcons.chat;
          const Icon = cfg.icon;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="relative"
            >
              {/* Dot on timeline */}
              <div
                className={`absolute -left-[22px] top-1 w-4 h-4 rounded-full border-2 border-white ${cfg.bg} flex items-center justify-center`}
              >
                <Icon size={8} className={cfg.color} />
              </div>

              <div>
                <p className="text-[10px] text-gray-300">
                  {new Date(event.timestamp).toLocaleString("ko-KR")}
                </p>
                <p className="text-sm text-gray-700 font-medium">
                  {event.content}
                </p>
                {event.detail && (
                  <p className="text-xs text-gray-400 mt-0.5">{event.detail}</p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
