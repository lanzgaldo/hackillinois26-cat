import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Pressable, FlatList, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useInspection } from '../../../context/InspectionContext';
import { CATEGORIES } from '../../../constants/inspectionCategories';
import { getAllVoiceNoteUrisForSession, clearVoiceNotesForSession } from '../../../utils/voiceNoteStorage';
import { VoiceNoteCompilationPayload } from '../../../types/inspection';

// TODO: Replace with actual types from your app context/state
interface AiContext {
    voice_context: { raw_transcript: string };
    evidence_backed: boolean;
    preliminary_status: "STOP" | "CAUTION" | "GO";
    technician_review_flag: boolean;
    context_entries: {
        component: string;
        observation: string;
        severity: "CRITICAL" | "WARNING" | "INFO";
    }[];
    vision_raw?: string;
}

interface InspectionItem {
    id: string;
    name: string;
    status: "green" | "yellow" | "red";
    aiContext: any | null;
    aiPreliminaryStatus: "STOP" | "CAUTION" | "GO" | null;
    globalSafetyOverridePresent: boolean;
}

export default function ConfirmScreen() {
    const router = useRouter();
    const { state, submitInspection } = useInspection();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const shimmerAnim = useRef(new Animated.Value(0.3)).current;

    const [compilationPayload, setCompilationPayload] =
        useState<VoiceNoteCompilationPayload | null>(null);

    // PLACEHOLDER: sessionId should come from the active inspection session context
    // TODO: replace with real sessionId from global inspection session store
    const sessionId = state.assetId || 'PLACEHOLDER_SESSION_ID';

    useEffect(() => {
        (async () => {
            const clips = await getAllVoiceNoteUrisForSession(sessionId);

            if (clips.length === 0) return;

            // Assemble the compilation payload — ready for the AI overview POST in next sprint
            // PLACEHOLDER: items array is stubbed; TODO wire to real InspectionItem list from store
            const payload: VoiceNoteCompilationPayload = {
                inspectionId: sessionId,
                clips: clips.map(({ itemId, uri }) => ({
                    itemId,
                    itemName: 'PLACEHOLDER_ITEM_NAME', // TODO: look up real name from item store
                    voiceNoteUri: uri,
                    aiPreliminaryStatus: null, // TODO: look up from aiContext for this itemId
                })),
            };

            setCompilationPayload(payload);
        })();
    }, [sessionId]);

    const inspectionItems: InspectionItem[] = [];
    let globalSafetyOverride = false;
    let preliminaryStatus: "STOP" | "CAUTION" | "GO" = "GO";
    let technicianReview = false;
    let hasAiContext = false;

    CATEGORIES.forEach(category => {
        category.items.forEach(itemConfig => {
            const itemState = state.itemStates[itemConfig.id];
            if (itemState) {
                const ctx = itemState.aiContext;
                if (ctx) hasAiContext = true;

                const aiPreliminaryStatus = ctx?.preliminary_status || null;
                const isCritical = Array.isArray(ctx?.context_entries)
                    ? ctx.context_entries.some((e: any) => e.severity === 'CRITICAL')
                    : false;

                if (isCritical) globalSafetyOverride = true;
                if (ctx?.technician_review_flag) technicianReview = true;

                if (aiPreliminaryStatus === 'STOP') preliminaryStatus = 'STOP';
                else if (aiPreliminaryStatus === 'CAUTION' && preliminaryStatus !== 'STOP') preliminaryStatus = 'CAUTION';

                inspectionItems.push({
                    id: itemConfig.id,
                    name: itemConfig.name,
                    status: itemState.status as any,
                    aiContext: ctx || null,
                    aiPreliminaryStatus,
                    globalSafetyOverridePresent: isCritical
                });
            }
        });
    });

    useEffect(() => {
        Animated.loop(
            Animated.sequence([
                Animated.timing(shimmerAnim, {
                    toValue: 0.7,
                    duration: 800,
                    useNativeDriver: true,
                }),
                Animated.timing(shimmerAnim, {
                    toValue: 0.3,
                    duration: 800,
                    useNativeDriver: true,
                }),
            ])
        ).start();
    }, [shimmerAnim]);

    const renderItem = ({ item }: { item: InspectionItem }) => {
        let dotColor = '#4CAF50'; // green
        if (item.status === 'yellow') dotColor = '#FFCD11'; // yellow
        if (item.status === 'red') dotColor = '#F44336'; // red

        return (
            <Pressable style={styles.itemRow}>
                <View style={styles.itemLeft}>
                    <View style={[styles.statusDot, { backgroundColor: dotColor }]} />
                    <Text style={styles.itemText}>{item.name}</Text>
                </View>
                <Ionicons name="chevron-forward" size={24} color="#888" />
            </Pressable>
        );
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'STOP': return '#F44336';
            case 'CAUTION': return '#FFCD11';
            case 'GO': return '#4CAF50';
            default: return '#888';
        }
    };

    const handleBack = () => {
        router.back();
    };

    const handleConfirm = () => {
        setIsSubmitting(true);
        submitInspection();

        // PLACEHOLDER: Global AI overview compilation step — NOT active this sprint.
        // When the compilation endpoint is ready, replace this block with a real POST.
        // Payload is already assembled above in compilationPayload state.
        // After successful POST: call clearVoiceNotesForSession(sessionId)
        // TODO: POST compilationPayload to compilation endpoint before final submit
        console.log(
            '[VoiceNote] Compilation payload ready:',
            JSON.stringify(compilationPayload, null, 2)
        );

        router.replace('/(tabs)/inspections/review');
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            {/* 1. Header Bar */}
            <View style={styles.header}>
                <Pressable style={styles.backButton} onPress={handleBack}>
                    <Ionicons name="chevron-back" size={28} color="#FFF" />
                </Pressable>
                <Text style={styles.headerTitle}>Review & Confirm</Text>
                <Pressable
                    style={isSubmitting ? styles.submitButtonDisabled : styles.submitButtonActive}
                    disabled={isSubmitting}
                    onPress={handleConfirm}
                >
                    <Text style={isSubmitting ? styles.submitButtonTextDisabled : styles.submitButtonTextActive}>Submit</Text>
                </Pressable>
            </View>

            <View style={styles.content}>
                {/* 2. AI Overview Card */}
                <View style={styles.aiCard}>
                    <Text style={styles.aiCardTitle}>AI-Generated Overview</Text>

                    {/* CRITICAL OVERRIDE BANNER */}
                    {globalSafetyOverride && (
                        <View style={styles.criticalBanner}>
                            <Ionicons name="warning-outline" size={20} color="#FFF" style={styles.criticalIcon} />
                            <Text style={styles.criticalBannerText}>⚠ CRITICAL OVERRIDE</Text>
                        </View>
                    )}

                    {/* Preliminary Status Badge */}
                    <View style={[styles.statusBadge, { borderColor: getStatusColor(preliminaryStatus) }]}>
                        <Text style={[styles.statusBadgeText, { color: getStatusColor(preliminaryStatus) }]}>
                            {preliminaryStatus}
                        </Text>
                    </View>

                    {/* PLACEHOLDER: Voice note compilation readiness indicator */}
                    {compilationPayload && compilationPayload.clips.length > 0 ? (
                        <View style={styles.compilationBanner}>
                            <Ionicons name="layers-outline" size={16} color="#FFCD11" />
                            <Text style={styles.compilationBannerText}>
                                {compilationPayload.clips.length} voice note
                                {compilationPayload.clips.length !== 1 ? 's' : ''} queued for AI overview
                            </Text>
                            {/* TODO: replace this with a POST to the compilation endpoint on submit */}
                        </View>
                    ) : (
                        <View style={styles.compilationBanner}>
                            <Ionicons name="layers-outline" size={16} color="#9CA3AF" />
                            <Text style={styles.compilationBannerTextEmpty}>
                                No voice notes queued
                            </Text>
                        </View>
                    )}

                    <View style={styles.textSkeletonContainer}>
                        {!hasAiContext ? (
                            <>
                                <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim }]} />
                                <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim }]} />
                                <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim, width: '80%' }]} />
                                <Text style={styles.aiPlaceholderText} numberOfLines={4}>
                                    AI summary will appear here after voice and image analysis...
                                </Text>
                            </>
                        ) : (
                            <>
                                {inspectionItems
                                    .filter(i => i.aiContext)
                                    .flatMap(i => {
                                        // Support both real API schema (inspection_output.anomalies)
                                        // and legacy schema (context_entries)
                                        const output = i.aiContext?.inspection_output ?? i.aiContext;
                                        const anomalies: any[] = output?.anomalies ?? i.aiContext?.context_entries ?? [];
                                        return anomalies.map((a: any, idx: number) => ({
                                            key: `${i.id}-${idx}`,
                                            component: a.component ?? a.component_location ?? '—',
                                            severity: a.severity ?? a.severity_indicator ?? 'INFO',
                                            description: a.condition_description ?? a.observation ?? '',
                                            timeline: a.estimated_timeline ?? null,
                                        }));
                                    })
                                    .slice(0, 6)
                                    .map(entry => (
                                        <View key={entry.key} style={{ marginBottom: 8 }}>
                                            <Text style={{ color: entry.severity === 'Critical' || entry.severity === 'CRITICAL' ? '#F44336' : entry.severity === 'Moderate' || entry.severity === 'WARNING' ? '#FFCD11' : '#9CA3AF', fontSize: 11, fontWeight: '700', marginBottom: 2 }}>
                                                {entry.severity.toUpperCase()} · {entry.component}
                                            </Text>
                                            <Text style={styles.aiActiveText}>{entry.description}</Text>
                                            {entry.timeline && (
                                                <Text style={{ color: '#FFCD11', fontSize: 11, marginTop: 2 }}>⏱ {entry.timeline}</Text>
                                            )}
                                        </View>
                                    ))
                                }
                                {inspectionItems.filter(i => i.aiContext).length === 0 && (
                                    <Text style={styles.aiActiveText}>
                                        AI analysis complete — no anomalies flagged.
                                    </Text>
                                )}
                            </>
                        )}
                    </View>

                    {/* Technician Review Flag */}
                    {technicianReview && (
                        <View style={styles.technicianReviewRow}>
                            <Ionicons name="clipboard-outline" size={20} color="#FFCD11" />
                            <Text style={styles.technicianReviewText}>Technician Review Required</Text>
                        </View>
                    )}
                </View>

                {/* 3. Inspection Items List */}
                <Text style={styles.listHeader}>Inspection Items</Text>
                <FlatList
                    data={inspectionItems}
                    keyExtractor={(item) => item.id}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContent}
                    style={styles.list}
                    showsVerticalScrollIndicator={false}
                />
            </View>

            {/* 4. Footer Action Bar */}
            <View style={styles.footer}>
                <Pressable style={styles.footerSecondaryBtn} onPress={handleConfirm} disabled={isSubmitting}>
                    <Text style={styles.footerSecondaryText}>Save Without AI</Text>
                </Pressable>
                <Pressable style={styles.footerPrimaryBtn} onPress={handleConfirm} disabled={isSubmitting}>
                    <Text style={styles.footerPrimaryText}>Confirm & Submit</Text>
                </Pressable>
            </View>
        </SafeAreaView >
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        height: 64, // glove-friendly target
        borderBottomWidth: 1,
        borderBottomColor: '#333',
    },
    backButton: {
        height: 48,
        width: 48,
        justifyContent: 'center',
        alignItems: 'flex-start',
    },
    headerTitle: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    submitButtonDisabled: {
        height: 48,
        justifyContent: 'center',
        alignItems: 'flex-end',
        paddingHorizontal: 8,
    },
    submitButtonTextDisabled: {
        color: '#555',
        fontWeight: '600',
        fontSize: 16,
    },
    submitButtonActive: {
        height: 48,
        justifyContent: 'center',
        alignItems: 'flex-end',
        paddingHorizontal: 8,
    },
    submitButtonTextActive: {
        color: '#FFCD11',
        fontWeight: '600',
        fontSize: 16,
    },
    content: {
        flex: 1,
        padding: 16,
    },
    aiCard: {
        backgroundColor: '#2A2A2A',
        borderRadius: 8,
        padding: 16,
        marginBottom: 24,
        borderWidth: 1,
        borderColor: '#444',
    },
    aiCardTitle: {
        color: '#AAA',
        fontSize: 14,
        textTransform: 'uppercase',
        fontWeight: 'bold',
        marginBottom: 16,
    },
    compilationBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        backgroundColor: '#242424',
        borderRadius: 8,
        paddingHorizontal: 14,
        paddingVertical: 12,
        marginTop: 12,
        minHeight: 48,
    },
    compilationBannerText: {
        fontSize: 14,
        color: '#FFCD11',
        fontWeight: '600',
        flex: 1,
    },
    compilationBannerTextEmpty: {
        fontSize: 14,
        color: '#9CA3AF',
        flex: 1,
    },
    criticalBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#D32F2F',
        padding: 8,
        borderRadius: 4,
        marginBottom: 12,
    },
    criticalIcon: {
        marginRight: 8,
    },
    criticalBannerText: {
        color: '#FFF',
        fontWeight: 'bold',
        fontSize: 14,
    },
    statusBadge: {
        alignSelf: 'flex-start',
        borderWidth: 1,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
        marginBottom: 16,
    },
    statusBadgeText: {
        fontWeight: 'bold',
        fontSize: 12,
    },
    textSkeletonContainer: {
        marginBottom: 16,
    },
    textSkeletonLine: {
        height: 12,
        backgroundColor: '#444',
        borderRadius: 4,
        marginBottom: 8,
    },
    aiPlaceholderText: {
        color: '#888',
        fontStyle: 'italic',
        fontSize: 14,
        lineHeight: 20,
        marginTop: 8,
    },
    aiActiveText: {
        color: '#F2F0EB',
        fontSize: 14,
        lineHeight: 20,
        marginTop: 4,
    },
    technicianReviewRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 8,
        paddingTop: 16,
        borderTopWidth: 1,
        borderTopColor: '#444',
    },
    technicianReviewText: {
        color: '#FFCD11',
        marginLeft: 8,
        fontSize: 14,
        fontWeight: '600',
    },
    listHeader: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 12,
    },
    list: {
        flex: 1,
    },
    listContent: {
        paddingBottom: 80,
    },
    itemRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#2A2A2A',
        height: 64, // glove-friendly minimum height
        paddingHorizontal: 16,
        borderRadius: 8,
        marginBottom: 8,
    },
    itemLeft: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    statusDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 12,
    },
    itemText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: '500',
    },
    footer: {
        flexDirection: 'row',
        padding: 16,
        borderTopWidth: 1,
        borderTopColor: '#333',
        backgroundColor: '#1A1A1A',
        paddingBottom: 80, // tab bar clearance
    },
    footerSecondaryBtn: {
        flex: 1,
        height: 56, // glove-friendly height
        borderWidth: 1,
        borderColor: '#FFCD11',
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 8,
        marginRight: 8,
    },
    footerSecondaryText: {
        color: '#FFCD11',
        fontWeight: 'bold',
        fontSize: 16,
    },
    footerPrimaryBtn: {
        flex: 1,
        height: 56, // glove-friendly height
        backgroundColor: '#FFCD11',
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 8,
        marginLeft: 8,
    },
    footerPrimaryText: {
        color: '#080808', // Black text for high contrast on CAT yellow
        fontWeight: 'bold',
        fontSize: 16,
    },
});
