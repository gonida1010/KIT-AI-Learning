import { useState } from "react";
import {
  MessageSquare,
  LayoutDashboard,
  CalendarClock,
  Compass,
  BookOpen,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const NAV_BY_ROLE = {
  student: [
    {
      id: "chat",
      label: "💬 AI 멘토",
      icon: MessageSquare,
      desc: "AI 챗봇 상담",
    },
    {
      id: "currimap",
      label: "🧭 CurriMap",
      icon: Compass,
      desc: "진척도 나침반",
    },
  ],
  mentor: [
    {
      id: "mentor",
      label: "📊 대시보드",
      icon: LayoutDashboard,
      desc: "브리핑 & 대기열",
    },
    {
      id: "currimap",
      label: "🧭 CurriMap",
      icon: Compass,
      desc: "진척도 나침반",
    },
    {
      id: "knowledge",
      label: "📚 지식 베이스",
      icon: BookOpen,
      desc: "자료 관리",
    },
  ],
  ta: [
    {
      id: "ta",
      label: "📅 스케줄 관리",
      icon: CalendarClock,
      desc: "스케줄 & 브리핑",
    },
    {
      id: "currimap",
      label: "🧭 CurriMap",
      icon: Compass,
      desc: "진척도 나침반",
    },
    {
      id: "knowledge",
      label: "📚 지식 베이스",
      icon: BookOpen,
      desc: "자료 관리",
    },
  ],
};

const ROLE_LABELS = {
  student: { label: "🎓 수강생", color: "bg-blue-50 text-blue-600" },
  mentor: { label: "👨‍🏫 멘토", color: "bg-green-50 text-green-600" },
  ta: { label: "📋 조교", color: "bg-purple-50 text-purple-600" },
};

export default function Sidebar({ currentPage, onNavigate, role }) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems = NAV_BY_ROLE[role] || NAV_BY_ROLE.student;
  const roleInfo = ROLE_LABELS[role] || ROLE_LABELS.student;

  const handleNav = (id) => {
    onNavigate(id);
    setMobileOpen(false);
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-50 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-extrabold text-gray-800 tracking-tight">
            <span className="text-indigo-500">Edu</span>-Sync
            <span className="text-xs ml-1 font-medium text-indigo-400 bg-indigo-50 px-1.5 py-0.5 rounded">
              AI
            </span>
          </h1>
          <p className="text-[10px] text-gray-300 mt-0.5">
            KDT 하이브리드 관리 플랫폼
          </p>
        </div>
        <button
          onClick={() => setMobileOpen(false)}
          className="md:hidden p-1 text-gray-400 hover:text-gray-600"
        >
          <X size={20} />
        </button>
      </div>

      {/* User Info */}
      <div className="px-4 py-3 border-b border-gray-50">
        <div className="flex items-center gap-2.5">
          {user?.profile_image ? (
            <img
              src={user.profile_image}
              alt=""
              className="w-9 h-9 rounded-full object-cover"
            />
          ) : (
            <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-bold text-indigo-600">
              {user?.name?.charAt(0) || "?"}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-700 truncate">
              {user?.name}
            </p>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${roleInfo.color}`}
            >
              {roleInfo.label}
            </span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ id, label, icon: Icon, desc }) => {
          const active = currentPage === id;
          return (
            <button
              key={id}
              onClick={() => handleNav(id)}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all duration-200
                ${
                  active
                    ? "bg-indigo-50 text-indigo-600 shadow-sm"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-700"
                }
              `}
            >
              <Icon
                size={18}
                className={active ? "text-indigo-500" : "text-gray-400"}
              />
              <div>
                <p
                  className={`text-sm font-semibold ${active ? "text-indigo-600" : "text-gray-600"}`}
                >
                  {label}
                </p>
                <p className="text-[10px] text-gray-300">{desc}</p>
              </div>
            </button>
          );
        })}
      </nav>

      {/* Footer with Logout */}
      <div className="px-3 py-3 border-t border-gray-50">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
        >
          <LogOut size={16} />
          로그아웃
        </button>
        <p className="text-[10px] text-gray-300 mt-2 px-3">
          © 2026 KIT · Edu-Sync AI
        </p>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile header bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-100 flex items-center px-4 z-40 shadow-sm">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-1.5 text-gray-500 hover:text-gray-700"
        >
          <Menu size={22} />
        </button>
        <h1 className="ml-3 text-sm font-bold text-gray-700">
          <span className="text-indigo-500">Edu</span>-Sync AI
        </h1>
        <span
          className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-bold ${roleInfo.color}`}
        >
          {roleInfo.label}
        </span>
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/30 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
        fixed left-0 top-0 h-screen w-64 bg-white border-r border-gray-100 flex flex-col z-50 shadow-sm
        transition-transform duration-300
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0
      `}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
