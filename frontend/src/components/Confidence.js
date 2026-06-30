import { ShieldCheck, Globe } from "lucide-react";

/** Returns "verified" | "unverified" based on source string. */
export function confidenceOf(source) {
  if (!source) return "unverified";
  if (/^(NHAI|Sub-Registrar)/.test(source)) return "verified";
  return "unverified";
}

export function ConfidenceBadge({ source }) {
  const level = confidenceOf(source);
  if (level === "verified") {
    return (
      <span
        title={source}
        data-testid="badge-verified"
        className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] border border-[var(--ph-success)] text-[var(--ph-success)] font-mono-ph"
      >
        <ShieldCheck size={10} /> VERIFIED
      </span>
    );
  }
  return (
    <span
      title={source || "Unknown"}
      data-testid="badge-unverified"
      className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] border border-[var(--ph-muted)] text-[var(--ph-muted)] font-mono-ph"
    >
      <Globe size={10} /> OPEN
    </span>
  );
}

export function ConfidenceToggle({ value, onChange, testId = "confidence-toggle" }) {
  return (
    <div className="flex items-stretch border border-[var(--ph-line)]" data-testid={testId}>
      <button
        onClick={() => onChange(false)}
        data-testid={`${testId}-all`}
        className={`px-3 py-2 text-xs font-medium flex items-center gap-1.5 ${
          !value ? "bg-[var(--ph-ink)] text-white" : "bg-white text-[var(--ph-ink-2)] hover:bg-[var(--ph-bg-2)]"
        }`}
      >
        <Globe size={12} /> All sources
      </button>
      <button
        onClick={() => onChange(true)}
        data-testid={`${testId}-verified`}
        className={`px-3 py-2 text-xs font-medium flex items-center gap-1.5 border-l border-[var(--ph-line)] ${
          value ? "bg-[var(--ph-success)] text-white" : "bg-white text-[var(--ph-ink-2)] hover:bg-[var(--ph-bg-2)]"
        }`}
      >
        <ShieldCheck size={12} /> Verified only
      </button>
    </div>
  );
}
