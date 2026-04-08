import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("edu_sync_token");
    if (!token) {
      setLoading(false);
      return;
    }
    fetch(`/api/auth/me?token=${encodeURIComponent(token)}`)
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setUser)
      .catch(() => localStorage.removeItem("edu_sync_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (code, inviteCode) => {
    const res = await fetch("/api/auth/kakao/callback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, invite_code: inviteCode || null }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || "로그인 실패");
    }
    const data = await res.json();
    localStorage.setItem("edu_sync_token", data.token);
    setUser(data.user);
    return data.user;
  };

  const logout = useCallback(async () => {
    const token = localStorage.getItem("edu_sync_token");
    if (token)
      await fetch(`/api/auth/logout?token=${encodeURIComponent(token)}`, {
        method: "POST",
      }).catch(() => {});
    localStorage.removeItem("edu_sync_token");
    localStorage.removeItem("edu_sync_invite");
    setUser(null);
  }, []);

  const updateRole = async (role) => {
    const token = localStorage.getItem("edu_sync_token");
    const res = await fetch(
      `/api/auth/role?token=${encodeURIComponent(token)}&role=${role}`,
      { method: "POST" },
    );
    if (res.ok) setUser((prev) => ({ ...prev, role }));
  };

  const demoLogin = async (role) => {
    const res = await fetch(`/api/auth/demo?role=${role}`, { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    localStorage.setItem("edu_sync_token", data.token);
    setUser(data.user);
  };

  const linkMentor = async (inviteCode) => {
    const token = localStorage.getItem("edu_sync_token");
    await fetch(`/api/auth/link-mentor?token=${encodeURIComponent(token)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ invite_code: inviteCode }),
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        updateRole,
        demoLogin,
        linkMentor,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
