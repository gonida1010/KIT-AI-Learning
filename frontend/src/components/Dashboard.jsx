import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import ProgressTimeline from "./ProgressTimeline";
import InfoCard from "./InfoCard";
import GlossaryAccordion from "./GlossaryAccordion";

export default function Dashboard({ data, onReset }) {
  const { location, progress_percentage, why_learn, whats_next, glossary } =
    data;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Back button */}
      <button
        onClick={onReset}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-indigo-500 transition-colors group"
      >
        <ArrowLeft
          size={16}
          className="group-hover:-translate-x-1 transition-transform"
        />
        다른 파일 분석하기
      </button>

      {/* Location badge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="text-center"
      >
        <span className="inline-block px-5 py-2 rounded-full bg-indigo-100 text-indigo-600 font-semibold text-sm">
          📍 {location}
        </span>
      </motion.div>

      {/* Progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <ProgressTimeline
          percentage={progress_percentage}
          location={location}
        />
      </motion.div>

      {/* Info cards */}
      <div className="grid md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <InfoCard
            title="이것을 왜 배우나요?"
            emoji="🤔"
            content={why_learn}
            glossary={glossary}
            color="blue"
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <InfoCard
            title="다음은 무엇인가요?"
            emoji="🚀"
            content={whats_next}
            glossary={glossary}
            color="purple"
          />
        </motion.div>
      </div>

      {/* Glossary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <GlossaryAccordion glossary={glossary} />
      </motion.div>
    </motion.div>
  );
}
