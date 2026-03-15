import React from "react";

export default function InlineError({ title, error }: { title: string; error: string }) {
  return (
    <div className="panel">
      <div style={{ color: "rgba(251,113,133,0.95)", fontWeight: 650 }}>{title}</div>
      <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.72)", marginTop: 10 }}>
        {error}
      </pre>
    </div>
  );
}

