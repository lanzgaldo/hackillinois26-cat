import { InspectionState, AIReview } from '../context/InspectionContext';
import { featureFlags } from '../constants/featureFlags';
import { mockAiReview } from './mockAiReview';

export const generateAiReview = async (state: InspectionState): Promise<AIReview> => {
    if (featureFlags.USE_MOCK_AI_REVIEW) {
        // Simulate network latency
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(mockAiReview(state));
            }, 2500); // Wait 2.5s
        });
    }

    // Real API call would go here
    const res = await fetch('YOUR_API_ENDPOINT', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            assetId: state.assetId,
            elapsedSeconds: state.elapsedSeconds,
            items: Object.entries(state.itemStates).map(([id, item]) => ({
                id,
                status: item.status,
                transcript: item.voiceNoteEditedTranscript || item.voiceNoteTranscript,
                timelineEstimate: item.timelineEstimate
            }))
        })
    });

    if (!res.ok) {
        throw new Error('Failed to generate AI review');
    }

    return res.json();
};
