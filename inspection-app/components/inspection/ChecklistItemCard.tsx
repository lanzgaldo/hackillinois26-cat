import React, { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, { useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { ChecklistItem, Status } from '../../constants/inspectionCategories';
import { useInspection } from '../../context/InspectionContext';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import StatusToggle from './StatusToggle';
import TimelineChipSelector from './TimelineChipSelector';
import AISuggestionChip from './AISuggestionChip';
import AttachmentRow from './AttachmentRow';
import TranscriptReviewSheet from './TranscriptReviewSheet';

interface Props {
    item: ChecklistItem;
}

export default function ChecklistItemCard({ item }: Props) {
    const { state, updateItemStatus, updateItemVoiceNote, addItemPhoto, removeItemPhoto } = useInspection();
    const itemState = state.itemStates[item.id] || { status: null };
    const [pendingTranscript, setPendingTranscript] = useState<{ text: string } | null>(null);

    const handleStatusChange = (status: Status) => {
        updateItemStatus(item.id, status, itemState.timelineEstimate);
    };

    const handleTimelineSelect = (timeline: string) => {
        updateItemStatus(item.id, 'yellow', timeline);
    };

    const expandStyle = useAnimatedStyle(() => {
        const isExpanded = itemState.status === 'red' || itemState.status === 'yellow';
        return {
            opacity: withSpring(isExpanded ? 1 : 0),
        };
    });

    return (
        <View style={styles.card}>
            <Text style={styles.itemName}>{item.name}</Text>

            <StatusToggle value={itemState.status} onChange={handleStatusChange} />

            {itemState.status === 'yellow' && (
                <TimelineChipSelector
                    selected={itemState.timelineEstimate}
                    onSelect={handleTimelineSelect}
                />
            )}

            <AttachmentRow
                itemId={item.id}
                voiceNoteUri={itemState.voiceNoteUri || null}
                voiceNoteTranscript={itemState.voiceNoteEditedTranscript || itemState.voiceNoteTranscript || null}
                photos={itemState.photos || []}
                onVoiceStart={() => { }}
                onVoiceStop={(uri) => updateItemVoiceNote(item.id, uri, null)}
                onPhotoCapture={(uri) => addItemPhoto(item.id, uri)}
                onPhotoRemove={(uri) => removeItemPhoto(item.id, uri)}
                onTranscriptReady={(transcript) => setPendingTranscript({ text: transcript })}
            />

            {item.id === 'eng_1' && itemState.status === 'red' && (
                <AISuggestionChip
                    suggestion="Oil level is critically low. Inspect underneath for active leaks."
                    onAccept={() => updateItemStatus(item.id, 'red')}
                    onDismiss={() => { }}
                />
            )}

            {pendingTranscript && (
                <TranscriptReviewSheet
                    visible={!!pendingTranscript}
                    itemName={item.name}
                    initialTranscript={pendingTranscript.text}
                    onSave={(finalText, wasEdited) => {
                        updateItemVoiceNote(
                            item.id,
                            itemState.voiceNoteUri || null,
                            pendingTranscript.text,
                            wasEdited ? finalText : null
                        );
                        setPendingTranscript(null);
                    }}
                    onCancel={() => setPendingTranscript(null)}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: colors.surfaceCard,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: colors.border,
        padding: 16,
        marginBottom: 16,
    },
    itemName: {
        fontFamily: typography.families.ui,
        fontSize: typography.sizes.body,
        color: colors.textPrimary,
        marginBottom: 16,
    }
});
