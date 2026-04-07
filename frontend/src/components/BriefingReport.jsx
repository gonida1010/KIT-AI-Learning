import { User, Target, Lightbulb, Search } from "lucide-react";

export default function BriefingReport({ report }) {
  if (!report) return null;

  return (
    <div className="space-y-2.5">
      <div className="flex items-start gap-2.5 p-2.5 bg-blue-50/60 rounded-lg">
        <User size={14} className="text-blue-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-[10px] font-bold text-blue-500 mb-0.5">
            요청 학생
          </p>
          <p className="text-sm text-gray-700">
            {report.student_name}
            {report.search_history && (
              <span className="text-xs text-gray-400 ml-1">
                (최근: {report.search_history})
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-start gap-2.5 p-2.5 bg-amber-50/60 rounded-lg">
        <Target size={14} className="text-amber-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-[10px] font-bold text-amber-500 mb-0.5">
            핵심 필요 내용
          </p>
          <p className="text-sm text-gray-700">{report.core_need}</p>
        </div>
      </div>

      <div className="flex items-start gap-2.5 p-2.5 bg-green-50/60 rounded-lg">
        <Lightbulb size={14} className="text-green-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-[10px] font-bold text-green-500 mb-0.5">
            AI 추천 지도 방향
          </p>
          <p className="text-sm text-gray-700">{report.ai_recommendation}</p>
        </div>
      </div>
    </div>
  );
}
