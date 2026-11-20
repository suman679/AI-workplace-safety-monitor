import { Badge, Banner } from "./ui";
import useFetch from "../hooks/useFetch";
import { PPE_LABELS } from "../utils/constants";

export const STATE_TONE = { SAFE: "green", WARNING: "amber", VIOLATION: "red" };
export const STATE_LABEL = { SAFE: "Safe", WARNING: "Warning", VIOLATION: "Violation" };

/** Explains honestly what the loaded AI model can and cannot do. */
export function ModelBanner() {
  const { data: s } = useFetch("/api/detection/status");
  if (!s) return null;
  if (!s.ml_installed)
    return <Banner tone="amber">AI libraries are not installed on the server. Stop the backend and run <code>pip install -r requirements-ml.txt</code>, then start it again.</Banner>;
  if (!s.model_file_found)
    return <Banner tone="amber">Demo mode: no PPE model was found at MODEL_PATH, so only people are detected and PPE is <b>not checked</b>. Train or download a PPE model (see ml-training/README.md) to detect helmets, vests and more.</Banner>;
  if (s.loaded && !s.ppe_capable)
    return <Banner tone="amber">The loaded model has no PPE classes, so PPE is not checked.</Banner>;
  return null;
}

export function SummaryCards({ items }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((i) => (
        <div key={i.label} className="card p-4">
          <div className="text-xs text-slate-400">{i.label}</div>
          <div className={`mt-1 text-2xl font-semibold ${i.tone || "text-white"}`}>{i.value ?? "—"}</div>
        </div>
      ))}
    </div>
  );
}

const cell = (v) => (v === true ? <span className="text-emerald-400">✓</span> : v === false ? <span className="text-red-400">✗</span> : <span className="text-slate-600" title="Not checked by this model">–</span>);

export function PersonTable({ persons }) {
  if (!persons?.length) return <p className="text-sm text-slate-400">No people detected.</p>;
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[620px]">
        <thead className="border-b border-white/10">
          <tr>{["Worker", "Status", "Helmet", "Vest", "Gloves", "Shoes", "Mask", "Score", "Issues"].map((h) => <th key={h} className="th">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {persons.map((p) => (
            <tr key={p.person_id}>
              <td className="td">#{p.person_id} <span className="text-xs text-slate-500">{Math.round(p.confidence * 100)}%</span></td>
              <td className="td"><Badge tone={STATE_TONE[p.state]}>{STATE_LABEL[p.state]}</Badge></td>
              <td className="td">{cell(p.helmet)}</td><td className="td">{cell(p.vest)}</td><td className="td">{cell(p.gloves)}</td>
              <td className="td">{cell(p.safety_shoes)}</td><td className="td">{cell(p.mask)}</td>
              <td className="td">{p.compliance_score == null ? "—" : `${p.compliance_score}%`}</td>
              <td className="td">{p.violations.length ? p.violations.join(", ") : p.not_checked.length ? <span className="text-slate-500">Not checked: {p.not_checked.join(", ")}</span> : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SiteRulesSelect({ sites, value, onChange, SelectField }) {
  return (
    <SelectField label="Site (decides which PPE is required)" value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Default rules (helmet + vest)</option>
      {sites?.map((s) => <option key={s.id} value={s.id}>{s.name}: {s.required_ppe.map((p) => PPE_LABELS[p]).join(", ") || "no PPE required"}</option>)}
    </SelectField>
  );
}
