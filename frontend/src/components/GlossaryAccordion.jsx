import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, ChevronDown } from "lucide-react";

export default function GlossaryAccordion({ glossary = {} }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(glossary);

  if (entries.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-6 py-5 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-amber-500" />
          <span className="font-bold text-gray-700 text-sm">
            💡 용어 사전 열어보기
          </span>
          <span className="text-xs text-gray-300 ml-1">
            ({entries.length}개)
          </span>
        </div>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={18} className="text-gray-400" />
        </motion.div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-5 space-y-3">
              {entries.map(([term, definition], i) => (
                <motion.div
                  key={term}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex gap-4 items-start p-3 rounded-xl bg-amber-50/60 border border-amber-100"
                >
                  <span className="shrink-0 inline-flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100 text-amber-600 text-xs font-bold">
                    {term.charAt(0).toUpperCase()}
                  </span>
                  <div>
                    <p className="font-semibold text-gray-700 text-sm">
                      {term}
                    </p>
                    <p className="text-gray-500 text-xs leading-relaxed mt-0.5">
                      {definition}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
