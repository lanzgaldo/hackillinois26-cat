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
    const isComplete = true; // completed >= TOTAL_COMPLETED_REQUIRED; // Unlocked for easier testing

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
        paddingHorizontal: 16,
        paddingBottom: 24,  // breathing room above tab bar
        paddingTop: 12,
        gap: 12,
        backgroundColor: '#1A1A1A',
        borderTopWidth: 1,
        borderTopColor: '#333333',
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
