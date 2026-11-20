import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Field } from "../components/AuthShell";
import Modal from "../components/Modal";
import { Badge, Banner, EmptyState, Loading, PageHeader, SelectField, TableShell } from "../components/ui";
import useFetch from "../hooks/useFetch";
import usePermissions from "../hooks/usePermissions";
import api, { errorMessage } from "../services/api";
import { CAMERA_STATUSES, SOURCE_TYPES, STATUS_TONE } from "../utils/constants";

function CameraForm({ camera, sites, onDone, onClose }) {
  const [form, setForm] = useState({
    name: camera?.name || "",
    camera_code: camera?.camera_code || "",
    site_id: camera?.site_id || sites[0]?.id || "",
    location: camera?.location || "",
    source_type: camera?.source_type || "WEBCAM",
    stream_url: camera?.stream_url || "",
    status: camera?.status || "OFFLINE",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = { ...form, location: form.location || null, stream_url: form.source_type === "RTSP" ? form.stream_url : null };
    try {
      if (camera) await api.put(`/api/cameras/${camera.id}`, payload);
      else await api.post("/api/cameras", payload);
      onDone();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <Banner>{error}</Banner>
      <Field label="Camera name" required minLength={2} value={form.name} onChange={set("name")} />
      <Field label="Camera ID (unique, e.g. CAM-01)" required value={form.camera_code} onChange={set("camera_code")} />
      <SelectField label="Site" required value={form.site_id} onChange={set("site_id")}>
        {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </SelectField>
      <Field label="Location (e.g. Main gate)" value={form.location} onChange={set("location")} />
      <SelectField label="Source" value={form.source_type} onChange={set("source_type")}>
        {SOURCE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
      </SelectField>
      {form.source_type === "RTSP" && <Field label="Stream URL" placeholder="rtsp://user:pass@192.168.1.10/stream" required value={form.stream_url} onChange={set("stream_url")} />}
      <SelectField label="Status" value={form.status} onChange={set("status")}>
        {CAMERA_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
      </SelectField>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn" onClick={onClose}>Cancel</button>
        <button className="btn-accent" disabled={busy}>{busy ? "Saving…" : camera ? "Save changes" : "Add camera"}</button>
      </div>
    </form>
  );
}

export default function Cameras() {
  const [siteFilter, setSiteFilter] = useState("");
  const { data: sites } = useFetch("/api/sites");
  const { data: cameras, loading, error, reload } = useFetch("/api/cameras", { site_id: siteFilter || undefined });
  const { canWrite, canDelete } = usePermissions();
  const [editing, setEditing] = useState(undefined);
  const [actionError, setActionError] = useState("");

  async function remove(c) {
    if (!window.confirm(`Delete camera "${c.name}"?`)) return;
    try {
      await api.delete(`/api/cameras/${c.id}`);
      reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  const add = canWrite && sites?.length > 0 && <button className="btn-accent" onClick={() => setEditing(null)}><Plus size={16} /> Add camera</button>;

  return (
    <div>
      <PageHeader title="Cameras" subtitle="Webcams and uploaded-video sources (RTSP/CCTV can be registered for later)" action={add} />
      <Banner>{error || actionError}</Banner>
      {sites?.length === 0 ? (
        <EmptyState title="Create a site first" text="Every camera belongs to a site." action={<Link to="/sites" className="btn-accent">Go to Sites</Link>} />
      ) : (
        <>
          <div className="mb-4 w-60">
            <SelectField label="Filter by site" value={siteFilter} onChange={(e) => setSiteFilter(e.target.value)}>
              <option value="">All sites</option>
              {sites?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </SelectField>
          </div>
          {loading && !cameras ? <Loading /> : cameras?.length === 0 ? (
            <EmptyState title="No cameras yet" text="Add a webcam or video source for a site." action={add} />
          ) : cameras && (
            <TableShell head={["Camera", "Site", "Source", "Status", "Last active", ""]}>
              {cameras.map((c) => (
                <tr key={c.id}>
                  <td className="td"><div className="font-medium text-white">{c.name}</div><div className="text-xs text-slate-500">{c.camera_code}{c.location ? ` · ${c.location}` : ""}</div></td>
                  <td className="td">{c.site_name}</td>
                  <td className="td">{SOURCE_TYPES.find((t) => t.value === c.source_type)?.label}</td>
                  <td className="td"><Badge tone={STATUS_TONE[c.status]}>{c.status}</Badge></td>
                  <td className="td">{c.last_active_at ? new Date(c.last_active_at).toLocaleString() : "Never"}</td>
                  <td className="td"><div className="flex justify-end gap-2">
                    {canWrite && <button className="btn" aria-label={`Edit ${c.name}`} onClick={() => setEditing(c)}><Pencil size={14} /></button>}
                    {canDelete && <button className="btn-danger" aria-label={`Delete ${c.name}`} onClick={() => remove(c)}><Trash2 size={14} /></button>}
                  </div></td>
                </tr>
              ))}
            </TableShell>
          )}
        </>
      )}
      {editing !== undefined && sites && (
        <Modal title={editing ? "Edit camera" : "Add camera"} onClose={() => setEditing(undefined)}>
          <CameraForm camera={editing} sites={sites} onClose={() => setEditing(undefined)} onDone={() => { setEditing(undefined); reload(); }} />
        </Modal>
      )}
    </div>
  );
}
