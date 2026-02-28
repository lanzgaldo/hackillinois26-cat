import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../constants/colors';
import { typography } from '../constants/typography';

const MOCK_ASSETS = [
    { id: '1', assetId: 'D8T-004', model: 'D8T Track-Type Tractor', lastDate: '2026-02-26', status: 'green' },
    { id: '2', assetId: 'EX-920', model: '320 Hydraulic Excavator', lastDate: '2026-02-25', status: 'yellow' },
    { id: '3', assetId: 'WL-402', model: '950 GC Wheel Loader', lastDate: '2026-02-20', status: 'red' },
];

export default function DashboardScreen() {
    const router = useRouter();

    const handleStart = (assetId: string) => {
        router.push(`/inspections/${assetId}`);
    };

    const getStatusColor = (status: string) => {
        if (status === 'red') return colors.statusRed;
        if (status === 'yellow') return colors.statusYellow;
        return colors.statusGreen;
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.greeting}>GOOD MORNING, TECH</Text>
                <Text style={styles.date}>{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }).toUpperCase()}</Text>
                <View style={styles.badgeContainer}>
                    <Text style={styles.badgeText}>{MOCK_ASSETS.length} PENDING INSPECTIONS</Text>
                </View>
            </View>

            <ScrollView contentContainerStyle={styles.scrollContent}>
                {MOCK_ASSETS.map(asset => (
                    <View key={asset.id} style={styles.card}>
                        <View style={styles.cardHeader}>
                            <View>
                                <Text style={styles.assetId}>{asset.assetId}</Text>
                                <Text style={styles.model}>{asset.model}</Text>
                            </View>
                            <View style={[styles.statusDot, { backgroundColor: getStatusColor(asset.status) }]} />
                        </View>

                        <View style={styles.cardFooter}>
                            <Text style={styles.lastDate}>LAST INSP: {asset.lastDate}</Text>
                            <Pressable
                                style={styles.startButton}
                                onPress={() => handleStart(asset.assetId)}
                                accessibilityRole="button"
                                accessibilityLabel={`Start inspection for ${asset.assetId}`}
                            >
                                <Text style={styles.startText}>START</Text>
                                <Ionicons name="arrow-forward" size={20} color="#000" />
                            </Pressable>
                        </View>
                    </View>
                ))}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    header: {
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    greeting: {
        fontFamily: typography.families.display,
        fontSize: 32,
        color: colors.textPrimary,
    },
    date: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: colors.textSecondary,
        marginBottom: 12,
    },
    badgeContainer: {
        backgroundColor: colors.primaryDim,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
        alignSelf: 'flex-start',
        borderWidth: 1,
        borderColor: colors.primaryBorder,
    },
    badgeText: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: colors.primary,
    },
    scrollContent: {
        padding: 20,
        gap: 16,
    },
    card: {
        backgroundColor: colors.surfaceCard,
        borderRadius: 12,
        padding: 20,
        borderWidth: 1,
        borderColor: colors.border,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 24,
    },
    assetId: {
        fontFamily: typography.families.mono,
        fontSize: 24,
        color: colors.textPrimary,
        marginBottom: 4,
    },
    model: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: colors.textSecondary,
    },
    statusDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    cardFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    lastDate: {
        fontFamily: typography.families.mono,
        fontSize: 14,
        color: colors.textSecondary,
    },
    startButton: {
        backgroundColor: colors.primary,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingHorizontal: 24,
        height: 56, // Accessible touch target
        borderRadius: 28,
    },
    startText: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: '#000000', // High contrast on yellow
    }
});
