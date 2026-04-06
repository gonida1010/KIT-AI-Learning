import TermText from "./TermText";

const colorMap = {
  blue: {
    bg: "bg-blue-50/60",
    border: "border-blue-100",
    badge: "bg-blue-100 text-blue-500",
  },
  purple: {
    bg: "bg-purple-50/60",
    border: "border-purple-100",
    badge: "bg-purple-100 text-purple-500",
  },
};

export default function InfoCard({
  title,
  emoji,
  content,
  glossary,
  color = "blue",
}) {
  const scheme = colorMap[color] || colorMap.blue;

  return (
    <div
      className={`rounded-2xl border ${scheme.border} ${scheme.bg} p-6 h-full shadow-sm hover:shadow-md transition-shadow`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">{emoji}</span>
        <h3 className="font-bold text-gray-700 text-base">{title}</h3>
      </div>
      <div className="text-gray-600 text-sm leading-relaxed">
        <TermText text={content} glossary={glossary} />
      </div>
    </div>
  );
}
