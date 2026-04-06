import { useState, useRef, useEffect, Fragment } from "react";

/**
 * <term>용어</term> 태그를 파싱하여, 전문 용어에 점선 밑줄 + 호버 툴팁을 적용하는 컴포넌트.
 */
export default function TermText({ text, glossary = {} }) {
  if (!text) return null;

  // <term>...</term> 기준으로 분리
  const parts = text.split(/(<term>.*?<\/term>)/g);

  return (
    <span>
      {parts.map((part, idx) => {
        const match = part.match(/^<term>(.*?)<\/term>$/);
        if (match) {
          const term = match[1];
          const definition = glossary[term];
          return (
            <TermWithTooltip key={idx} term={term} definition={definition} />
          );
        }
        return <Fragment key={idx}>{part}</Fragment>;
      })}
    </span>
  );
}

function TermWithTooltip({ term, definition }) {
  const [show, setShow] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const ref = useRef(null);
  const tooltipRef = useRef(null);

  useEffect(() => {
    if (show && ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setPos({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    }
  }, [show]);

  return (
    <>
      <span
        ref={ref}
        className="relative inline-block border-b-2 border-dotted border-indigo-300 text-indigo-600 font-semibold cursor-help transition-colors hover:border-indigo-500 hover:text-indigo-700"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {term}

        {/* Inline tooltip */}
        {show && definition && (
          <span
            ref={tooltipRef}
            className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-4 py-2.5 w-64
                       bg-gray-800 text-white text-xs leading-relaxed rounded-xl shadow-xl
                       pointer-events-none animate-fade-in"
            style={{ animation: "fadeIn 0.2s ease-out" }}
          >
            <span className="font-bold text-indigo-300 block mb-0.5">
              {term}
            </span>
            {definition}
            {/* Arrow */}
            <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-px w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-gray-800" />
          </span>
        )}
      </span>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateX(-50%) translateY(4px); }
          to   { opacity: 1; transform: translateX(-50%) translateY(0);   }
        }
      `}</style>
    </>
  );
}
