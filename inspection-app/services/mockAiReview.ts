import { InspectionState, AIReview } from '../context/InspectionContext';

export const mockAiReview = (state: InspectionState): AIReview => {
    let redCount = 0;
    let yellowCount = 0;
    const urgentFlags: string[] = [];

    Object.entries(state.itemStates).forEach(([id, item]) => {
        if (item.status === 'red') {
            redCount++;
            urgentFlags.push(`Critical issue identified on item ${id}.`);
        } else if (item.status === 'yellow') {
            yellowCount++;
        }
    });

    let narrative = `Inspection for asset ${state.assetId || 'unknown'} completed. `;
    if (redCount > 0) {
        narrative += `There are ${redCount} critical failures requiring immediate maintenance. `;
    } else {
        narrative += 'No critical issues were found during this inspection. ';
    }

    if (yellowCount > 0) {
        narrative += `Additionally, ${yellowCount} items have been flagged for monitoring and may require service in the future. `;
    }

    narrative += 'The overall condition needs attention according to the timeline estimates provided in the report.';

    return {
        narrative,
        urgentFlags,
        recommendedAction: redCount > 0 ? "Ground machine and schedule maintenance immediately." : "Machine cleared for operation. Schedule standard PMs.",
    };
};
