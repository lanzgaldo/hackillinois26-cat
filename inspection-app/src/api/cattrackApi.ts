// ─────────────────────────────────────────────────────────────────────────────
// CATrack Inspect AI — API Client
// Uses fetch only. No Axios. Typed errors. Retry logic on 502/504.
// ─────────────────────────────────────────────────────────────────────────────

import {
    ApiError,
    ExtractResponse,
    HealthResponse,
    InspectionOutput,
    SynthesizeResponse,
    ComponentCategory,
    Severity,
    Anomaly,
} from "../types/inspection";

const API_BASE = "https://lanzgaldo--catrack-provider-fastapi-app.modal.run";

const EXTRACT_TIMEOUT_MS = 180_000;
const DEFAULT_TIMEOUT_MS = 15_000;

const VALID_SEVERITIES: readonly Severity[] = ["Critical", "Moderate", "Low"];

// ── Internal helpers ─────────────────────────────────────────────────────────

async function fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number
): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...init,
            signal: controller.signal,
        });
        return response;
    } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
            throw new ApiError(504, "Request timed out");
        }
        throw err;
    } finally {
        clearTimeout(timer);
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = "";
        try {
            const body = await response.text();
            detail = body.slice(0, 300);
        } catch {
            detail = response.statusText;
        }
        throw new ApiError(response.status, detail);
    }
    return response.json() as Promise<T>;
}

function sanitizeAnomalies(
    anomalies: Anomaly[],
    imageWasSent: boolean
): Anomaly[] {
    return anomalies.map((a) => {
        let severity = a.severity;
        let techReview = a.technician_review_required;

        // Guard: replace hallucinated severity values
        if (!VALID_SEVERITIES.includes(severity)) {
            severity = "Low";
            techReview = true;
        }

        // Guard: if no image was sent, force evidence_backed to false
        const evidenceBacked = imageWasSent ? a.evidence_backed : false;

        return { ...a, severity, technician_review_required: techReview, evidence_backed: evidenceBacked };
    });
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Convert a local file URI to a base64 string (data: prefix stripped).
 * Works with Expo's file system URIs and standard blob URIs.
 */
export async function toBase64(uri: string): Promise<string> {
    const response = await fetch(uri);
    const blob = await response.blob();
    return new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result as string;
            // Strip data:*;base64, prefix if present
            const commaIdx = result.indexOf(",");
            resolve(commaIdx >= 0 ? result.slice(commaIdx + 1) : result);
        };
        reader.onerror = () => reject(new Error("Failed to read file as base64"));
        reader.readAsDataURL(blob);
    });
}

/**
 * Health check — verify the backend is alive.
 */
export async function healthCheck(): Promise<HealthResponse> {
    const response = await fetchWithTimeout(
        `${API_BASE}/health`,
        { method: "GET" },
        DEFAULT_TIMEOUT_MS
    );
    return handleResponse<HealthResponse>(response);
}

/**
 * Stage 1 — Full AI extraction from audio + optional image.
 * Retries once automatically on 502 or 504.
 */
export async function runInspection(
    audioUri: string,
    imageUri?: string,
    jobId?: string,
    category: ComponentCategory = "auto"
): Promise<ExtractResponse> {
    // Pre-flight validation
    if (!audioUri || typeof audioUri !== "string" || audioUri.trim() === "") {
        throw new ApiError(400, "audioUri is required and must be a non-empty string");
    }

    const audio_b64 = await toBase64(audioUri);
    const body: Record<string, unknown> = { audio_b64, category };

    const imageWasSent = !!imageUri;
    if (imageUri) {
        body.image_b64 = await toBase64(imageUri);
    }
    if (jobId) {
        body.job_id = jobId;
    }

    const init: RequestInit = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    };

    // Attempt with single retry on 502/504
    let lastError: ApiError | null = null;
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            const response = await fetchWithTimeout(
                `${API_BASE}/extract`,
                init,
                EXTRACT_TIMEOUT_MS
            );

            if (response.status === 502 || response.status === 504) {
                lastError = new ApiError(
                    response.status,
                    response.status === 502
                        ? "Service temporarily unavailable"
                        : "Processing took too long — try again"
                );
                if (attempt === 0) continue; // retry once
                throw lastError;
            }

            const result = await handleResponse<ExtractResponse>(response);

            // Post-flight validation: anomalies must be an array
            if (
                !result.inspection_output ||
                !Array.isArray(result.inspection_output.anomalies)
            ) {
                throw new ApiError(500, "Malformed response: anomalies missing");
            }

            // Sanitize anomalies (enum guard + evidence parity)
            result.inspection_output.anomalies = sanitizeAnomalies(
                result.inspection_output.anomalies,
                imageWasSent
            );

            return result;
        } catch (err) {
            if (err instanceof ApiError) {
                lastError = err;
                if (
                    attempt === 0 &&
                    (err.status === 502 || err.status === 504)
                ) {
                    continue; // retry once
                }
            }
            throw err;
        }
    }

    throw lastError ?? new ApiError(500, "Unknown error during inspection");
}

/**
 * Stage 3 — Generate a professional report from technician-verified JSON.
 */
export async function synthesizeReport(
    verifiedJson: InspectionOutput,
    jobId?: string
): Promise<SynthesizeResponse> {
    const body: Record<string, unknown> = { verified_json: verifiedJson };
    if (jobId) body.job_id = jobId;

    const response = await fetchWithTimeout(
        `${API_BASE}/synthesize`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        },
        DEFAULT_TIMEOUT_MS
    );

    return handleResponse<SynthesizeResponse>(response);
}
