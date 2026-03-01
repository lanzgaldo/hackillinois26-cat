// ─────────────────────────────────────────────────────────────────────────────
// useInspection — Stage 1 hook for the full AI extraction pipeline
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback, useMemo } from "react";
import { runInspection } from "../api/cattrackApi";
import {
    ExtractResponse,
    InspectionStatus,
    ComponentCategory,
    ApiError,
} from "../types/inspection";

interface UseInspectionResult {
    /** Submit audio + optional image for AI inspection */
    submit: (
        audioUri: string,
        imageUri?: string,
        jobId?: string,
        category?: ComponentCategory
    ) => Promise<void>;
    /** True while the /extract call is in flight */
    isLoading: boolean;
    /** Full API response (null until submit completes) */
    result: ExtractResponse | null;
    /** Error message (null if no error) */
    error: string | null;
    /** True if any anomaly is Critical or is a global safety override */
    hasCritical: boolean;
    /** Convenience: inspection status from the summary */
    overallStatus: InspectionStatus | null;
    /** True if no image was provided — UI should show audio-only warning */
    audioOnly: boolean;
    /** Reset state for a new inspection */
    reset: () => void;
}

export function useInspection(): UseInspectionResult {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<ExtractResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [audioOnly, setAudioOnly] = useState(false);

    const submit = useCallback(
        async (
            audioUri: string,
            imageUri?: string,
            jobId?: string,
            category: ComponentCategory = "auto"
        ) => {
            setIsLoading(true);
            setError(null);
            setResult(null);
            setAudioOnly(!imageUri);

            try {
                const response = await runInspection(audioUri, imageUri, jobId, category);
                setResult(response);
            } catch (err: unknown) {
                if (err instanceof ApiError) {
                    switch (err.status) {
                        case 502:
                            setError("Service temporarily unavailable — please retry");
                            break;
                        case 504:
                            setError("Processing took too long — try again");
                            break;
                        default:
                            setError(err.message);
                    }
                } else if (err instanceof Error) {
                    setError(err.message);
                } else {
                    setError("An unexpected error occurred");
                }
            } finally {
                setIsLoading(false);
            }
        },
        []
    );

    const hasCritical = useMemo(() => {
        if (!result) return false;
        return result.inspection_output.anomalies.some(
            (a) => a.severity === "Critical" || a.is_global_safety_override === true
        );
    }, [result]);

    const overallStatus = useMemo<InspectionStatus | null>(() => {
        if (!result) return null;
        return result.inspection_output.inspection_summary.status;
    }, [result]);

    const reset = useCallback(() => {
        setResult(null);
        setError(null);
        setIsLoading(false);
        setAudioOnly(false);
    }, []);

    return {
        submit,
        isLoading,
        result,
        error,
        hasCritical,
        overallStatus,
        audioOnly,
        reset,
    };
}
