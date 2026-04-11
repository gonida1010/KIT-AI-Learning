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
  const [loadedMentorPages, setLoadedMentorPages] = useState([]);
  const mentorPage = ["mentor", "students", "knowledge"].includes(page)
    ? page
    : "mentor";

  useEffect(() => {
    if (user) {
      if (user.role === "student") setPage("chat");
      else if (user.role === "mentor") setPage("mentor");
      else if (user.role === "ta") setPage("ta");
      else if (user.role === "admin") setPage("admin");
    }
  }, [user]);

  useEffect(() => {
    if (user?.role !== "mentor") {
      setLoadedMentorPages([]);
      return;
    }
    setLoadedMentorPages((prev) =>
      prev.includes(mentorPage) ? prev : [...prev, mentorPage],
    );
  }, [mentorPage, user?.role]);

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="animate-spin h-8 w-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );

  if (!user) return <LoginPage />;

  const renderContent = () => {
    if (user.role === "student") return <StudentChat />;
    if (user.role === "ta") return <TADashboard />;
    if (user.role === "admin") return <AdminDashboard />;

    return (
      <>
        {(mentorPage === "mentor" || loadedMentorPages.includes("mentor")) && (
          <div className={mentorPage === "mentor" ? "block" : "hidden"}>
            <MentorDashboard isActive={mentorPage === "mentor"} />
          </div>
        )}
        {(mentorPage === "students" || loadedMentorPages.includes("students")) && (
          <div className={mentorPage === "students" ? "block" : "hidden"}>
            <MentorStudents isActive={mentorPage === "students"} />
          </div>
        )}
        {(mentorPage === "knowledge" || loadedMentorPages.includes("knowledge")) && (
          <div className={mentorPage === "knowledge" ? "block" : "hidden"}>
            <KnowledgeBase isActive={mentorPage === "knowledge"} />
          </div>
        )}
      </>
    );
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800">
      {user.role !== "student" && (
        <Sidebar current={page} onNavigate={setPage} />
      )}
      <Layout fullWidth={user.role === "student"}>{renderContent()}</Layout>
    </div>
  );
}
