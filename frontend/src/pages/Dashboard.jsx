import { Camera, MapPin, Users, Wifi } from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Banner, Loading, PageHeader } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";

const STATUS_COLOR = { ONLINE: "#34d399", OFFLINE: "#64748b", WARNING: "#fbbf24" };

function StatCard({ icon: Icon, label, value, hint }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between text-slate-400"><span className="text-sm">{label}</span><Icon size={18} className="text-safety" /></div>
      <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data: s, loading, error } = useFetch("/api/dashboard/stats");

  const chart = s ? Object.entries(s.cameras_by_status).map(([status, count]) => ({ status, count })) : [];
  const steps = s && [
    { done: s.total_sites > 0, text: "Create a site and choose its required PPE", to: "/sites" },
    { done: s.total_cameras > 0, text: "Add a camera or video source", to: "/cameras" },
    { done: s.total_workers > 0, text: "Add your workers", to: "/workers" },
  ];

  return (
    <div>
      <PageHeader title={`Welcome, ${user.full_name.split(" ")[0]}`} subtitle="Your safety operations at a glance" />
      <Banner>{error}</Banner>
      {loading && !s ? <Loading /> : s && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard icon={MapPin} label="Sites" value={s.total_sites} />
            <StatCard icon={Camera} label="Cameras" value={s.total_cameras} />
            <StatCard icon={Wifi} label="Online cameras" value={s.online_cameras} hint={`${s.total_cameras - s.online_cameras} not online`} />
            <StatCard icon={Users} label="Workers" value={s.total_workers} hint={`${s.active_workers} active`} />
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            <div className="card p-5 lg:col-span-2">
              <h2 className="mb-4 text-sm font-medium text-slate-300">Cameras by status</h2>
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chart}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="status" stroke="#64748b" fontSize={12} />
                    <YAxis allowDecimals={false} stroke="#64748b" fontSize={12} />
                    <Tooltip contentStyle={{ background: "#111a28", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>{chart.map((d) => <Cell key={d.status} fill={STATUS_COLOR[d.status]} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card p-5">
              <h2 className="mb-4 text-sm font-medium text-slate-300">Getting started</h2>
              <ul className="space-y-3 text-sm">
                {steps.map((st) => (
                  <li key={st.to} className="flex items-start gap-2">
                    <span className={st.done ? "text-emerald-400" : "text-slate-600"}>{st.done ? "✓" : "○"}</span>
                    <Link to={st.to} className={st.done ? "text-slate-500 line-through" : "text-slate-200 hover:text-safety"}>{st.text}</Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
