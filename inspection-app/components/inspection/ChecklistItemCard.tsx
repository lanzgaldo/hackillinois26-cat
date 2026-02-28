import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, { useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { ChecklistItem, Status } from '../../constants/inspectionCategories';
import { useInspection } from '../../context/InspectionContext';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import StatusToggle from './StatusToggle';
import TimelineChipSelector from './TimelineChipSelector';
import PhotoCapture from '../shared/PhotoCapture';
import VoiceRecorder from '../shared/VoiceRecorder';
import AISuggestionChip from './AISuggestionChip';

interface Props {
    item: ChecklistItem;
}

export default function ChecklistItemCard({ item }: Props) {
    const { state, updateItemStatus } = useInspection();
    const itemState = state.itemStates[item.id] || { status: null };

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

            {itemState.status === 'red' && (
                <Animated.View style={[styles.redSubArea, expandStyle]}>
                    <Text style={styles.redHeader}>REQUIRED ACTION DETAILS</Text>

                    <View style={styles.actionRow}>
                        <VoiceRecorder itemId={item.id} />
                    </View>
                    <View style={[styles.actionRow, { marginTop: 12 }]}>
                        <PhotoCapture itemId={item.id} />
                    </View>
                </Animated.View>
            )}

            {item.id === 'eng_1' && itemState.status === 'red' && (
                <AISuggestionChip
                    suggestion="Oil level is critically low. Inspect underneath for active leaks."
                    onAccept={() => updateItemStatus(item.id, 'red')}
                    onDismiss={() => { }}
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
    },
    redSubArea: {
        marginTop: 16,
        paddingTop: 16,
        borderTopWidth: 1,
        borderTopColor: colors.border,
    },
    redHeader: {
        fontFamily: typography.families.ui,
        fontSize: typography.sizes.minimumLabel,
        color: colors.statusRed,
        marginBottom: 12,
    },
    actionRow: {
        flexDirection: 'row',
        gap: 16,
        alignItems: 'center',
    }
});
