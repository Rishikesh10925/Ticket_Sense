import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, FormField } from "../components";
import { DraftIcon, GaugeIcon, LogoMark, RouteIcon, TagIcon, TicketIcon, UserCheckIcon } from "../components/icons";
import { register as apiRegister, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

// The pipeline every ticket actually runs through (see docs/langgraph-pipeline.md)
// — shown here as a diagram rather than marketing bullet copy, so the login screen
// itself communicates what makes this product different: an independent confidence
// gate stands between the AI's draft and a human ever seeing it.
const PIPELINE_STEPS: { icon: typeof TicketIcon; title: string; detail: string; signature?: boolean }[] = [
  { icon: TicketIcon, title: "Submit", detail: "An employee reports an issue in plain language." },
  { icon: TagIcon, title: "Classify", detail: "Priority and sentiment are inferred automatically." },
  { icon: RouteIcon, title: "Route", detail: "Sent to the right department — SAP, Cloud, Networking…" },
  { icon: DraftIcon, title: "Draft", detail: "A reply is grounded in retrieved evidence, with citations." },
  {
    icon: GaugeIcon,
    title: "Confidence gate",
    detail: "A second, independent model scores the draft before anyone sees it.",
    signature: true,
  },
  { icon: UserCheckIcon, title: "Human review", detail: "An engineer accepts, edits, rejects, or escalates." },
];

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
        <h1>An AI drafts the reply. A second AI grades it. A human decides.</h1>
        <p>
          Every ticket runs the same pipeline — classified, routed, matched against
          evidence, and drafted automatically. Nothing reaches an engineer until an
          independent confidence model has scored it.
        </p>

        <ol className="pipeline">
          {PIPELINE_STEPS.map((step, i) => (
            <li key={step.title} className={`pipeline-step${step.signature ? " pipeline-step-signature" : ""}`}>
              <span className="pipeline-node">
                <step.icon width={16} height={16} />
              </span>
              <div className="pipeline-body">
                <span className="pipeline-step-title">
                  <span className="pipeline-step-index tabular-nums">{String(i + 1).padStart(2, "0")}</span>
                  {step.title}
                </span>
                <span className="pipeline-step-detail">{step.detail}</span>
              </div>
            </li>
          ))}
        </ol>
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
