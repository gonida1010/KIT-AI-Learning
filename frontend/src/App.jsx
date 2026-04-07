import { useState } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Sidebar from "./components/Sidebar";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import StudentChat from "./pages/StudentChat";
import MentorDashboard from "./pages/MentorDashboard";
import TADashboard from "./pages/TADashboard";
import CurriMap from "./pages/CurriMap";
import KnowledgeBase from "./pages/KnowledgeBase";

const ROLE_PAGES = {
  student: {
    default: "chat",
    pages: {
      chat: StudentChat,
      currimap: CurriMap,
    },
  },
  mentor: {
    default: "mentor",
    pages: {
      mentor: MentorDashboard,
      currimap: CurriMap,
      knowledge: KnowledgeBase,
    },
  },
  ta: {
    default: "ta",
    pages: {
      ta: TADashboard,
      currimap: CurriMap,
      knowledge: KnowledgeBase,
    },
  },
};

function AuthenticatedApp() {
  const { user } = useAuth();
  const roleConfig = ROLE_PAGES[user.role] || ROLE_PAGES.student;
  const [page, setPage] = useState(roleConfig.default);
  const PageComponent =
    roleConfig.pages[page] || Object.values(roleConfig.pages)[0];

  return (
    <div className="flex min-h-screen">
      <Sidebar currentPage={page} onNavigate={setPage} role={user.role} />
      <Layout>
        <PageComponent />
      </Layout>
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
        <div className="w-8 h-8 border-3 border-indigo-200 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <LoginPage />;
  return <AuthenticatedApp />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
