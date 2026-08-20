import type { ReactNode } from "react";
import "./Card.css";

interface CardProps {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function Card({ title, actions, children }: CardProps) {
  return (
    <div className="card">
      {(title || actions) && (
        <div className="card-header">
          {title && <h3>{title}</h3>}
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}
