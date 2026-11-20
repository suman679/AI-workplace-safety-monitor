import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import Modal from "../components/Modal";
import { Banner, Badge, EmptyState, Loading, PageHeader, SelectField, TableShell } from "../components/ui";
import { Field } from "../components/AuthShell";
import useFetch from "../hooks/useFetch";
import usePermissions from "../hooks/usePermissions";
import api, { errorMessage } from "../services/api";
import { PPE_LABELS, PPE_ORDER, SITE_TYPES } from "../utils/constants";

function SiteForm({ site, onDone, onClose }) {
  const [form, setForm] = useState({
    name: site?.name || "",
    site_type: site?.site_type || "CONSTRUCTION",
    address: site?.address || "",
    safety_threshold: site?.safety_threshold ?? 80,
    required_ppe: site?.required_ppe || [],
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (item) => set("required_ppe", form.required_ppe.includes(item) ? form.required_ppe.filter((i) => i !== item) : [...form.required_ppe, item]);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = { ...form, address: form.address || null, safety_threshold: Number(form.safety_threshold) };
    try {
      if (site) await api.put(`/api/sites/${site.id}`, payload);
      else await api.post("/api/sites", { ...payload, required_ppe: form.required_ppe.length ? form.required_ppe : undefined });
      onDone();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <Banner>{error}</Banner>
      <Field label="Site name" required minLength={2} value={form.name} onChange={(e) => set("name", e.target.value)} />
      <SelectField label="Site type" value={form.site_type} onChange={(e) => set("site_type", e.target.value)}>
        {SITE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
      </SelectField>
      <Field label="Address" value={form.address} onChange={(e) => set("address", e.target.value)} />
      <Field label="Safety threshold (%)" type="number" min={0} max={100} required value={form.safety_threshold} onChange={(e) => set("safety_threshold", e.target.value)} />
      <fieldset>
        <legend className="mb-2 text-xs font-medium text-slate-400">Required PPE</legend>
        <div className="grid grid-cols-2 gap-2">
          {PPE_ORDER.map((item) => (
            <label key={item} className="flex items-center gap-2 text-sm text-slate-300">
              <input type="checkbox" checked={form.required_ppe.includes(item)} onChange={() => toggle(item)} className="accent-amber-500" />
              {PPE_LABELS[item]}
            </label>
          ))}
        </div>
        {!site && <p className="mt-2 text-xs text-slate-500">Leave all unchecked to use the defaults for this site type.</p>}
      </fieldset>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn" onClick={onClose}>Cancel</button>
        <button className="btn-accent" disabled={busy}>{busy ? "Saving…" : site ? "Save changes" : "Create site"}</button>
      </div>
    </form>
  );
}

export default function Sites() {
  const { data: sites, loading, error, reload } = useFetch("/api/sites");
  const { canWrite, canDelete } = usePermissions();
  const [editing, setEditing] = useState(undefined); // undefined = closed, null = new
  const [actionError, setActionError] = useState("");

  async function remove(site) {
    if (!window.confirm(`Delete "${site.name}"? Its cameras will be deleted and its workers unassigned.`)) return;
    try {
      await api.delete(`/api/sites/${site.id}`);
      reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  const add = canWrite && <button className="btn-accent" onClick={() => setEditing(null)}><Plus size={16} /> Add site</button>;

  return (
    <div>
      <PageHeader title="Sites" subtitle="Locations you monitor, each with its own required PPE" action={add} />
      <Banner>{error || actionError}</Banner>
      {loading && !sites ? <Loading /> : sites?.length === 0 ? (
        <EmptyState title="No sites yet" text="Create your first site to start adding cameras and workers." action={add} />
      ) : sites && (
        <TableShell head={["Site", "Type", "Required PPE", "Threshold", "Cameras", "Workers", ""]}>
          {sites.map((s) => (
            <tr key={s.id}>
              <td className="td"><div className="font-medium text-white">{s.name}</div><div className="text-xs text-slate-500">{s.address}</div></td>
              <td className="td">{SITE_TYPES.find((t) => t.value === s.site_type)?.label}</td>
              <td className="td"><div className="flex flex-wrap gap-1">{s.required_ppe.length ? s.required_ppe.map((p) => <Badge key={p} tone="blue">{PPE_LABELS[p]}</Badge>) : <span className="text-slate-500">None</span>}</div></td>
              <td className="td">{s.safety_threshold}%</td>
              <td className="td">{s.camera_count}</td>
              <td className="td">{s.worker_count}</td>
              <td className="td"><div className="flex justify-end gap-2">
                {canWrite && <button className="btn" aria-label={`Edit ${s.name}`} onClick={() => setEditing(s)}><Pencil size={14} /></button>}
                {canDelete && <button className="btn-danger" aria-label={`Delete ${s.name}`} onClick={() => remove(s)}><Trash2 size={14} /></button>}
              </div></td>
            </tr>
          ))}
        </TableShell>
      )}
      {editing !== undefined && (
        <Modal title={editing ? "Edit site" : "Add site"} onClose={() => setEditing(undefined)}>
          <SiteForm site={editing} onClose={() => setEditing(undefined)} onDone={() => { setEditing(undefined); reload(); }} />
        </Modal>
      )}
    </div>
  );
}
