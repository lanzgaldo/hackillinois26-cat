import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, withSequence } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useInspection } from '../../../context/InspectionContext';
import { colors } from '../../../constants/colors';
import { typography } from '../../../constants/typography';
import { CATEGORIES } from '../../../constants/inspectionCategories';

export default function AIReviewScreen() {
    const router = useRouter();
    const { state } = useInspection();

    let greenCount = 0;
    let yellowCount = 0;
    let redCount = 0;

    const redItems: any[] = [];
    const yellowItems: any[] = [];

    Object.entries(state.itemStates).forEach(([itemId, itemState]) => {
        if (itemState.status === 'green') greenCount++;
        if (itemState.status === 'yellow') {
            yellowCount++;
            const name = CATEGORIES.flatMap(c => c.items).find(i => i.id === itemId)?.name || itemId;
            yellowItems.push({ id: itemId, name, ...itemState });
        }
        if (itemState.status === 'red') {
            redCount++;
            const name = CATEGORIES.flatMap(c => c.items).find(i => i.id === itemId)?.name || itemId;
            redItems.push({ id: itemId, name, ...itemState });
        }
    });

    const totalCount = greenCount + yellowCount + redCount;
    const score = totalCount > 0 ? Math.round(((greenCount * 1.0 + yellowCount * 0.5 + redCount * 0.0) / totalCount) * 100) : 0;

    let scoreColor = colors.statusGreen;
    if (score < 50) scoreColor = colors.statusRed;
    else if (score < 80) scoreColor = colors.statusYellow;

    const shimmerOpacity = useSharedValue(0.3);

    useEffect(() => {
        if (state.aiReviewLoading) {
            shimmerOpacity.value = withRepeat(
                withSequence(
                    withTiming(0.7, { duration: 800 }),
                    withTiming(0.3, { duration: 800 })
                ),
                -1,
                true
            );
        }
    }, [state.aiReviewLoading]);

    const shimmerStyle = useAnimatedStyle(() => ({
        opacity: shimmerOpacity.value
    }));

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={styles.identityBar}>
                    <Text style={styles.assetModel}>{state.assetId || 'UNKNOWN'} — D8T DOZER</Text>
                    <Text style={styles.title}>AI INSPECTION OVERVIEW</Text>
                    <Text style={styles.timestamp}>SUBMITTED TODAY AT {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</Text>
                </View>

                <View style={styles.divider} />

                <View style={styles.scoreBlock}>
                    <Text style={[styles.scoreNumber, { color: scoreColor }]}>{score}</Text>
                    <Text style={styles.scoreLabel}>EQUIPMENT HEALTH SCORE</Text>
                </View>

                <View style={styles.divider} />

                <View style={styles.narrativeBlock}>
                    <Text style={styles.sectionLabel}>OVERVIEW</Text>
                    {state.aiReviewLoading ? (
                        <View style={styles.skeletonContainer}>
                            <Animated.View style={[styles.skeletonLine, shimmerStyle]} />
                            <Animated.View style={[styles.skeletonLine, shimmerStyle]} />
                            <Animated.View style={[styles.skeletonLine, shimmerStyle, { width: '80%' }]} />
                            <Animated.View style={[styles.skeletonLine, shimmerStyle, { width: '60%' }]} />
                            <Text style={styles.analyzingText}>AI is analyzing your inspection...</Text>
                        </View>
                    ) : state.aiReviewError ? (
                        <Text style={styles.errorText}>AI overview unavailable. Proceeding with manual summary.</Text>
                    ) : state.aiReview ? (
                        <>
                            <Text style={styles.narrativeText}>{state.aiReview.narrative}</Text>
                            {state.aiReview.urgentFlags.map((flag, idx) => (
                                <Text key={idx} style={styles.urgentFlagText}>• {flag}</Text>
                            ))}
                            <Text style={styles.recommendedText}>Recommendation: {state.aiReview.recommendedAction}</Text>
                        </>
                    ) : null}
                </View>

                <View style={styles.listBlock}>
                    <Text style={[styles.listLabel, { color: colors.statusRed }]}>CRITICAL — IMMEDIATE ACTION</Text>
                    {redItems.length === 0 ? (
                        <Text style={[styles.emptyText, { color: colors.statusGreen }]}>NO CRITICAL ITEMS FOUND</Text>
                    ) : (
                        redItems.map(item => (
                            <View key={item.id} style={[styles.itemRow, styles.redRow]}>
                                <View style={[styles.dot, { backgroundColor: colors.statusRed }]} />
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.itemName}>{item.name}</Text>
                                    <Text style={styles.transcriptSnippet} numberOfLines={1}>
                                        {(item.voiceNoteEditedTranscript || item.voiceNoteTranscript || 'No voice note attached').substring(0, 60)}
                                    </Text>
                                </View>
                            </View>
                        ))
                    )}
                </View>

                <View style={[styles.listBlock, { marginTop: 24 }]}>
                    <Text style={[styles.listLabel, { color: colors.statusYellow }]}>MONITOR — ACTION REQUIRED</Text>
                    {yellowItems.length === 0 ? (
                        <Text style={[styles.emptyText, { color: colors.statusGreen }]}>NO ITEMS REQUIRING MONITORING</Text>
                    ) : (
                        yellowItems.map(item => (
                            <View key={item.id} style={[styles.itemRow, styles.yellowRow]}>
                                <View style={[styles.dot, { backgroundColor: colors.statusYellow }]} />
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.itemName}>{item.name}</Text>
                                    <Text style={styles.timelineEstimate}>Timeline: {item.timelineEstimate}</Text>
                                </View>
                            </View>
                        ))
                    )}
                </View>

                <View style={[styles.listBlock, { marginTop: 24, marginBottom: 40 }]}>
                    <Text style={[styles.listLabel, { color: colors.statusGreen }]}>PASSED</Text>
                    <View style={[styles.itemRow, styles.greenRow]}>
                        <Text style={[styles.itemName, { color: colors.statusGreen }]}>{greenCount} ITEMS PASSED</Text>
                    </View>
                </View>

                <Text style={styles.disclaimerText}>
                    AI overview is advisory only. Technician judgment supersedes all AI-generated content.
                </Text>
            </ScrollView>

            <View style={styles.footer}>
                {!state.isSubmitted && (
                    <Pressable style={styles.backButton} onPress={() => router.back()} accessibilityRole="button">
                        <Text style={styles.backButtonText}>BACK</Text>
                    </Pressable>
                )}
                <Pressable
                    style={[styles.fullReportButton, state.isSubmitted ? { flex: 1 } : undefined]}
                    onPress={() => router.replace('/(tabs)/inspections/summary')}
                    accessibilityRole="button"
                >
                    <Text style={styles.fullReportText}>VIEW FULL REPORT</Text>
                </Pressable>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollContent: {
        padding: 24,
        paddingBottom: 80,
    },
    identityBar: {
        marginBottom: 20,
    },
    assetModel: {
        fontFamily: typography.families.mono,
        color: colors.primary,
        fontSize: 14,
        marginBottom: 8,
    },
    title: {
        fontFamily: typography.families.display,
        color: '#FFFFFF',
        fontSize: 28,
        textTransform: 'uppercase',
        marginBottom: 8,
    },
    timestamp: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#888',
    },
    divider: {
        width: '100%',
        height: 1,
        backgroundColor: '#2A2A2A',
        marginVertical: 20,
    },
    scoreBlock: {
        alignItems: 'center',
        marginVertical: 12,
    },
    scoreNumber: {
        fontFamily: typography.families.display,
        fontSize: 80,
        lineHeight: 90,
    },
    scoreLabel: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        color: '#888',
        marginTop: 4,
    },
    narrativeBlock: {
        marginBottom: 32,
    },
    sectionLabel: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        color: '#888',
        textTransform: 'uppercase',
        marginBottom: 12,
    },
    skeletonContainer: {
        gap: 8,
    },
    skeletonLine: {
        height: 16,
        backgroundColor: '#2A2A2A',
        borderRadius: 4,
        width: '100%',
    },
    analyzingText: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#666',
        marginTop: 12,
    },
    errorText: {
        fontFamily: typography.families.body,
        fontSize: 15,
        color: '#888',
    },
    narrativeText: {
        fontFamily: typography.families.body,
        fontSize: 15,
        color: '#F2F0EB',
        lineHeight: 24,
    },
    urgentFlagText: {
        fontFamily: typography.families.body,
        fontSize: 15,
        color: colors.statusRed,
        lineHeight: 24,
        marginTop: 8,
    },
    recommendedText: {
        fontFamily: typography.families.ui,
        fontSize: 15,
        color: colors.primary,
        lineHeight: 24,
        marginTop: 12,
    },
    listBlock: {
        marginBottom: 8,
    },
    listLabel: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        marginBottom: 12,
    },
    itemRow: {
        flexDirection: 'row',
        padding: 12,
        borderRadius: 4,
        alignItems: 'center',
        marginBottom: 8,
        gap: 12,
    },
    redRow: {
        backgroundColor: 'rgba(229, 57, 53, 0.08)',
        borderLeftWidth: 3,
        borderLeftColor: colors.statusRed,
    },
    yellowRow: {
        backgroundColor: 'rgba(255, 205, 17, 0.08)',
        borderLeftWidth: 3,
        borderLeftColor: colors.statusYellow,
    },
    greenRow: {
        backgroundColor: 'rgba(67, 160, 71, 0.06)',
        borderLeftWidth: 3,
        borderLeftColor: colors.statusGreen,
    },
    dot: {
        width: 8,
        height: 8,
        borderRadius: 4,
    },
    itemName: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: '#FFFFFF',
    },
    transcriptSnippet: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#888',
        marginTop: 4,
    },
    timelineEstimate: {
        fontFamily: typography.families.mono,
        fontSize: 12,
        color: colors.statusYellow,
        marginTop: 4,
    },
    emptyText: {
        fontFamily: typography.families.ui,
        fontSize: 14,
    },
    disclaimerText: {
        fontFamily: typography.families.body,
        fontSize: 12,
        color: '#444',
        textAlign: 'center',
    },
    footer: {
        flexDirection: 'row',
        padding: 20,
        paddingBottom: 80, // tab bar clearance
        gap: 12,
        backgroundColor: '#080808',
        borderTopWidth: 1,
        borderTopColor: '#2A2A2A',
    },
    backButton: {
        height: 56,
        borderWidth: 1,
        borderColor: '#444',
        borderRadius: 8,
        paddingHorizontal: 24,
        alignItems: 'center',
        justifyContent: 'center',
    },
    backButtonText: {
        fontFamily: typography.families.ui,
        fontSize: 15,
        color: '#FFFFFF',
    },
    fullReportButton: {
        flex: 1,
        height: 56,
        backgroundColor: colors.primary,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    fullReportText: {
        fontFamily: typography.families.display,
        fontSize: 20,
        color: '#080808',
    }
});
