import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, FormField, ThemeToggle } from "../components";
import { GaugeIcon, LogoMark, RouteIcon, ShieldIcon } from "../components/icons";
import { register as apiRegister, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const HIGHLIGHTS = [
  { icon: RouteIcon, label: "Auto-routed", text: "Classified and routed to the right team instantly" },
  { icon: GaugeIcon, label: "Confidence gate", text: "An independent model scores every AI draft" },
  { icon: ShieldIcon, label: "Human backstop", text: "Anything uncertain goes to a person, not the customer" },
];

// Real department names — not usage stats — so this stays honest per the "no
// fake/hardcoded analytics" rule while still giving the login page something
// concrete to say about the product's actual coverage.
const DEPARTMENTS = ["Cloud", "Database", "HR", "Networking", "SAP"];

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
    <div className="login-v2-page">
      <div className="login-v2-theme-toggle">
        <ThemeToggle />
      </div>
      <div className="login-v2-grid" aria-hidden="true" />
      <div className="login-v2-glow login-v2-glow-a" aria-hidden="true" />
      <div className="login-v2-glow login-v2-glow-b" aria-hidden="true" />
      <div className="login-v2-glow login-v2-glow-c" aria-hidden="true" />

      <span className="login-v2-eyebrow">AI-Powered Ticket Routing</span>

      <div className="login-v2-card">
        <div className="login-v2-brand">
          <span className="login-v2-brand-mark">
            <LogoMark width={30} height={30} />
          </span>
          <span>TicketSense</span>
        </div>

        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="login-v2-subtitle">
          {mode === "login"
            ? "Log in to submit and track your support tickets."
            : "Set up an End User account to start submitting tickets."}
        </p>

        <ul className="login-v2-icon-row">
          {HIGHLIGHTS.map((h) => (
            <li key={h.label} title={h.text}>
              <span className="login-v2-icon-badge">
                <h.icon width={16} height={16} />
              </span>
              <span>{h.label}</span>
            </li>
          ))}
        </ul>

        <form onSubmit={handleSubmit} className="login-v2-form">
          <FormField label="Email" htmlFor="email">
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
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
          className="link-button login-v2-toggle"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError(null);
          }}
        >
          {mode === "login" ? "New End User? Create an account" : "Already have an account? Log in"}
        </button>
      </div>

      <div className="login-v2-departments">
        <span>Routes tickets across</span>
        <div className="login-v2-dept-chips">
          {DEPARTMENTS.map((d) => (
            <span key={d} className="login-v2-dept-chip">
              {d}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
