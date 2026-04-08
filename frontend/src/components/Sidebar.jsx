import { useAuth } from "../contexts/AuthContext";
import { MessageSquare, Users, BookOpen, Calendar, LogOut } from "lucide-react";

const NAV = {
  mentor: [
    { key: "mentor", label: "대시보드", Icon: Users },
    { key: "knowledge", label: "지식 베이스", Icon: BookOpen },
  ],
  ta: [
    { key: "ta", label: "스케줄", Icon: Calendar },
    { key: "knowledge", label: "지식 베이스", Icon: BookOpen },
  ],
};

export default function Sidebar({ current, onNavigate }) {
  const { user, logout } = useAuth();
  const items = NAV[user?.role] || [];

  return (
    <aside className="hidden md:flex flex-col w-60 bg-white border-r border-slate-200 shrink-0">
      {/* Logo */}
      <div className="p-5 border-b border-slate-200">
        <h1 className="text-lg font-bold text-primary-600">Edu-Sync AI</h1>
        <p className="text-xs text-slate-400 mt-0.5">v3.0 Multi-Agent</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1">
        {items.map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => onNavigate(key)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              current === key
                ? "bg-primary-50 text-primary-700 font-medium"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 mb-3">
          {user?.profile_image ? (
            <img
              src={user.profile_image}
              className="w-8 h-8 rounded-full"
              alt=""
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center text-xs font-bold">
              {user?.name?.[0] || "?"}
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-800 truncate">
              {user?.name}
            </p>
            <p className="text-xs text-slate-400">
              {user?.role === "mentor" ? "멘토" : "TA"}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          로그아웃
        </button>
      </div>
    </aside>
  );
}
