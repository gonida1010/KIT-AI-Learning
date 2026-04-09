import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";

export default function Layout({ children, fullWidth }) {
  const [showScrollTop, setShowScrollTop] = useState(false);
  const mainRef = useRef(null);

  useEffect(() => {
    const scrollContainer = mainRef.current;
    if (!scrollContainer) return undefined;

    const handleScroll = () => {
      setShowScrollTop(scrollContainer.scrollTop > 240);
    };

    handleScroll();
    scrollContainer.addEventListener("scroll", handleScroll, {
      passive: true,
    });
    return () => scrollContainer.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <main
        ref={mainRef}
        className={`flex-1 overflow-auto ${fullWidth ? "" : "p-4 md:p-6"}`}
      >
        {children}
      </main>
      <button
        onClick={() =>
          mainRef.current?.scrollTo({ top: 0, behavior: "smooth" })
        }
        className={`fixed bottom-6 right-6 z-50 rounded-full border border-slate-200 bg-white p-3 text-slate-500 shadow-lg transition-all hover:border-primary-300 hover:text-primary-600 ${showScrollTop ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-3 opacity-0"}`}
        aria-label="상단으로 이동"
      >
        <ArrowUp size={18} />
      </button>
    </>
  );
}
