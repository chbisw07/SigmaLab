import React from "react";

export default function PageHeader({
  title,
  subtitle,
  actions
}: {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <div className="row" style={{ marginBottom: 12 }}>
      <div>
        <h1 className="h1">{title}</h1>
        {subtitle ? <div className="subtle">{subtitle}</div> : null}
      </div>
      {actions ? <div style={{ display: "flex", gap: 10, alignItems: "center" }}>{actions}</div> : null}
    </div>
  );
}

