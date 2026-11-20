import { Download, ScanSearch } from "lucide-react";
import { useState } from "react";
import { ModelBanner, PersonTable, SiteRulesSelect, SummaryCards } from "../components/DetectionBits";
import { Banner, PageHeader, SelectField } from "../components/ui";
import useFetch from "../hooks/useFetch";
import api, { errorMessage } from "../services/api";

export default function ImageAnalysis() {
  const { data: sites } = useFetch("/api/sites");
  const [siteId, setSiteId] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function analyze(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    if (siteId) form.append("site_id", siteId);
    try {
      const { data } = await api.post("/api/detection/image", form);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const s = result?.summary;
  return (
    <div>
      <PageHeader title="Image Analysis" subtitle="Upload a photo to check PPE compliance" />
      <ModelBanner />
      <Banner>{error}</Banner>
      <form onSubmit={analyze} className="card mb-6 grid items-end gap-4 p-5 md:grid-cols-[1fr_1fr_auto]">
        <SiteRulesSelect sites={sites} value={siteId} onChange={setSiteId} SelectField={SelectField} />
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-400">Image (JPG, PNG, WEBP)</span>
          <input type="file" accept=".jpg,.jpeg,.png,.webp,.bmp" required onChange={(e) => setFile(e.target.files[0])} className="input file:mr-3 file:rounded file:border-0 file:bg-white/10 file:px-2 file:py-1 file:text-slate-200" />
        </label>
        <button className="btn-accent" disabled={busy || !file}><ScanSearch size={16} /> {busy ? "Analyzing…" : "Analyze"}</button>
      </form>

      {result && (
        <div className="space-y-5">
          <SummaryCards items={[
            { label: "Workers detected", value: s.workers },
            { label: "Compliant", value: s.compliant, tone: "text-emerald-400" },
            { label: "Violations", value: s.violations, tone: s.violations ? "text-red-400" : undefined },
            { label: "Safety score", value: s.safety_score == null ? null : `${s.safety_score}%` },
          ]} />
          <div className="card p-3">
            <img src={result.image} alt="Annotated result" className="mx-auto max-h-[70vh] rounded-lg" />
            <div className="mt-3 flex justify-end">
              <a className="btn" href={result.image} download="safevision-result.jpg"><Download size={16} /> Download annotated image</a>
            </div>
          </div>
          <PersonTable persons={result.persons} />
        </div>
      )}
    </div>
  );
}
