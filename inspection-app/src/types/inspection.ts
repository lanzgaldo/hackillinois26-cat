// ─────────────────────────────────────────────────────────────────────────────
// CATrack Inspect AI — TypeScript Types
// Generated from backend schemas (inspection_schema.py + modal_app.py)
// ─────────────────────────────────────────────────────────────────────────────

// ── Enums ────────────────────────────────────────────────────────────────────

export type Severity = "Critical" | "Moderate" | "Low";

export type InspectionStatus = "pass" | "monitor" | "fail";

export type ComponentCategory =
  | "auto"
  | "tires_rims"
  | "steps_access"
  | "undercarriage"
  | "cooling"
  | "engine"
  | "hydraulics"
  | "structural";

// ── Anomaly ──────────────────────────────────────────────────────────────────

export interface Anomaly {
  /** Exact D6N component name */
  component: string;
  /** Where on the machine this component is located */
  component_location: string;
  /** Short issue label */
  issue: string;
  /** Detailed technical description of the observed condition */
  condition_description: string;
  /** AI-assigned severity */
  severity: Severity;
  /** Personnel and operational safety risks */
  safety_impact_assessment: string;
  /** Effect on equipment operation */
  operational_impact: string;
  /** Recommended service timeline */
  estimated_timeline: string;
  /** Specific repair or monitoring instruction */
  recommended_action: string;
  /** CAT part number (PT-D6N-xxx format) or null */
  part_number: string | null;
  /** True if multiple AI modalities agree on this finding */
  evidence_backed: boolean;
  /** True if AI flagged this for mandatory human review */
  technician_review_required: boolean;
  /** AI confidence in this finding (0–100) */
  confidence_score: number;
  /** True if triggered by global safety clause, not direct observation */
  is_global_safety_override: boolean;
  /** True if the component may not belong to the inspected machine */
  segment_mismatch_flag: boolean;
  /** Which global safety category triggered the override */
  global_override_category: string | null;

  // ── Stage 2: Technician review fields (added in-app, not from API) ──

  /** Technician confirms or rejects this finding */
  technician_confirmed?: boolean;
  /** Technician overrides the AI severity */
  technician_severity_override?: Severity;
  /** Required when technician_severity_override is set */
  technician_override_rationale?: string;
  /** Free-text technician notes */
  technician_notes?: string;
}

// ── Summary & Output ─────────────────────────────────────────────────────────

export interface InspectionSummary {
  /** Equipment identifier — always "CAT D6N Dozer" */
  asset: string;
  /** Overall pass/monitor/fail status */
  status: InspectionStatus;
  /** Human-readable operational impact summary */
  overall_operational_impact: string;
}

export interface InspectionOutput {
  inspection_summary: InspectionSummary;
  anomalies: Anomaly[];
}

// ── API Payloads ─────────────────────────────────────────────────────────────

export interface ExtractRequest {
  audio_b64: string;
  image_b64?: string;
  job_id?: string;
  category?: ComponentCategory;
}

export interface ExtractResponse {
  context_path: string;
  inspection_output: InspectionOutput;
  job_id?: string;
}

export interface SynthesizeRequest {
  verified_json: InspectionOutput;
  job_id?: string;
}

export interface SynthesizeResponse {
  report: string;
  job_id?: string;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  gateway: string;
  adapter_available: boolean;
  backend: {
    status: string;
    engine: string;
  };
  endpoints: string[];
}

// ── Error Type ───────────────────────────────────────────────────────────────

export class ApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

// ── Color Constants ──────────────────────────────────────────────────────────

export const SEVERITY_COLORS: Record<Severity, string> = {
  Critical: "#E53E3E",
  Moderate: "#D69E2E",
  Low: "#38A169",
};

export const STATUS_COLORS: Record<InspectionStatus, string> = {
  fail: "#E53E3E",
  monitor: "#D69E2E",
  pass: "#38A169",
};
