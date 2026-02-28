import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { useInspection } from '../../context/InspectionContext';

interface Props {
    onSubmit: () => void;
    onDraft?: () => void;
}

export default function BottomActionBar({ onSubmit, onDraft }: Props) {
    const { state } = useInspection();

    let completed = 0;
    Object.values(state.itemStates).forEach(item => {
        if (item.status) completed++;
    });

    const TOTAL_COMPLETED_REQUIRED = 12; // Mock total
    const isComplete = completed >= TOTAL_COMPLETED_REQUIRED;

    return (
        <View style={styles.container}>
            <Pressable style={styles.draftButton} onPress={onDraft} accessibilityRole="button">
                <Text style={styles.draftText}>SAVE DRAFT</Text>
            </Pressable>

            <Pressable
                style={[
                    styles.submitButton,
                    { backgroundColor: isComplete ? colors.primary : colors.elevatedSurface }
                ]}
                onPress={() => isComplete && onSubmit()}
                disabled={!isComplete}
                accessibilityRole="button"
            >
                {!isComplete && <Ionicons name="lock-closed" size={20} color={colors.textSecondary} style={{ marginRight: 8 }} />}
                <Text style={[styles.submitText, { color: isComplete ? '#000000' : colors.textSecondary }]}>
                    SUBMIT INSPECTION
                </Text>
            </Pressable>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        padding: 16,
        paddingBottom: 32, // Safe area padding approx
        backgroundColor: colors.background,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        gap: 12,
    },
    draftButton: {
        flex: 1,
        height: 64, // Touch target req
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: 8,
    },
    draftText: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: colors.textPrimary,
    },
    submitButton: {
        flex: 2,
        height: 64,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 8,
    },
    submitText: {
        fontFamily: typography.families.ui,
        fontSize: 18,
    }
});
