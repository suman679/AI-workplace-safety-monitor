import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthShell, { Alert, Field } from "../components/AuthShell";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../services/api";

export default function Login() {
  const { login, sessionExpired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(form.email, form.password);
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to your safety dashboard"
      footer={<>New here? <Link className="text-safety hover:underline" to="/register">Create an account</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        {sessionExpired && !error && <Alert>Authentication expired. Please log in again.</Alert>}
        <Alert>{error}</Alert>
        <Field label="Email" type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Field label="Password" type="password" required autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <div className="text-right text-xs"><Link className="text-slate-400 hover:text-safety" to="/forgot-password">Forgot password?</Link></div>
        <button className="btn-primary" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      </form>
    </AuthShell>
  );
}
