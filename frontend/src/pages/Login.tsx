import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, FormField } from "../components";
import { LogoMark } from "../components/icons";
import { register as apiRegister, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        await apiRegister(email, fullName, password);
      }
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-brand-panel">
        <div className="login-brand-mark">
          <LogoMark width={40} height={40} />
          <span>TicketSense</span>
        </div>
        <h1>Multi-agent enterprise ticket routing &amp; resolution</h1>
        <p>
          Tickets are classified, routed to the right team, and matched against a
          knowledge base and prior resolved cases. An AI drafts a cited reply from
          that evidence — a human engineer always makes the final call.
        </p>
        <ul className="login-brand-points">
          <li>Automatic classification &amp; department routing</li>
          <li>Grounded, cited draft replies with source evidence</li>
          <li>Human review before anything reaches the requester</li>
        </ul>
      </div>

      <div className="login-form-panel">
        <Card title={mode === "login" ? "Log in" : "Create an End User account"}>
          <form onSubmit={handleSubmit}>
            <FormField label="Email" htmlFor="email">
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </FormField>

            {mode === "register" && (
              <FormField label="Full name" htmlFor="fullName">
                <input
                  id="fullName"
                  placeholder="Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </FormField>
            )}

            <FormField label="Password" htmlFor="password">
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </FormField>

            {error && <p className="form-error">{error}</p>}

            <Button type="submit" disabled={submitting} className="login-submit">
              {submitting ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
            </Button>
          </form>

          <button
            type="button"
            className="link-button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
          >
            {mode === "login"
              ? "New End User? Create an account"
              : "Already have an account? Log in"}
          </button>
        </Card>
      </div>
    </div>
  );
}
