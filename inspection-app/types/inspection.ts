import { Status } from '../constants/inspectionCategories';

export interface InspectionItem {
    id: string;
    name: string;
    category: string;
    status: Status;
    voiceNoteTranscript: string | null;
    voiceNoteEditedTranscript: string | null;
    photos: string[];
    timelineEstimate: string | null;
    aiContext: any | null;
    aiPreliminaryStatus: "STOP" | "CAUTION" | "GO" | null;
    globalSafetyOverridePresent: boolean;
    voiceNoteUri: string | null; // PLACEHOLDER — populated by AI parser, consumed at compile step
}

export interface LegacyCompletedInspection {
    inspectionId: string;
    inspectorName: string;
    assetId: string;
    serialNumber: string;
    model: string;
    customerName: string | null;
    submittedAt: string;
    elapsedSeconds: number;
    generalComments: string | null;
    aiReview: {
        narrative: string;
        urgentFlags: string[];
        recommendedAction: string;
    } | null;
    items: InspectionItem[];
}

export type InspectionStatus = "green" | "yellow" | "red";
export type SeverityLevel = "CRITICAL" | "WARNING" | "INFO";
export type AiPreliminaryStatus = "STOP" | "CAUTION" | "GO";

export interface ContextEntry {
    component: string;
    observation: string;
    severity: SeverityLevel;
}

export interface AiContext {
    voice_context: { raw_transcript: string };
    evidence_backed: boolean;
    preliminary_status: AiPreliminaryStatus;
    technician_review_flag: boolean;
    context_entries: ContextEntry[];
    vision_raw?: string;
}

export interface CompletedInspection {
    id: string;
    title: string;
    formNumber: string;
    formType: string;
    assetId: string;
    serialNumber: string;
    model: string;
    customer?: string;
    submittedAt: string;
    submittedBy: string;
    status: InspectionStatus;
    overallRating: InspectionStatus;
    partsRating: number;
    severity: SeverityLevel;
    summary: string;
    actionableItems: string[];
    items: InspectionItem[];
}

// PLACEHOLDER: Future shape consumed by the global AI overview compilation layer.
// All voiceNoteUri values from a CompletedInspection are collected into this struct
// and POSTed to the compilation endpoint in a future sprint.
export interface VoiceNoteCompilationPayload {
    inspectionId: string;
    clips: {
        itemId: string;
        itemName: string;
        voiceNoteUri: string; // local file URI
        aiPreliminaryStatus: AiPreliminaryStatus | null;
    }[];
}
