import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router";

/** Go back in app history, or to `fallback` when the screen was opened directly. */
export function useBack(fallback: string): () => void {
  const navigate = useNavigate();
  const location = useLocation();
  return useCallback(() => {
    if (location.key === "default") navigate(fallback, { replace: true });
    else navigate(-1);
  }, [location.key, navigate, fallback]);
}
