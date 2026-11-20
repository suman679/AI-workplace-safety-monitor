import { useState } from "react";
import { Link } from "react-router-dom";
import AuthShell, { Alert, Field } from "../components/AuthShell";
import api, { errorMessage } from "../services/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/api/auth/forgot-password", { email });
      setMessage(data.message);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Reset your password" subtitle="We'll send a reset link to your email" footer={<Link className="text-safety hover:underline" to="/login">Back to login</Link>}>
      <form onSubmit={submit} className="space-y-4">
        <Alert>{error}</Alert>
        <Alert kind="success">{message}</Alert>
        <Field label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <button className="btn-primary" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button>
      </form>
    </AuthShell>
  );
}
