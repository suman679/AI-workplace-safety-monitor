import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Banner, EmptyState, Loading, PageHeader, SelectField } from "../components/ui";
import useFetch from "../hooks/useFetch";
import usePermissions from "../hooks/usePermissions";
import api, { errorMessage } from "../services/api";
import { PPE_LABELS, PPE_ORDER, SEVERITIES } from "../utils/constants";

export default function PpeRules() {
  const { data: sites, error: sitesError } = useFetch("/api/sites");
  const [siteId, setSiteId] = useState("");
  const { canWrite } = usePermissions();
  const { data: rules, loading, error, reload } = useFetch("/api/ppe-rules", { site_id: siteId }, !!siteId);
  const [saveError, setSaveError] = useState("");

  useEffect(() => { if (!siteId && sites?.length) setSiteId(sites[0].id); }, [sites, siteId]);

  async function save(rule, patch) {
    setSaveError("");
    try {
      await api.put(`/api/ppe-rules/${rule.id}`, patch);
      reload();
    } catch (err) {
      setSaveError(errorMessage(err));
    }
  }

  const ordered = rules ? [...rules].sort((a, b) => PPE_ORDER.indexOf(a.ppe_item) - PPE_ORDER.indexOf(b.ppe_item)) : [];

  return (
    <div>
      <PageHeader title="PPE Rules" subtitle="Choose which PPE each site requires and how severe a violation is" />
      <Banner>{sitesError || error || saveError}</Banner>
      {sites?.length === 0 ? (
        <EmptyState title="No sites yet" text="PPE rules are set per site." action={<Link to="/sites" className="btn-accent">Create a site</Link>} />
      ) : (
        <>
          <div className="mb-4 w-64">
            <SelectField label="Site" value={siteId} onChange={(e) => setSiteId(e.target.value)}>
              {sites?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </SelectField>
          </div>
          {!rules || (loading && !rules.length) ? <Loading /> : (
            <div className="card divide-y divide-white/5">
              {ordered.map((r) => (
                <div key={r.id} className="flex flex-wrap items-center justify-between gap-4 px-5 py-4">
                  <label className="flex items-center gap-3 text-sm font-medium text-white">
                    <input type="checkbox" className="h-4 w-4 accent-amber-500" checked={r.is_required} disabled={!canWrite} onChange={(e) => save(r, { is_required: e.target.checked })} />
                    {PPE_LABELS[r.ppe_item]}
                  </label>
                  <div className="w-44">
                    <SelectField label="Violation severity" value={r.severity} disabled={!canWrite || !r.is_required} onChange={(e) => save(r, { severity: e.target.value })}>
                      {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </SelectField>
                  </div>
                </div>
              ))}
            </div>
          )}
          {!canWrite && <p className="mt-3 text-xs text-slate-500">Your role can view rules but not change them.</p>}
        </>
      )}
    </div>
  );
}
