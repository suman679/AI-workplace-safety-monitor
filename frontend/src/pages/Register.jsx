import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell, { Alert, Field } from "../components/AuthShell";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../services/api";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", company_name: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Set up your company workspace in a minute"
      footer={<>Already registered? <Link className="text-safety hover:underline" to="/login">Log in</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Alert>{error}</Alert>
        <Field label="Full name" required minLength={2} value={form.full_name} onChange={set("full_name")} />
        <Field label="Work email" type="email" required autoComplete="email" value={form.email} onChange={set("email")} />
        <Field label="Company name" required minLength={2} value={form.company_name} onChange={set("company_name")} />
        <Field label="Password (8+ characters, letters and numbers)" type="password" required minLength={8} autoComplete="new-password" value={form.password} onChange={set("password")} />
        <button className="btn-primary" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}
