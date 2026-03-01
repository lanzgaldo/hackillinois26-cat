import * as FileSystem from 'expo-file-system/legacy';
import * as ImageManipulator from 'expo-image-manipulator';

// Direct cleanpxe endpoints
const TRANSCRIBE_URL = 'https://cleanpxe--cat-inspect-ai-sprint1-web-transcribe.modal.run/';
const VISION_URL = 'https://cleanpxe--cat-inspect-ai-sprint1-web-analyze-image.modal.run/';
const EXTRACT_URL = 'https://cleanpxe--cat-inspect-ai-sprint1-web-extract.modal.run/';
const SYNTHESIZE_URL = 'https://cleanpxe--cat-inspect-ai-sprint1-web-synthesize.modal.run/';

const MODE = process.env.EXPO_PUBLIC_INSPECTION_MODE;
const MAX_IMAGE_DIMENSION = 800;
const IMAGE_QUALITY = 0.6;

export interface AIInspectionResult {
    transcript: string;
    aiContext: any | null;
    error: string | null;
}

const MOCK_CONTEXT = {
    inspection_output: {
        inspection_summary: {
            asset: 'CAT D6N Dozer',
            status: 'fail',
            overall_operational_impact: 'Hydraulic leak near final drive — do not operate.'
        },
        anomalies: [{
            component: 'Hydraulic System',
            condition_description: 'Active leak near the final drive fitting. Fluid loss confirmed.',
            severity: 'Critical',
            estimated_timeline: 'Replace immediately before next operation',
            recommended_action: 'Inspect and replace hydraulic hose before operation.'
        }]
    }
};

async function compressImageUri(uri: string): Promise<string> {
    try {
        const result = await ImageManipulator.manipulateAsync(
            uri,
            [{ resize: { width: MAX_IMAGE_DIMENSION } }],
            { compress: IMAGE_QUALITY, format: ImageManipulator.SaveFormat.JPEG }
        );
        return result.uri;
    } catch {
        return uri;
    }
}

function buildTranscriptFromContext(context: any): string {
    const output = context?.inspection_output ?? context;
    let transcript = context?.raw_transcript ?? context?.voice_context?.raw_transcript ?? '';

    if (!transcript && output?.anomalies?.length > 0) {
        const lines: string[] = [];
        const summary = output.inspection_summary?.overall_operational_impact;
        if (summary) lines.push(summary);
        output.anomalies.forEach((a: any) => {
            const desc = a.condition_description ?? a.observation ?? '';
            if (desc) lines.push(`• ${a.component}: ${desc}`);
        });
        transcript = lines.join('\n\n');
    }
    if (!transcript && output?.inspection_summary?.overall_operational_impact) {
        transcript = output.inspection_summary.overall_operational_impact;
    }
    return transcript;
}

async function postJSON(url: string, body: object): Promise<Response> {
    return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export async function runInspectionAI(
    audioUri: string,
    imageUri: string | null = null,
    componentCategory: string = 'auto'
): Promise<AIInspectionResult> {

    console.log('[AI] runInspectionAI', { MODE, hasAudio: !!audioUri, hasImage: !!imageUri });

    if (MODE === 'mock') {
        await new Promise(r => setTimeout(r, 1500));
        return {
            transcript: 'Hydraulic line on left side has an active leak near the final drive fitting.',
            aiContext: MOCK_CONTEXT,
            error: null
        };
    }

    // Step 1: Read audio
    let audio_b64: string;
    try {
        audio_b64 = await FileSystem.readAsStringAsync(audioUri, { encoding: 'base64' as any });
        console.log('[AI] Audio ready, length:', audio_b64.length);
    } catch (e: any) {
        return { transcript: '', aiContext: null, error: `Could not read audio: ${e?.message}` };
    }

    // Step 2: Compress + read image
    let image_b64: string | null = null;
    if (imageUri) {
        try {
            const compressed = await compressImageUri(imageUri);
            image_b64 = await FileSystem.readAsStringAsync(compressed, { encoding: 'base64' as any });
            console.log('[AI] Image ready (compressed), length:', image_b64.length);
        } catch (e: any) {
            console.warn('[AI] Image read failed, continuing audio-only:', e?.message);
        }
    }

    // Step 3: Call /extract (audio-only) — returns full structured analysis
    // Vision endpoint currently unstable; extract pipeline handles analysis without it
    const job_id = `job-${Date.now()}`;
    let extractContext: any = null;
    try {
        const extractResponse = await postJSON(EXTRACT_URL, {
            audio_b64,
            image_b64: null,
            job_id,
            category: componentCategory,
        });
        console.log('[AI] /extract status:', extractResponse.status);
        if (extractResponse.ok) {
            extractContext = await extractResponse.json();
            console.log('[AI] /extract succeeded:', JSON.stringify(extractContext).slice(0, 300));
        } else {
            const body = await extractResponse.text().catch(() => '');
            const s = extractResponse.status;
            console.error('[AI] /extract error:', s, body.slice(0, 150));
            let msg = `API error ${s} — please retry`;
            if (s === 401 || s === 402) msg = 'AI service initializing, try again shortly';
            if (s === 429) msg = 'Service busy — wait 30s and retry';
            return { transcript: '', aiContext: null, error: msg };
        }
    } catch (e: any) {
        console.error('[AI] Network error:', e?.message);
        return { transcript: '', aiContext: null, error: 'Network error — check WiFi and retry' };
    }
    const transcript = buildTranscriptFromContext(extractContext);
    console.log('[AI] Transcript:', transcript.slice(0, 100));

    return { transcript, aiContext: extractContext, error: null };
}

// Standalone transcription-only
export async function transcribeOnly(audioUri: string): Promise<{ transcript: string; error: string | null }> {
    if (MODE === 'mock') {
        await new Promise(r => setTimeout(r, 800));
        return { transcript: 'Mock transcription of voice note.', error: null };
    }
    let audio_b64: string;
    try {
        audio_b64 = await FileSystem.readAsStringAsync(audioUri, { encoding: 'base64' as any });
    } catch (e: any) {
        return { transcript: '', error: `Could not read audio: ${e?.message}` };
    }
    try {
        const res = await postJSON(TRANSCRIBE_URL, { audio_b64 });
        if (!res.ok) return { transcript: '', error: 'Transcription failed — retry' };
        const data = await res.json();
        return { transcript: data?.transcript ?? data?.text ?? '', error: null };
    } catch (e: any) {
        return { transcript: '', error: `Network error: ${e?.message}` };
    }
}

export const ENDPOINTS = { EXTRACT_URL, TRANSCRIBE_URL, VISION_URL, SYNTHESIZE_URL };
