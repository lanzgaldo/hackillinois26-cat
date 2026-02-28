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
}

export interface CompletedInspection {
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
