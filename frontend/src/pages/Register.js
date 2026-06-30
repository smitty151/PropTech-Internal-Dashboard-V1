import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Building2 } from "lucide-react";

export default function Register() {
  const { register, error } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", company: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await register(form);
    setLoading(false);
    if (res.ok) setDone({ email: res.email || form.email });
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--ph-bg-2)]" data-testid="register-sent">
        <div className="panel p-10 max-w-md w-full text-center">
          <div className="tiny-caps text-[var(--ph-muted)]">Check your inbox</div>
          <h1 className="font-display text-2xl font-bold mt-3 tracking-tight">Verify your email.</h1>
          <p className="text-sm text-[var(--ph-ink-2)] mt-4">
            We&apos;ve sent a verification link to <b>{done.email}</b>. Click the link to activate your account, then sign in.
          </p>
          <p className="text-xs text-[var(--ph-muted)] mt-3">Link expires in 6 hours.</p>
          <button onClick={() => navigate("/login")} className="btn-outline mt-8" data-testid="register-done-to-login">Go to sign in</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      <div className="flex items-center justify-center p-8 order-2 lg:order-1">
        <form onSubmit={onSubmit} className="w-full max-w-sm" data-testid="register-form">
          <div className="tiny-caps text-[var(--ph-muted)]">Get started</div>
          <h1 className="font-display text-3xl font-bold mt-2 tracking-tight">Create your account.</h1>
          <p className="text-sm text-[var(--ph-ink-2)] mt-2">Phase 1 access is free. No credit card needed.</p>

          <label className="tiny-caps block mt-8 mb-2">Full name</label>
          <input data-testid="register-name-input" className="input-ph" value={form.name} onChange={set("name")} required />

          <label className="tiny-caps block mt-4 mb-2">Company</label>
          <input data-testid="register-company-input" className="input-ph" value={form.company} onChange={set("company")} placeholder="Optional" />

          <label className="tiny-caps block mt-4 mb-2">Email</label>
          <input data-testid="register-email-input" type="email" className="input-ph" value={form.email} onChange={set("email")} required />

          <label className="tiny-caps block mt-4 mb-2">Password</label>
          <input data-testid="register-password-input" type="password" className="input-ph" value={form.password} onChange={set("password")} minLength={6} required />

          {error && (
            <div data-testid="register-error" className="mt-4 text-sm text-[var(--ph-accent)]">
              {error}
            </div>
          )}

          <button data-testid="register-submit-btn" type="submit" disabled={loading} className="btn-primary w-full mt-6 disabled:opacity-60">
            {loading ? "Creating account…" : "Create account"}
          </button>

          <div className="mt-6 text-sm text-[var(--ph-ink-2)]">
            Already registered?{" "}
            <Link to="/login" className="underline font-medium" data-testid="register-to-login">
              Sign in
            </Link>
          </div>
        </form>
      </div>

      <div className="hidden lg:block relative border-l border-[var(--ph-line)] order-1 lg:order-2">
        <img
          src="https://images.unsplash.com/photo-1653299311171-31939b3b84b0?crop=entropy&cs=srgb&fm=jpg&q=85"
          alt="Infrastructure"
          className="w-full h-full object-cover grayscale-[15%]"
        />
        <div className="absolute inset-0 bg-white/10" />
        <div className="absolute top-8 right-8 flex items-center gap-2">
          <Building2 size={18} strokeWidth={1.5} />
          <span className="font-display font-bold">PlaceHolder</span>
        </div>
      </div>
    </div>
  );
}
