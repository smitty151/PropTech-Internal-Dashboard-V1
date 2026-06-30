import { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Building2 } from "lucide-react";

export default function Login() {
  const { login, error, user, resendVerification } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("admin@placeholder.in");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [resent, setResent] = useState(false);

  useEffect(() => {
    if (user && user !== false) {
      navigate("/app", { replace: true });
    }
  }, [user, navigate]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const ok = await login(email, password);
    setLoading(false);
    if (ok) navigate(location.state?.from || "/app", { replace: true });
  };

  const onResend = async () => {
    const ok = await resendVerification(email);
    if (ok) setResent(true);
  };

  const isUnverified = error && /verify your email/i.test(error);

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      <div className="hidden lg:block relative border-r border-[var(--ph-line)]">
        <img
          src="https://images.unsplash.com/photo-1601039913996-d74e58095333?crop=entropy&cs=srgb&fm=jpg&q=85"
          alt="Commercial building India"
          className="w-full h-full object-cover grayscale-[15%]"
        />
        <div className="absolute inset-0 bg-white/10" />
        <div className="absolute top-8 left-8 flex items-center gap-2">
          <Building2 size={18} strokeWidth={1.5} />
          <span className="font-display font-bold">PlaceHolder</span>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <form onSubmit={onSubmit} className="w-full max-w-sm" data-testid="login-form">
          <div className="tiny-caps text-[var(--ph-muted)]">Sign in</div>
          <h1 className="font-display text-3xl font-bold mt-2 tracking-tight">Welcome back.</h1>
          <p className="text-sm text-[var(--ph-ink-2)] mt-2">Use the demo admin to explore Phase 1.</p>

          <label className="tiny-caps block mt-8 mb-2">Email</label>
          <input
            data-testid="login-email-input"
            type="email"
            className="input-ph"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label className="tiny-caps block mt-4 mb-2">Password</label>
          <input
            data-testid="login-password-input"
            type="password"
            className="input-ph"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && (
            <div data-testid="login-error" className="mt-4 text-sm text-[var(--ph-accent)]">
              {error}
              {isUnverified && (
                <div className="mt-2">
                  {resent ? (
                    <span className="text-[var(--ph-ink-2)]" data-testid="login-resent">Verification email re-sent. Check your inbox.</span>
                  ) : (
                    <button type="button" onClick={onResend} className="underline" data-testid="login-resend">
                      Resend verification email
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          <button
            data-testid="login-submit-btn"
            type="submit"
            disabled={loading}
            className="btn-primary w-full mt-6 disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <div className="mt-6 text-sm text-[var(--ph-ink-2)]">
            New here?{" "}
            <Link to="/register" className="underline font-medium" data-testid="login-to-register">
              Create an account
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
