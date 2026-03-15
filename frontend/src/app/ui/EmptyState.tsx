import React from "react";
import { Link } from "react-router-dom";

export default function EmptyState({
  title,
  body,
  actions
}: {
  title: string;
  body: React.ReactNode;
  actions?: Array<{ label: string; to: string }>;
}) {
  return (
    <div className="panel" style={{ background: "rgba(255,255,255,0.04)" }}>
      <div style={{ fontWeight: 650 }}>{title}</div>
      <div className="subtle" style={{ marginTop: 6 }}>
        {body}
      </div>
      {actions && actions.length ? (
        <div style={{ display: "flex", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
          {actions.map((a) => (
            <Link key={a.to} to={a.to} className="btn primary">
              {a.label}
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}

