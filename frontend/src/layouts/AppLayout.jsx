import { Camera, Film, HardHat, Image as ImageIcon, LayoutDashboard, LogOut, MapPin, ScanEye, ShieldCheck, Users } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live", label: "Live Monitoring", icon: ScanEye },
  { to: "/video-analysis", label: "Video Analysis", icon: Film },
  { to: "/image-analysis", label: "Image Analysis", icon: ImageIcon },
  { to: "/sites", label: "Sites", icon: MapPin },
  { to: "/cameras", label: "Cameras", icon: Camera },
  { to: "/workers", label: "Workers", icon: Users },
  { to: "/ppe-rules", label: "PPE Rules", icon: HardHat },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const doLogout = async () => { await logout(); navigate("/login"); };

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-white/10 bg-ink-900 p-4 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2 text-lg font-semibold text-white"><ShieldCheck className="text-safety" /> SafeVision AI</div>
        <nav className="flex-1 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${isActive ? "bg-safety/15 text-safety" : "text-slate-400 hover:bg-white/5"}`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 pt-4 text-sm">
          <div className="truncate font-medium text-white">{user.full_name}</div>
          <div className="truncate text-xs text-slate-500">{user.role.replaceAll("_", " ")}</div>
          <button onClick={doLogout} className="mt-3 flex items-center gap-2 text-slate-400 hover:text-safety"><LogOut size={16} /> Log out</button>
        </div>
      </aside>
      <header className="flex items-center gap-1 overflow-x-auto border-b border-white/10 bg-ink-900 px-3 py-2 md:hidden">
        {NAV.map(({ to, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `whitespace-nowrap rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-safety/15 text-safety" : "text-slate-400"}`}>{label}</NavLink>
        ))}
        <button onClick={doLogout} className="ml-auto whitespace-nowrap px-3 py-1.5 text-sm text-slate-400">Log out</button>
      </header>
      <main className="min-w-0 flex-1 p-5 md:p-10"><Outlet /></main>
    </div>
  );
}
