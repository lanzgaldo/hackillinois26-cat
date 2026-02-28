import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { useInspection } from '../../context/InspectionContext';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

const TWO_PI = Math.PI * 2;
const RADIUS = 16;
const CIRCUMFERENCE = TWO_PI * RADIUS;

export default function StickyInspectionHeader() {
    const { state } = useInspection();

    let redCount = 0;
    let yellowCount = 0;
    let greenCount = 0;
    let totalItems = 0;

    Object.values(state.itemStates).forEach(item => {
        totalItems++;
        if (item.status === 'red') redCount++;
        if (item.status === 'yellow') yellowCount++;
        if (item.status === 'green') greenCount++;
    });

    const TOTAL_INSPECTION_ITEMS = 12; // sum of mock items
    const completed = redCount + yellowCount + greenCount;
    const progress = totalItems > 0 ? completed / TOTAL_INSPECTION_ITEMS : 0;

    const animatedProgress = useSharedValue(0);

    useEffect(() => {
        animatedProgress.value = withTiming(progress, { duration: 500 });
    }, [progress]);

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <View style={styles.container}>
            <View style={styles.leftCol}>
                <Text style={styles.assetId}>{state.assetId || 'ASSET-291'}</Text>
                <Text style={styles.assetModel}>D8T DOZER</Text>
            </View>

            <View style={styles.centerCol}>
                <StatusBadge color={colors.statusRed} count={redCount} />
                <StatusBadge color={colors.statusYellow} count={yellowCount} />
                <StatusBadge color={colors.statusGreen} count={greenCount} />
            </View>

            <View style={styles.rightCol}>
                <Text style={styles.timer}>{formatTime(state.elapsedSeconds)}</Text>
                <View style={styles.progressRing}>
                    <Text style={styles.progressText}>{Math.round(progress * 100)}%</Text>
                </View>
            </View>
        </View>
    );
}

function StatusBadge({ color, count }: { color: string, count: number }) {
    return (
        <View style={[styles.badge, { borderColor: color }]}>
            <Text style={[styles.badgeText, { color }]}>{count}</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: colors.background,
        paddingHorizontal: 16,
        paddingVertical: 12,
        borderBottomWidth: 2,
        borderBottomColor: colors.primary,
        zIndex: 10,
    },
    leftCol: {
        flex: 1,
    },
    assetId: {
        fontFamily: typography.families.mono,
        fontSize: 16,
        color: colors.textPrimary,
    },
    assetModel: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        color: colors.textSecondary,
    },
    centerCol: {
        flexDirection: 'row',
        gap: 8,
        flex: 1,
        justifyContent: 'center',
    },
    badge: {
        borderWidth: 2,
        borderRadius: 16,
        paddingHorizontal: 8,
        paddingVertical: 2,
        minWidth: 32,
        alignItems: 'center',
    },
    badgeText: {
        fontFamily: typography.families.ui,
        fontSize: 14,
    },
    rightCol: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 12,
    },
    timer: {
        fontFamily: typography.families.mono,
        fontSize: 16,
        color: colors.textPrimary,
    },
    progressRing: {
        width: 36,
        height: 36,
        borderRadius: 18,
        borderWidth: 2,
        borderColor: colors.border,
        alignItems: 'center',
        justifyContent: 'center',
    },
    progressText: {
        fontFamily: typography.families.mono,
        fontSize: 10,
        color: colors.textSecondary,
    }
});
