import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Landing() {
  const { user } = useAuth();
  return (
    <div className="mx-auto max-w-5xl px-6">
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-2 text-lg font-semibold text-white"><ShieldCheck className="text-safety" /> SafeVision AI</div>
        <Link to={user ? "/dashboard" : "/login"} className="text-sm text-slate-300 hover:text-safety">{user ? "Dashboard" : "Log in"}</Link>
      </header>
      <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-white md:text-6xl">AI-Powered Workplace Safety Monitoring</h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-400">Detect PPE violations in real time and transform workplace safety with computer vision.</p>
        <div className="mt-9 flex justify-center gap-3">
          <Link to="/register" className="rounded-lg bg-safety px-5 py-3 text-sm font-semibold text-ink-950 hover:bg-safety-soft">Start Monitoring</Link>
        </div>
      </motion.section>
    </div>
  );
}
