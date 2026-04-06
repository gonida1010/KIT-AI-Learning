import { motion } from "framer-motion";
import { MapPin } from "lucide-react";

export default function ProgressTimeline({ percentage, location }) {
  const clampedPercent = Math.min(100, Math.max(0, percentage));

  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 md:p-8">
      <div className="flex items-center gap-2 mb-6">
        <MapPin size={18} className="text-indigo-500" />
        <h3 className="font-bold text-gray-700 text-base">현재 나의 위치</h3>
        <span className="ml-auto text-2xl font-extrabold text-indigo-500">
          {clampedPercent}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative w-full h-4 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-indigo-400 via-indigo-500 to-purple-500"
          initial={{ width: 0 }}
          animate={{ width: `${clampedPercent}%` }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
        {/* Glow effect */}
        <motion.div
          className="absolute top-0 h-full rounded-full bg-gradient-to-r from-indigo-400 via-indigo-500 to-purple-500 opacity-30 blur-sm"
          initial={{ width: 0 }}
          animate={{ width: `${clampedPercent}%` }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </div>

      {/* Label row */}
      <div className="flex justify-between mt-3 text-xs text-gray-300">
        <span>시작</span>
        <span>수료</span>
      </div>

      {/* Milestone markers */}
      <div className="relative mt-4 flex justify-between items-center">
        {[0, 25, 50, 75, 100].map((milestone) => (
          <div key={milestone} className="flex flex-col items-center">
            <div
              className={`w-3 h-3 rounded-full border-2 transition-colors ${
                clampedPercent >= milestone
                  ? "bg-indigo-500 border-indigo-500"
                  : "bg-white border-gray-200"
              }`}
            />
            <span className="text-[10px] text-gray-300 mt-1">{milestone}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
