import { useEffect, useState } from "react";

export type AsyncState<T> =
  | { status: "idle" | "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading", data: null, error: null });

  useEffect(() => {
    let alive = true;
    setState({ status: "loading", data: null, error: null });
    fn()
      .then((data) => {
        if (!alive) return;
        setState({ status: "success", data, error: null });
      })
      .catch((e) => {
        if (!alive) return;
        setState({ status: "error", data: null, error: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}

