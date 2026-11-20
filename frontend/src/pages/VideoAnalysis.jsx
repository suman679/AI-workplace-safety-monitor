import { Download, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { ModelBanner, SiteRulesSelect, SummaryCards } from "../components/DetectionBits";
import { Badge, Banner, PageHeader, SelectField } from "../components/ui";
import useFetch from "../hooks/useFetch";
import api, { errorMessage } from "../services/api";
import { PPE_LABELS } from "../utils/constants";

const TONE = { QUEUED: "slate", PROCESSING: "amber", COMPLETED: "green", FAILED: "red" };

function JobResult({ job }) {
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState("");
  const s = job.summary;

  useEffect(() => {
    let url;
    setVideoUrl("");
    if (job.status === "COMPLETED" && job.has_output) {
      api.get(`/api/detection/jobs/${job.id}/video`, { responseType: "blob" })
        .then((r) => { url = URL.createObjectURL(r.data); setVideoUrl(url); })
        .catch((e) => setError(errorMessage(e)));
    }
    return () => url && URL.revokeObjectURL(url);
  }, [job.id, job.status, job.has_output]);

  if (job.status === "FAILED") return <Banner>{job.error || "Video processing failed."}</Banner>;
  if (job.status !== "COMPLETED") {
    return (
      <div className="card p-5">
        <div className="mb-2 text-sm text-slate-300">{job.status === "QUEUED" ? "Waiting to start…" : `Processing… ${Math.round(job.progress)}%`}</div>
        <div className="h-2 overflow-hidden rounded bg-white/10"><div className="h-full bg-safety transition-all" style={{ width: `${job.progress}%` }} /></div>
      </div>
    );
  }
  return (
    <div className="space-y-5">
      {!s.ppe_checked && <Banner tone="amber">PPE was not checked (the model cannot detect PPE). Only people were counted.</Banner>}
      <SummaryCards items={[
        { label: "Total workers", value: s.total_workers },
        { label: "Workers with violations", value: s.workers_with_violations, tone: s.workers_with_violations ? "text-red-400" : undefined },
        { label: "Overall compliance", value: s.compliance_rate == null ? null : `${s.compliance_rate}%` },
        { label: "Safety score", value: s.safety_score == null ? null : `${s.safety_score}%` },
      ]} />
      <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-5">
        {Object.entries(s.violations_by_item).map(([item, n]) => (
          <div key={item} className="card p-3 text-center"><div className="text-xs text-slate-400">{PPE_LABELS[item]} violations</div><div className="mt-1 text-xl font-semibold text-white">{n}</div></div>
        ))}
      </div>
      <Banner>{error}</Banner>
      {videoUrl && (
        <div className="card p-3">
          <video src={videoUrl} controls className="mx-auto max-h-[65vh] rounded-lg" />
          <div className="mt-3 flex justify-end"><a className="btn" href={videoUrl} download={`${job.original_name.replace(/\.[^.]+$/, "")}-processed.mp4`}><Download size={16} /> Download processed video</a></div>
        </div>
      )}
    </div>
  );
}

export default function VideoAnalysis() {
  const { data: sites } = useFetch("/api/sites");
  const { data: jobs, reload } = useFetch("/api/detection/jobs");
  const [siteId, setSiteId] = useState("");
  const [file, setFile] = useState(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const active = jobs?.some((j) => j.status === "QUEUED" || j.status === "PROCESSING");
  useEffect(() => {
    if (!active) return;
    const t = setInterval(reload, 2000);
    return () => clearInterval(t);
  }, [active, reload]);

  const current = jobs?.find((j) => j.id === selected) || jobs?.[0];

  async function upload(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    if (siteId) form.append("site_id", siteId);
    try {
      const { data } = await api.post("/api/detection/video", form);
      setSelected(data.id);
      setFile(null);
      e.target.reset();
      reload();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Video Analysis" subtitle="Upload a video; it is processed in the background and annotated" />
      <ModelBanner />
      <Banner>{error}</Banner>
      <form onSubmit={upload} className="card mb-6 grid items-end gap-4 p-5 md:grid-cols-[1fr_1fr_auto]">
        <SiteRulesSelect sites={sites} value={siteId} onChange={setSiteId} SelectField={SelectField} />
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-400">Video (MP4, AVI, MOV, MKV)</span>
          <input type="file" accept=".mp4,.avi,.mov,.mkv" required onChange={(e) => setFile(e.target.files[0])} className="input file:mr-3 file:rounded file:border-0 file:bg-white/10 file:px-2 file:py-1 file:text-slate-200" />
        </label>
        <button className="btn-accent" disabled={busy || !file}><Upload size={16} /> {busy ? "Uploading…" : "Upload & analyze"}</button>
      </form>

      {jobs?.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
          <div className="card max-h-[70vh] divide-y divide-white/5 overflow-y-auto">
            {jobs.map((j) => (
              <button key={j.id} onClick={() => setSelected(j.id)} className={`block w-full px-4 py-3 text-left hover:bg-white/5 ${current?.id === j.id ? "bg-white/5" : ""}`}>
                <div className="truncate text-sm text-white">{j.original_name}</div>
                <div className="mt-1 flex items-center justify-between text-xs text-slate-500"><span>{new Date(j.created_at).toLocaleString()}</span><Badge tone={TONE[j.status]}>{j.status}</Badge></div>
              </button>
            ))}
          </div>
          {current && <JobResult job={current} />}
        </div>
      )}
    </div>
  );
}
