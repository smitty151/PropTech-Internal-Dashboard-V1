import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Plus, Trash2, Calculator as CalcIcon } from "lucide-react";

const DebtTrancheRow = ({ tranche, index, onChange, onRemove }) => (
  <div className="grid grid-cols-[1fr_140px_120px_40px] gap-2 items-center" data-testid={`calc-debt-row-${index}`}>
    <input className="input-ph" value={tranche.name} onChange={(e) => onChange(index, "name", e.target.value)} />
    <input className="input-ph font-mono-ph" type="number" placeholder="Amount ₹Cr" value={tranche.amount} onChange={(e) => onChange(index, "amount", e.target.value)} />
    <input className="input-ph font-mono-ph" type="number" step="0.1" placeholder="Rate %" value={tranche.rate} onChange={(e) => onChange(index, "rate", e.target.value)} />
    <button onClick={() => onRemove(index)} className="p-2 hover:text-[var(--ph-accent)]" data-testid={`calc-remove-debt-${index}`}>
      <Trash2 size={14} />
    </button>
  </div>
);

const ResultPanel = ({ result }) => {
  if (!result) {
    return <div className="mt-8 text-sm text-[var(--ph-muted)]">Run the calculator to see your blended WACC and capital weights.</div>;
  }
  return (
    <>
      <div className="mt-6 panel p-6 text-center">
        <div className="tiny-caps text-[var(--ph-muted)]">WACC / Discount Rate</div>
        <div className="font-display text-5xl font-bold mt-3 tracking-tight" data-testid="calc-wacc">
          {result.wacc.toFixed(2)}<span className="text-2xl">%</span>
        </div>
        <div className="text-xs text-[var(--ph-muted)] mt-3 font-mono-ph">
          Ke source: {result.cost_of_equity_source === "reit" ? "REIT-anchored" : "Manual input"}
        </div>
      </div>
      <div className="mt-6 panel divide-y divide-[var(--ph-line)]">
        <Row k="Total capital" v={`₹${result.total_capital_inr_cr.toFixed(0)} Cr`} />
        <Row k="Weight of Equity" v={`${(result.weights.equity * 100).toFixed(1)}%`} />
        <Row k="Weight of Debt" v={`${(result.weights.debt * 100).toFixed(1)}%`} />
        <Row k="Cost of Equity (Ke)" v={`${result.cost_of_equity.toFixed(2)}%`} />
        <Row k="Pre-tax Cost of Debt" v={`${result.weighted_cost_of_debt.toFixed(2)}%`} />
        <Row k="After-tax Cost of Debt" v={`${result.after_tax_cost_of_debt.toFixed(2)}%`} />
      </div>
      <div className="mt-6 text-xs text-[var(--ph-ink-2)] leading-relaxed">
        Use this discount rate to NPV your project cashflows or to bound capitalisation rates when valuing the underlying asset.
      </div>
    </>
  );
};

export default function Calculator() {
  const [reits, setReits] = useState([]);
  const [equity, setEquity] = useState(300);
  const [costOfEquity, setCostOfEquity] = useState(12.5);
  const [taxRate, setTaxRate] = useState(25.17);
  const [reitSymbol, setReitSymbol] = useState("");
  const [spread, setSpread] = useState(4.0);
  const [debt, setDebt] = useState([
    { name: "Construction Loan", amount: 400, rate: 9.5 },
    { name: "Mezzanine", amount: 150, rate: 13.0 },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const { data } = await api.get("/reits");
      setReits(data);
    })();
  }, []);

  const setDebtField = (i, k, v) => {
    const next = [...debt];
    next[i] = { ...next[i], [k]: k === "name" ? v : Number(v) };
    setDebt(next);
  };

  const addDebt = () =>
    setDebt([
      ...debt,
      { id: `d-${Date.now()}`, name: `Tranche ${debt.length + 1}`, amount: 100, rate: 10 },
    ]);
  const removeDebt = (i) => setDebt(debt.filter((_, idx) => idx !== i));

  const compute = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/calculator/wacc", {
        equity_amount: Number(equity),
        cost_of_equity: Number(costOfEquity),
        tax_rate: Number(taxRate),
        debt: debt.map((d) => ({ ...d, amount: Number(d.amount), rate: Number(d.rate) })),
        reit_symbol: reitSymbol || null,
        spread_over_reit: Number(spread),
      });
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="calculator-page">
      <div className="px-6 lg:px-8 py-6 border-b border-[var(--ph-line)]">
        <div className="tiny-caps text-[var(--ph-muted)]">Cost of Capital</div>
        <h1 className="font-display text-2xl lg:text-3xl font-bold mt-2 tracking-tight">
          REIT-anchored WACC & discount rate.
        </h1>
        <p className="text-sm text-[var(--ph-ink-2)] mt-3 max-w-2xl">
          Build your debt stack, optionally anchor your cost of equity to a listed Indian REIT yield
          plus a project-risk spread, and get a defensible blended discount rate for valuation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px]">
        {/* Form */}
        <div className="p-6 lg:p-8 border-r border-[var(--ph-line)]">
          {/* Equity */}
          <div className="mb-8">
            <div className="tiny-caps text-[var(--ph-muted)] mb-3">Equity</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-[var(--ph-ink-2)]">Equity amount (₹ Cr)</label>
                <input data-testid="calc-equity-amount" type="number" className="input-ph mt-1" value={equity} onChange={(e) => setEquity(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-[var(--ph-ink-2)]">Manual cost of equity (%)</label>
                <input data-testid="calc-cost-of-equity" type="number" step="0.1" className="input-ph mt-1" value={costOfEquity} onChange={(e) => setCostOfEquity(e.target.value)} />
              </div>
            </div>

            <div className="mt-4 p-4 border border-[var(--ph-line)] bg-[var(--ph-bg-2)]">
              <div className="tiny-caps text-[var(--ph-muted)]">Anchor to REIT (optional — overrides manual Ke)</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                <select data-testid="calc-reit-select" className="input-ph" value={reitSymbol} onChange={(e) => setReitSymbol(e.target.value)}>
                  <option value="">— None (use manual Ke) —</option>
                  {reits.map((r) => (
                    <option key={r.symbol} value={r.symbol}>{r.name} ({r.dividend_yield}% yld)</option>
                  ))}
                </select>
                <div>
                  <label className="text-xs text-[var(--ph-ink-2)]">Project spread over REIT (%)</label>
                  <input data-testid="calc-spread" type="number" step="0.1" className="input-ph mt-1" value={spread} onChange={(e) => setSpread(e.target.value)} />
                </div>
              </div>
            </div>
          </div>

          {/* Debt tranches */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <div className="tiny-caps text-[var(--ph-muted)]">Debt tranches</div>
              <button data-testid="calc-add-debt" onClick={addDebt} className="text-sm flex items-center gap-1 underline">
                <Plus size={14} /> Add tranche
              </button>
            </div>
            <div className="space-y-2">
              {debt.map((d, i) => (
                <DebtTrancheRow key={d.id} tranche={d} index={i} onChange={setDebtField} onRemove={removeDebt} />
              ))}
            </div>
          </div>

          <div className="mb-8">
            <label className="text-xs text-[var(--ph-ink-2)]">Corporate tax rate (%)</label>
            <input data-testid="calc-tax-rate" type="number" step="0.01" className="input-ph mt-1 !w-40" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} />
          </div>

          <button data-testid="calc-compute" onClick={compute} disabled={loading} className="btn-primary flex items-center gap-2">
            <CalcIcon size={16} /> {loading ? "Computing…" : "Compute WACC"}
          </button>
        </div>

        {/* Result */}
        <div className="bg-[var(--ph-bg-2)] p-6 lg:p-8" data-testid="calc-result">
          <div className="tiny-caps text-[var(--ph-muted)]">Output</div>
          <div className="font-display text-xl font-bold">Discount rate</div>
          <ResultPanel result={result} />
        </div>
      </div>
    </div>
  );
}

const Row = ({ k, v }) => (
  <div className="flex justify-between px-5 py-3 text-sm">
    <span className="text-[var(--ph-ink-2)]">{k}</span>
    <span className="font-mono-ph font-medium">{v}</span>
  </div>
);
