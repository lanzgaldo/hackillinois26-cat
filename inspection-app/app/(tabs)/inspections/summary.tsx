import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useInspection } from '../../../context/InspectionContext';
import { colors } from '../../../constants/colors';
import { typography } from '../../../constants/typography';
import { CATEGORIES } from '../../../constants/inspectionCategories';

export default function SummaryScreen() {
    const router = useRouter();
    const { state } = useInspection();

    let redCount = 0;
    let yellowCount = 0;
    let greenCount = 0;

    const redItems: any[] = [];
    const yellowItems: any[] = [];

    Object.entries(state.itemStates).forEach(([itemId, itemState]) => {
        if (itemState.status === 'red') {
            redCount++;
            const name = CATEGORIES.flatMap(c => c.items).find(i => i.id === itemId)?.name || itemId;
            redItems.push({ id: itemId, name, ...itemState });
        }
        if (itemState.status === 'yellow') {
            yellowCount++;
            const name = CATEGORIES.flatMap(c => c.items).find(i => i.id === itemId)?.name || itemId;
            yellowItems.push({ id: itemId, name, ...itemState });
        }
        if (itemState.status === 'green') greenCount++;
    });

    const generateParts = () => {
        router.push('/parts');
    };

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Text style={styles.header}>INSPECTION COMPLETE</Text>

                <View style={styles.tallyCard}>
                    <View style={styles.tallyItem}>
                        <Text style={[styles.tallyNumber, { color: colors.statusRed }]}>{redCount}</Text>
                        <Text style={styles.tallyLabel}>CRITICAL</Text>
                    </View>
                    <View style={styles.tallyItem}>
                        <Text style={[styles.tallyNumber, { color: colors.statusYellow }]}>{yellowCount}</Text>
                        <Text style={styles.tallyLabel}>WARNINGS</Text>
                    </View>
                    <View style={styles.tallyItem}>
                        <Text style={[styles.tallyNumber, { color: colors.statusGreen }]}>{greenCount}</Text>
                        <Text style={styles.tallyLabel}>PASS</Text>
                    </View>
                </View>

                {redItems.length > 0 && (
                    <View style={styles.section}>
                        <Text style={[styles.sectionTitle, { color: colors.statusRed }]}>REQUIRED ACTIONS</Text>
                        {redItems.map(item => (
                            <View key={item.id} style={styles.listItem}>
                                <Ionicons name="close-circle" size={24} color={colors.statusRed} />
                                <Text style={styles.listItemText}>{item.name}</Text>
                            </View>
                        ))}
                    </View>
                )}

                {yellowItems.length > 0 && (
                    <View style={styles.section}>
                        <Text style={[styles.sectionTitle, { color: colors.statusYellow }]}>WARNINGS</Text>
                        {yellowItems.map(item => (
                            <View key={item.id} style={styles.listItem}>
                                <Ionicons name="warning" size={24} color={colors.statusYellow} />
                                <View>
                                    <Text style={styles.listItemText}>{item.name}</Text>
                                    <Text style={styles.timelineText}>Est: {item.timelineEstimate}</Text>
                                </View>
                            </View>
                        ))}
                    </View>
                )}
            </ScrollView>

            <View style={styles.footer}>
                <Pressable style={styles.orderButton} onPress={generateParts} accessibilityRole="button">
                    <Text style={styles.orderButtonText}>GENERATE PARTS ORDER</Text>
                </Pressable>
                <Pressable style={styles.shareButton} onPress={() => router.replace('/(tabs)/inspections' as any)} accessibilityRole="button">
                    <Text style={styles.shareText}>RETURN TO DASHBOARD</Text>
                </Pressable>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollContent: {
        padding: 20,
        paddingBottom: 40,
    },
    header: {
        fontFamily: typography.families.display,
        fontSize: 32,
        color: colors.textPrimary,
        textAlign: 'center',
        marginVertical: 24,
    },
    tallyCard: {
        flexDirection: 'row',
        backgroundColor: colors.surfaceCard,
        borderRadius: 16,
        padding: 24,
        borderWidth: 1,
        borderColor: colors.border,
        marginBottom: 32,
    },
    tallyItem: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
    tallyNumber: {
        fontFamily: typography.families.mono,
        fontSize: 48,
        lineHeight: 56,
    },
    tallyLabel: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: colors.textSecondary,
        marginTop: 8,
    },
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        fontFamily: typography.families.ui,
        fontSize: 18,
        marginBottom: 16,
    },
    listItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.surfaceCard,
        padding: 16,
        borderRadius: 8,
        marginBottom: 8,
        gap: 12,
    },
    listItemText: {
        fontFamily: typography.families.bodyMedium,
        fontSize: 16,
        color: colors.textPrimary,
    },
    timelineText: {
        fontFamily: typography.families.mono,
        fontSize: 12,
        color: colors.statusYellow,
        marginTop: 4,
    },
    footer: {
        padding: 20,
        paddingBottom: 40,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        backgroundColor: colors.background,
        gap: 16,
    },
    orderButton: {
        backgroundColor: colors.primary,
        height: 64,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    orderButtonText: {
        fontFamily: typography.families.display,
        fontSize: 24,
        color: '#000000',
    },
    shareButton: {
        height: 56,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: colors.border,
        alignItems: 'center',
        justifyContent: 'center',
    },
    shareText: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: colors.textPrimary,
    }
});
