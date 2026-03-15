import React from "react";

export default function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre
      className="mono"
      style={{
        margin: "10px 0 0 0",
        whiteSpace: "pre-wrap",
        color: "rgba(255,255,255,0.78)",
        fontSize: 12,
        lineHeight: 1.45
      }}
    >
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

