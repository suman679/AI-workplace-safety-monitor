import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AuthShell, { Alert, Field } from "../components/AuthShell";
import api, { errorMessage } from "../services/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const token = params.get("token");

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/auth/reset-password", { token, new_password: password });
      navigate("/login", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Choose a new password" footer={<Link className="text-safety hover:underline" to="/login">Back to login</Link>}>
      {!token ? (
        <Alert>Reset link is invalid or has expired</Alert>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <Alert>{error}</Alert>
          <Field label="New password (8+ characters, letters and numbers)" type="password" required minLength={8} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="btn-primary" disabled={busy}>{busy ? "Updating…" : "Update password"}</button>
        </form>
      )}
    </AuthShell>
  );
}
