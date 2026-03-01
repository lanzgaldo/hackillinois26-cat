// ─────────────────────────────────────────────────────────────────────────────
// useReportSynthesis — Stage 3 hook for professional report generation
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";
import { synthesizeReport } from "../api/cattrackApi";
import { InspectionOutput, ApiError } from "../types/inspection";

interface UseReportSynthesisResult {
    /** Generate a professional report from technician-verified JSON */
    synthesize: (verifiedJson: InspectionOutput, jobId?: string) => Promise<void>;
    /** True while the /synthesize call is in flight */
    isLoading: boolean;
    /** The generated report text (null until synthesize completes) */
    report: string | null;
    /** Error message (null if no error) */
    error: string | null;
}

export function useReportSynthesis(): UseReportSynthesisResult {
    const [isLoading, setIsLoading] = useState(false);
    const [report, setReport] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const synthesize = useCallback(
        async (verifiedJson: InspectionOutput, jobId?: string) => {
            setIsLoading(true);
            setError(null);
            setReport(null);

            try {
                const response = await synthesizeReport(verifiedJson, jobId);
                setReport(response.report);
            } catch (err: unknown) {
                if (err instanceof ApiError) {
                    setError(err.message);
                } else if (err instanceof Error) {
                    setError(err.message);
                } else {
                    setError("Failed to generate report");
                }
            } finally {
                setIsLoading(false);
            }
        },
        []
    );

    return { synthesize, isLoading, report, error };
}
