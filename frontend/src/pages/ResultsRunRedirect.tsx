import React from "react";
import { Navigate, useParams } from "react-router-dom";

export default function ResultsRunRedirect() {
  const { runId } = useParams();
  if (!runId) return <Navigate to="/backtests" replace />;
  return <Navigate to={`/backtests/${encodeURIComponent(runId)}`} replace />;
}

