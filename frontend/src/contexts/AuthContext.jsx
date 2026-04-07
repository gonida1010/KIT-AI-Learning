import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { id, name, role, profile_image }
  const [loading, setLoading] = useState(true);

  // 페이지 로드 시 저장된 세션 확인
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
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem("edu_sync_token");
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (code) => {
    const res = await fetch("/api/auth/kakao/callback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "로그인 실패");
    }
    const data = await res.json();
    localStorage.setItem("edu_sync_token", data.token);
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    const token = localStorage.getItem("edu_sync_token");
    if (token) {
      await fetch(`/api/auth/logout?token=${encodeURIComponent(token)}`, {
        method: "POST",
      }).catch(() => {});
    }
    localStorage.removeItem("edu_sync_token");
    setUser(null);
  };

  const updateRole = async (role) => {
    const token = localStorage.getItem("edu_sync_token");
    const res = await fetch(
      `/api/auth/role?token=${encodeURIComponent(token)}&role=${role}`,
      {
        method: "POST",
      },
    );
    if (res.ok) {
      setUser((prev) => ({ ...prev, role }));
    }
  };

  // 데모 로그인 (카카오 API 키 없을 때 사용)
  const demoLogin = (role) => {
    const demoUser = {
      id: `demo_${role}`,
      name:
        role === "student"
          ? "김수강생"
          : role === "mentor"
            ? "이멘토"
            : "박조교",
      role,
      profile_image: "",
    };
    localStorage.setItem("edu_sync_token", `demo_${role}_token`);
    setUser(demoUser);
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, updateRole, demoLogin }}
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
