import type { ReactNode } from "react";
import "./FormField.css";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  hint?: string;
  children: ReactNode;
}

export default function FormField({ label, htmlFor, hint, children }: FormFieldProps) {
  return (
    <div className="form-field">
      <label htmlFor={htmlFor}>{label}</label>
      {children}
      {hint && <span className="form-field-hint">{hint}</span>}
    </div>
  );
}
