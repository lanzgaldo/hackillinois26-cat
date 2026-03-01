import axios from 'axios';

const MODAL_URL = process.env.EXPO_PUBLIC_MODAL_URL;
const MODE = process.env.EXPO_PUBLIC_INSPECTION_MODE;

export interface AIInspectionResult {
    transcript: string;
    aiContext: any | null;
    error: string | null;
}

const MOCK_CANONICAL_CONTEXT = {
    evidence_backed: true,
    preliminary_status: "STOP",
    technician_review_flag: true,
    context_entries: [
        {
            component: "Hydraulic System",
            observation: "Active leak near the final drive fitting",
            severity: "CRITICAL"
        }
    ]
};

export async function runInspectionAI(
    audioUri: string,
    imageUri: string | null = null,
    componentCategory: string = "auto"
): Promise<AIInspectionResult> {

    // Mock mode — no API call
    if (MODE === "mock") {
        await new Promise(r => setTimeout(r, 1500));
        return {
            transcript: "Hydraulic line on left side has an active leak near the final drive fitting.",
            aiContext: MOCK_CANONICAL_CONTEXT,
            error: null
        };
    }

    // Live mode
    try {
        const formData = new FormData();

        // Audio — read as blob from URI
        formData.append("audio", {
            uri: audioUri,
            type: "audio/wav",
            name: "inspection.wav"
        } as any);

        // Image — optional
        if (imageUri) {
            formData.append("image", {
                uri: imageUri,
                type: "image/jpeg",
                name: "inspection.jpg"
            } as any);
        }

        formData.append("component_category", componentCategory);

        const response = await axios.post(MODAL_URL || "", formData, {
            headers: { "Content-Type": "multipart/form-data" },
            timeout: 30000
        });

        const context = response.data;

        return {
            transcript: context?.voice_context?.raw_transcript ?? "",
            aiContext: context,
            error: null
        };

    } catch (err: any) {
        const status = err?.response?.status;
        let message = "Transcription service error — please retry";
        if (status === 401 || status === 402)
            message = "AI service initializing, try again shortly";
        if (status === 429)
            message = "Service busy — wait 30 seconds and retry";
        if (err?.code === "ECONNABORTED")
            message = "Taking too long — check your connection and retry";
        if (!err?.response)
            message = "No connection — audio saved, transcription pending";

        return { transcript: "", aiContext: null, error: message };
    }
}
