import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

export default function PartsOrderScreen() {
    const router = useRouter();

    // Mock mapped parts
    const MOCK_PARTS = [
        { id: '1', name: 'D8T Oil Filter Assy', partNo: '1R-0716', lead: 'In Stock', criticality: 'HIGH' },
        { id: '2', name: 'Hydraulic Hose - 48"', partNo: '244-5121', lead: '2 Days', criticality: 'MED' },
    ];

    const [quantities, setQuantities] = useState<Record<string, number>>(
        MOCK_PARTS.reduce((acc, part) => ({ ...acc, [part.id]: 1 }), {})
    );

    const updateQuantity = (id: string, delta: number) => {
        setQuantities(prev => {
            const current = prev[id] || 0;
            const next = current + delta;
            return { ...prev, [id]: next >= 0 ? next : 0 };
        });
    };

    const totalItems = Object.values(quantities).reduce((a, b) => a + b, 0);

    const handleSubmit = () => {
        Alert.alert('Order Submitted', `Successfully ordered ${totalItems} parts.`);
        router.replace('/(tabs)/inspections' as any);
    };

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Text style={styles.header}>PARTS REQUISITION</Text>

                {MOCK_PARTS.map(part => (
                    <View key={part.id} style={styles.card}>
                        <View style={styles.cardHeader}>
                            <View>
                                <Text style={styles.partName}>{part.name}</Text>
                                <Text style={styles.partNo}>{part.partNo}</Text>
                            </View>
                            <View style={[styles.badge, { backgroundColor: part.criticality === 'HIGH' ? colors.statusRedDim : colors.statusYellowDim }]}>
                                <Text style={[styles.badgeText, { color: part.criticality === 'HIGH' ? colors.statusRed : colors.statusYellow }]}>
                                    {part.criticality}
                                </Text>
                            </View>
                        </View>

                        <View style={styles.cardFooter}>
                            <Text style={styles.leadTime}>LEAD: {part.lead}</Text>

                            <View style={styles.counter}>
                                <Pressable style={styles.counterButton} onPress={() => updateQuantity(part.id, -1)} accessibilityRole="button">
                                    <Ionicons name="remove" size={24} color={colors.textPrimary} />
                                </Pressable>

                                <Text style={styles.countText}>{quantities[part.id]}</Text>

                                <Pressable style={styles.counterButton} onPress={() => updateQuantity(part.id, 1)} accessibilityRole="button">
                                    <Ionicons name="add" size={24} color={colors.textPrimary} />
                                </Pressable>
                            </View>
                        </View>
                    </View>
                ))}
            </ScrollView>

            <View style={styles.footer}>
                <View style={styles.totalRow}>
                    <Text style={styles.totalLabel}>TOTAL ITEMS:</Text>
                    <Text style={styles.totalValue}>{totalItems}</Text>
                </View>
                <Pressable
                    style={[styles.submitButton, { opacity: totalItems === 0 ? 0.5 : 1 }]}
                    onPress={handleSubmit}
                    disabled={totalItems === 0}
                    accessibilityRole="button"
                >
                    <Text style={styles.submitText}>SUBMIT ORDER</Text>
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
        fontFamily: typography.families.ui,
        fontSize: 24,
        color: colors.textPrimary,
        marginBottom: 24,
    },
    card: {
        backgroundColor: colors.surfaceCard,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: colors.border,
        padding: 20,
        marginBottom: 16,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 24,
    },
    partName: {
        fontFamily: typography.families.ui,
        fontSize: 18,
        color: colors.textPrimary,
        marginBottom: 4,
    },
    partNo: {
        fontFamily: typography.families.mono,
        fontSize: 16,
        color: colors.textSecondary,
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    badgeText: {
        fontFamily: typography.families.mono,
        fontSize: 12,
    },
    cardFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    leadTime: {
        fontFamily: typography.families.mono,
        fontSize: 14,
        color: colors.textSecondary,
    },
    counter: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 16,
    },
    counterButton: {
        width: 64, // Touch target
        height: 64,
        borderRadius: 32,
        backgroundColor: colors.elevatedSurface,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: colors.border,
    },
    countText: {
        fontFamily: typography.families.mono,
        fontSize: 24,
        color: colors.textPrimary,
        width: 32,
        textAlign: 'center',
    },
    footer: {
        padding: 20,
        paddingBottom: 40,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        backgroundColor: colors.background,
    },
    totalRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
    },
    totalLabel: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: colors.textSecondary,
    },
    totalValue: {
        fontFamily: typography.families.mono,
        fontSize: 24,
        color: colors.textPrimary,
    },
    submitButton: {
        backgroundColor: colors.primary,
        height: 64,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    submitText: {
        fontFamily: typography.families.display,
        fontSize: 24,
        color: '#000000',
    }
});
