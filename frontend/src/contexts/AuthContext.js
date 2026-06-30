import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking, object = logged-in, false = anonymous
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      setUser(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    setError("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setUser(data);
      return true;
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      return false;
    }
  };

  const register = async (payload) => {
    setError("");
    try {
      const { data } = await api.post("/auth/register", payload);
      // Hard-gate: do NOT auto-login. Backend returns { ok, email, email_verified:false }.
      return { ok: true, ...data };
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      return { ok: false };
    }
  };

  const resendVerification = async (email) => {
    try {
      await api.post("/auth/resend-verification", { email });
      return true;
    } catch (e) {
      console.warn("Resend verification failed:", e);
      return false;
    }
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (err) {
      // logout is best-effort: cookies may already be cleared / network down.
      // Surface the error to the console so it isn't silently swallowed.
      console.warn("Logout request failed (clearing client session anyway):", err);
    }
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, error, login, register, logout, refresh, resendVerification }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
