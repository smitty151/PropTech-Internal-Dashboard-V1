import { useEffect, useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [state, setState] = useState({ status: "loading", message: "Verifying your email…" });

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setState({ status: "error", message: "Missing verification token." });
      return;
    }
    (async () => {
      try {
        await api.get("/auth/verify-email", { params: { token } });
        setState({ status: "ok", message: "Email verified. You can now sign in." });
        setTimeout(() => navigate("/login", { replace: true }), 1800);
      } catch (e) {
        setState({ status: "error", message: formatApiErrorDetail(e.response?.data?.detail) || e.message });
      }
    })();
  }, [params, navigate]);

  const Icon = state.status === "ok" ? CheckCircle2 : state.status === "error" ? XCircle : Loader2;
  const color = state.status === "ok" ? "var(--ph-success)" : state.status === "error" ? "var(--ph-accent)" : "var(--ph-ink-2)";

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--ph-bg-2)]" data-testid="verify-page">
      <div className="panel p-10 max-w-md w-full text-center">
        <Icon size={36} strokeWidth={1.5} className={state.status === "loading" ? "animate-spin mx-auto" : "mx-auto"} style={{ color }} />
        <h1 className="font-display text-2xl font-bold mt-6 tracking-tight">
          {state.status === "ok" ? "All set." : state.status === "error" ? "Verification failed." : "Just a moment…"}
        </h1>
        <p className="text-sm text-[var(--ph-ink-2)] mt-3" data-testid="verify-message">{state.message}</p>
        <Link to="/login" className="btn-outline mt-8 inline-block" data-testid="verify-login-link">Back to sign in</Link>
      </div>
    </div>
  );
}
