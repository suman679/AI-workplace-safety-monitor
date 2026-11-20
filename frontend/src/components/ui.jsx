const TONES = {
  green: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  amber: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  red: "bg-red-500/15 text-red-300 border-red-500/30",
  slate: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  blue: "bg-sky-500/15 text-sky-300 border-sky-500/30",
};

export function Badge({ tone = "slate", children }) {
  return <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${TONES[tone]}`}>{children}</span>;
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-white">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function Banner({ children, tone = "red" }) {
  if (!children) return null;
  return <div role="alert" className={`mb-4 rounded-lg border px-3 py-2 text-sm ${TONES[tone]}`}>{children}</div>;
}

export function EmptyState({ title, text, action }) {
  return (
    <div className="card grid place-items-center px-6 py-14 text-center">
      <h3 className="font-medium text-white">{title}</h3>
      {text && <p className="mt-1 max-w-md text-sm text-slate-400">{text}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Loading() {
  return <div className="py-10 text-center text-sm text-slate-500">Loading…</div>;
}

export function TableShell({ head, children }) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[640px]">
        <thead className="border-b border-white/10"><tr>{head.map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
        <tbody className="divide-y divide-white/5">{children}</tbody>
      </table>
    </div>
  );
}

export function SelectField({ label, children, ...props }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-slate-400">{label}</span>
      <select className="input" {...props}>{children}</select>
    </label>
  );
}
