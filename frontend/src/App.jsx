import { useState, useEffect } from "react";
import { useAuth } from "./contexts/AuthContext";
import Sidebar from "./components/Sidebar";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import StudentChat from "./pages/StudentChat";
import MentorDashboard from "./pages/MentorDashboard";
import MentorStudents from "./pages/MentorStudents";
import TADashboard from "./pages/TADashboard";
import KnowledgeBase from "./pages/KnowledgeBase";
import AdminDashboard from "./pages/AdminDashboard";

export default function App() {
  const { user, loading } = useAuth();
  const [page, setPage] = useState("chat");

  useEffect(() => {
    if (user) {
      if (user.role === "student") setPage("chat");
      else if (user.role === "mentor") setPage("mentor");
      else if (user.role === "ta") setPage("ta");
      else if (user.role === "admin") setPage("admin");
    }
  }, [user]);

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="animate-spin h-8 w-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );

  if (!user) return <LoginPage />;

  const rolePages = {
    student: { chat: <StudentChat /> },
    mentor: {
      mentor: <MentorDashboard />,
      students: <MentorStudents />,
      knowledge: <KnowledgeBase />,
    },
    ta: {
      ta: <TADashboard />,
    },
    admin: {
      admin: <AdminDashboard />,
    },
  };
  const pages = rolePages[user.role] || rolePages.student;
  const currentPage = pages[page] || Object.values(pages)[0];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800">
      {user.role !== "student" && (
        <Sidebar current={page} onNavigate={setPage} />
      )}
      <Layout fullWidth={user.role === "student"}>{currentPage}</Layout>
    </div>
  );
}
