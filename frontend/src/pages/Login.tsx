import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, FormField } from "../components";
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
      <Card title={mode === "login" ? "Log in" : "Create an End User account"}>
        <form onSubmit={handleSubmit}>
          <FormField label="Email" htmlFor="email">
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </FormField>

          {mode === "register" && (
            <FormField label="Full name" htmlFor="fullName">
              <input
                id="fullName"
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
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </FormField>

          {error && <p className="form-error">{error}</p>}

          <Button type="submit" disabled={submitting}>
            {mode === "login" ? "Log in" : "Register"}
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
  );
}
