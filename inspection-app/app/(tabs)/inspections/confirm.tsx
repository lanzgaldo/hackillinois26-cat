import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Pressable, FlatList, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

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
    aiContext: AiContext | null;
    aiPreliminaryStatus: "STOP" | "CAUTION" | "GO" | null;
    globalSafetyOverridePresent: boolean;
}

// PLACEHOLDER DATA
const placeholderItems: InspectionItem[] = [
    {
        id: "1",
        name: "Engine Oil Level",
        status: "green",
        aiContext: null,
        aiPreliminaryStatus: "GO",
        globalSafetyOverridePresent: false,
    },
    {
        id: "2",
        name: "Hydraulic System",
        status: "red",
        aiContext: null,
        aiPreliminaryStatus: "STOP",
        globalSafetyOverridePresent: true,
    },
    {
        id: "3",
        name: "Tire Pressure",
        status: "yellow",
        aiContext: null,
        aiPreliminaryStatus: "CAUTION",
        globalSafetyOverridePresent: false,
    },
];

// PLACEHOLDER CONSTANTS
const mockGlobalOverride = true;
const mockPreliminaryStatus: "STOP" | "CAUTION" | "GO" = "STOP";
const mockTechnicianReview = true;

export default function ConfirmScreen() {
    const shimmerAnim = useRef(new Animated.Value(0.3)).current;

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

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            {/* 1. Header Bar */}
            <View style={styles.header}>
                {/* PLACEHOLDER: Navigation back action required */}
                <Pressable style={styles.backButton}>
                    <Ionicons name="chevron-back" size={28} color="#FFF" />
                </Pressable>
                <Text style={styles.headerTitle}>Review & Confirm</Text>
                <Pressable style={styles.submitButtonDisabled} disabled>
                    <Text style={styles.submitButtonTextDisabled}>Submit</Text>
                </Pressable>
            </View>

            <View style={styles.content}>
                {/* 2. AI Overview Card */}
                <View style={styles.aiCard}>
                    <Text style={styles.aiCardTitle}>AI-Generated Overview</Text>

                    {/* CRITICAL OVERRIDE BANNER */}
                    {mockGlobalOverride && (
                        <View style={styles.criticalBanner}>
                            <Ionicons name="warning-outline" size={20} color="#FFF" style={styles.criticalIcon} />
                            <Text style={styles.criticalBannerText}>⚠ CRITICAL OVERRIDE</Text>
                        </View>
                    )}

                    {/* Preliminary Status Badge */}
                    <View style={[styles.statusBadge, { borderColor: getStatusColor(mockPreliminaryStatus) }]}>
                        <Text style={[styles.statusBadgeText, { color: getStatusColor(mockPreliminaryStatus) }]}>
                            {mockPreliminaryStatus}
                        </Text>
                    </View>

                    {/* Placeholder Animated Text Block */}
                    {/* PLACEHOLDER: Replace skeleton with actual text when data is loaded */}
                    <View style={styles.textSkeletonContainer}>
                        <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim }]} />
                        <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim }]} />
                        <Animated.View style={[styles.textSkeletonLine, { opacity: shimmerAnim, width: '80%' }]} />
                        <Text style={styles.aiPlaceholderText} numberOfLines={4}>
                            AI summary will appear here after voice and image analysis...
                        </Text>
                    </View>

                    {/* Technician Review Flag */}
                    {mockTechnicianReview && (
                        <View style={styles.technicianReviewRow}>
                            <Ionicons name="clipboard-outline" size={20} color="#FFCD11" />
                            <Text style={styles.technicianReviewText}>Technician Review Required</Text>
                        </View>
                    )}
                </View>

                {/* 3. Inspection Items List */}
                <Text style={styles.listHeader}>Inspection Items</Text>
                <FlatList
                    data={placeholderItems}
                    keyExtractor={(item) => item.id}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContent}
                    style={styles.list}
                    showsVerticalScrollIndicator={false}
                />
            </View>

            {/* 4. Footer Action Bar */}
            {/* PLACEHOLDER: Wire up onPress actions */}
            <View style={styles.footer}>
                <Pressable style={styles.footerSecondaryBtn}>
                    <Text style={styles.footerSecondaryText}>Save Without AI</Text>
                </Pressable>
                <Pressable style={styles.footerPrimaryBtn}>
                    <Text style={styles.footerPrimaryText}>Confirm & Submit</Text>
                </Pressable>
            </View>
        </SafeAreaView>
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
        paddingBottom: 24,
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
