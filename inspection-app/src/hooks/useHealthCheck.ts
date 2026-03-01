// ─────────────────────────────────────────────────────────────────────────────
// useHealthCheck — polls /health on mount, re-polls every 30s if unhealthy
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useRef, useCallback } from "react";
import { healthCheck } from "../api/cattrackApi";

interface UseHealthCheckResult {
    isHealthy: boolean;
    isLoading: boolean;
    error: string | null;
}

const POLL_INTERVAL_MS = 30_000;

export function useHealthCheck(): UseHealthCheckResult {
    const [isHealthy, setIsHealthy] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const check = useCallback(async () => {
        try {
            setIsLoading(true);
            const result = await healthCheck();
            const healthy = result.status === "ok" && result.adapter_available === true;
            setIsHealthy(healthy);
            setError(null);

            // Stop polling once healthy
            if (healthy && timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        } catch (err: unknown) {
            setIsHealthy(false);
            setError(err instanceof Error ? err.message : "Health check failed");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        // Initial check
        check();

        // Poll every 30s while unhealthy
        timerRef.current = setInterval(() => {
            check();
        }, POLL_INTERVAL_MS);

        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        };
    }, [check]);

    return { isHealthy, isLoading, error };
}
