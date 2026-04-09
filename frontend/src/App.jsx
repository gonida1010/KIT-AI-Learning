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

function QRApprove({ qrToken }) {
  const { user } = useAuth();
  const [status, setStatus] = useState("ready");

  const approve = async () => {
    const token = localStorage.getItem("edu_sync_token");
    if (!token) {
      setStatus("need_login");
      return;
    }
    setStatus("processing");
    const res = await fetch("/api/auth/qr/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qr_token: qrToken, session_token: token }),
    });
    setStatus(res.ok ? "done" : "error");
  };

  if (!user)
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <p className="text-slate-600">모바일에서 먼저 로그인해 주세요.</p>
      </div>
    );

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white gap-4">
      <h2 className="text-xl font-bold text-slate-800">PC 로그인 승인</h2>
      <p className="text-slate-500">{user.name}님으로 PC에 로그인합니다.</p>
      {status === "ready" && (
        <button
          onClick={approve}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          승인
        </button>
      )}
      {status === "processing" && (
        <p className="text-primary-600">처리 중...</p>
      )}
      {status === "done" && (
        <p className="text-emerald-600">승인 완료! PC에서 로그인됩니다.</p>
      )}
      {status === "error" && (
        <p className="text-red-500">오류가 발생했습니다. 다시 시도해 주세요.</p>
      )}
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  const [page, setPage] = useState("chat");

  // URL params
  const params = new URLSearchParams(window.location.search);
  const oauthCode = params.get("code");
  const qrApprove = params.get("qr_approve");
  const inviteCode = params.get("invite");

  useEffect(() => {
    if (inviteCode) localStorage.setItem("edu_sync_invite", inviteCode);
  }, [inviteCode]);

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

  if (qrApprove) return <QRApprove qrToken={qrApprove} />;

  if (!user) return <LoginPage oauthCode={oauthCode} />;

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
