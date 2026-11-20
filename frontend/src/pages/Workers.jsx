import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Field } from "../components/AuthShell";
import Modal from "../components/Modal";
import { Badge, Banner, EmptyState, Loading, PageHeader, SelectField, TableShell } from "../components/ui";
import useFetch, { useDebounced } from "../hooks/useFetch";
import usePermissions from "../hooks/usePermissions";
import api, { errorMessage } from "../services/api";

function WorkerForm({ worker, sites, onDone, onClose }) {
  const [form, setForm] = useState({
    employee_code: worker?.employee_code || "",
    full_name: worker?.full_name || "",
    site_id: worker?.site_id || "",
    department: worker?.department || "",
    is_active: worker?.is_active ?? true,
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = { ...form, site_id: form.site_id || null, department: form.department || null };
    try {
      if (worker) await api.put(`/api/workers/${worker.id}`, payload);
      else await api.post("/api/workers", payload);
      onDone();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <Banner>{error}</Banner>
      <Field label="Employee code" required value={form.employee_code} onChange={set("employee_code")} />
      <Field label="Full name" required minLength={2} value={form.full_name} onChange={set("full_name")} />
      <SelectField label="Assigned site" value={form.site_id} onChange={set("site_id")}>
        <option value="">Unassigned</option>
        {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </SelectField>
      <Field label="Department" value={form.department} onChange={set("department")} />
      <label className="flex items-center gap-2 text-sm text-slate-300">
        <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} className="accent-amber-500" /> Active
      </label>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn" onClick={onClose}>Cancel</button>
        <button className="btn-accent" disabled={busy}>{busy ? "Saving…" : worker ? "Save changes" : "Add worker"}</button>
      </div>
    </form>
  );
}

export default function Workers() {
  const [search, setSearch] = useState("");
  const [siteFilter, setSiteFilter] = useState("");
  const q = useDebounced(search);
  const { data: sites } = useFetch("/api/sites");
  const { data: workers, loading, error, reload } = useFetch("/api/workers", { search: q || undefined, site_id: siteFilter || undefined });
  const { canWrite, canDelete } = usePermissions();
  const [editing, setEditing] = useState(undefined);
  const [actionError, setActionError] = useState("");

  async function remove(w) {
    if (!window.confirm(`Delete worker "${w.full_name}"?`)) return;
    try {
      await api.delete(`/api/workers/${w.id}`);
      reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  const add = canWrite && <button className="btn-accent" onClick={() => setEditing(null)}><Plus size={16} /> Add worker</button>;

  return (
    <div>
      <PageHeader title="Workers" subtitle="Your workforce roster" action={add} />
      <Banner>{error || actionError}</Banner>
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="w-64"><Field label="Search name or code" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
        <div className="w-56">
          <SelectField label="Site" value={siteFilter} onChange={(e) => setSiteFilter(e.target.value)}>
            <option value="">All sites</option>
            {sites?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </SelectField>
        </div>
      </div>
      {loading && !workers ? <Loading /> : workers?.length === 0 ? (
        <EmptyState title="No workers found" text={q || siteFilter ? "Try a different search or filter." : "Add workers to track them against safety incidents."} action={!q && !siteFilter && add} />
      ) : workers && (
        <TableShell head={["Code", "Name", "Site", "Department", "Status", ""]}>
          {workers.map((w) => (
            <tr key={w.id}>
              <td className="td">{w.employee_code}</td>
              <td className="td font-medium text-white">{w.full_name}</td>
              <td className="td">{w.site_name || <span className="text-slate-500">Unassigned</span>}</td>
              <td className="td">{w.department || "—"}</td>
              <td className="td"><Badge tone={w.is_active ? "green" : "slate"}>{w.is_active ? "Active" : "Inactive"}</Badge></td>
              <td className="td"><div className="flex justify-end gap-2">
                {canWrite && <button className="btn" aria-label={`Edit ${w.full_name}`} onClick={() => setEditing(w)}><Pencil size={14} /></button>}
                {canDelete && <button className="btn-danger" aria-label={`Delete ${w.full_name}`} onClick={() => remove(w)}><Trash2 size={14} /></button>}
              </div></td>
            </tr>
          ))}
        </TableShell>
      )}
      {editing !== undefined && sites && (
        <Modal title={editing ? "Edit worker" : "Add worker"} onClose={() => setEditing(undefined)}>
          <WorkerForm worker={editing} sites={sites} onClose={() => setEditing(undefined)} onDone={() => { setEditing(undefined); reload(); }} />
        </Modal>
      )}
    </div>
  );
}
