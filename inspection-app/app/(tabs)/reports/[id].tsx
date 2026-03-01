import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { CompletedInspection } from '../../../types/inspection';

const PLACEHOLDER_REPORTS: CompletedInspection[] = [
    {
        id: '1',
        title: 'D6 Dozer Pre-Op – March 2025',
        formNumber: 'PM-2025-00847',
        formType: 'Preventive Maintenance',
        assetId: 'CAT-00294',
        serialNumber: 'GSD01234',
        model: 'D6 XE',
        customer: 'Blackridge Construction',
        submittedAt: '2025-03-14T08:32:00Z',
        submittedBy: 'J. Hartwell',
        status: 'red',
        overallRating: 'red',
        partsRating: 61,
        severity: 'CRITICAL',
        summary: 'AI-generated summary placeholder text for this inspection report.',
        actionableItems: ['Replace left track pad assembly', 'Inspect hydraulic line seal'],
        items: [],
    },
    {
        id: '2',
        title: '966 Wheel Loader PM – Feb 2025',
        formNumber: 'PM-2025-00731',
        formType: 'Preventive Maintenance',
        assetId: 'CAT-00511',
        serialNumber: 'BXK09872',
        model: '966 XE',
        submittedAt: '2025-02-28T14:10:00Z',
        submittedBy: 'R. Morales',
        status: 'yellow',
        overallRating: 'yellow',
        partsRating: 78,
        severity: 'WARNING',
        summary: 'AI-generated summary placeholder for wheel loader inspection.',
        actionableItems: ['Monitor tire pressure weekly', 'Schedule bucket edge replacement'],
        items: [],
    },
    {
        id: '3',
        title: 'Cat 320 Excavator Annual',
        formNumber: 'TA-2025-00412',
        formType: 'Technical Analysis (TA-1)',
        assetId: 'CAT-00189',
        serialNumber: 'MJK55301',
        model: 'Cat 320',
        customer: 'Dunmore Earthworks',
        submittedAt: '2025-01-15T09:45:00Z',
        submittedBy: 'J. Hartwell',
        status: 'green',
        overallRating: 'green',
        partsRating: 94,
        severity: 'INFO',
        summary: 'Excavator within normal operating parameters. No immediate action required.',
        actionableItems: ['Continue standard PM schedule'],
        items: [{
            id: 'i1',
            name: 'Engine Oil',
            category: 'Engine',
            status: 'green',
            voiceNoteUri: null,
            voiceNoteTranscript: null,
            voiceNoteEditedTranscript: null,
            photos: [],
            timelineEstimate: null,
            aiContext: null,
            aiPreliminaryStatus: null,
            globalSafetyOverridePresent: false
        }],
    },
    {
        id: '4',
        title: 'D8 Dozer Daily Walkaround',
        formNumber: 'DW-2025-01003',
        formType: 'Daily Safety Walkaround',
        assetId: 'CAT-00672',
        serialNumber: 'PRX77821',
        model: 'D8T',
        submittedAt: '2025-03-01T06:20:00Z',
        submittedBy: 'T. Okafor',
        status: 'yellow',
        overallRating: 'yellow',
        partsRating: 82,
        severity: 'WARNING',
        summary: 'Minor fluid seep detected near rear final drive. Flagged for technician review.',
        actionableItems: ['Inspect rear final drive seal', 'Check fluid levels before next shift'],
        items: [],
    },
    {
        id: '5',
        title: 'CB13 Compactor Pre-Season',
        formNumber: 'PM-2025-00290',
        formType: 'Preventive Maintenance',
        assetId: 'CAT-00403',
        serialNumber: 'CMP44102',
        model: 'CB13',
        customer: 'Vortex Paving Co.',
        submittedAt: '2025-02-05T11:00:00Z',
        submittedBy: 'R. Morales',
        status: 'green',
        overallRating: 'green',
        partsRating: 91,
        severity: 'INFO',
        summary: 'All systems operational. Unit cleared for seasonal deployment.',
        actionableItems: [],
        items: [],
    },
];

const getStatusColor = (status: string) => {
    switch (status) {
        case 'green': case 'GO': return '#4CAF50';
        case 'yellow': case 'CAUTION': return '#F59E0B';
        case 'red': case 'STOP': return '#D32F2F';
        default: return '#9CA3AF';
    }
}

const getSeverityStyle = (severity: string) => {
    switch (severity) {
        case 'CRITICAL': return { bg: '#D32F2F', color: '#FFFFFF' };
        case 'WARNING': return { bg: '#F59E0B', color: '#000000' };
        case 'INFO': return { bg: '#374151', color: '#FFFFFF' };
        default: return { bg: '#374151', color: '#FFFFFF' };
    }
}

export default function ReportDetailScreen() {
    const { id, mode } = useLocalSearchParams<{ id: string; mode?: string }>();
    const router = useRouter();

    const report = PLACEHOLDER_REPORTS.find(r => r.id === id) ?? PLACEHOLDER_REPORTS[0];

    // Helpers
    const getPartsRatingText = (score: number) => {
        if (score >= 90) return { text: "Excellent condition", color: "#4CAF50" };
        if (score >= 70) return { text: "Good — minor attention needed", color: "#F59E0B" };
        if (score >= 50) return { text: "Fair — schedule service soon", color: "#F59E0B" };
        return { text: "Poor — immediate action required", color: "#D32F2F" };
    };

    const getOverallRatingString = (rating: string) => {
        if (rating === 'green') return 'GO';
        if (rating === 'yellow') return 'CAUTION';
        return 'STOP';
    };

    // PLACEHOLDER: until real items are wired, use hardcoded placeholder counts
    // TODO: replace with real computed values from report.items
    let criticalCount = 0;
    let warningCount = 0;
    let okCount = 0;
    let naCount = 0;

    if (report.id === '1') { criticalCount = 1; warningCount = 2; okCount = 3; naCount = 0; }
    else if (report.id === '2') { criticalCount = 0; warningCount = 0; okCount = 6; naCount = 0; }
    else if (report.id === '3') { criticalCount = 2; warningCount = 1; okCount = 4; naCount = 1; }
    else if (report.id === '4') { criticalCount = 0; warningCount = 3; okCount = 2; naCount = 0; }
    else if (report.id === '5') { criticalCount = 1; warningCount = 0; okCount = 5; naCount = 0; }

    const severityStyle = getSeverityStyle(report.severity);
    const bannerColor = getStatusColor(report.overallRating);
    const isYellow = report.overallRating === 'yellow';

    return (
        <ScrollView
            style={styles.container}
            contentContainerStyle={styles.scrollContent}
            bounces={false}
            showsVerticalScrollIndicator={false}
            scrollIndicatorInsets={{ right: 1 }}
        >
            {/* 1. Custom Header Row */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.headerButton} activeOpacity={0.6} hitSlop={{ top: 16, bottom: 16, left: 16, right: 16 }}>
                    <Ionicons name="arrow-back" size={28} color="#FFFFFF" />
                    <Text style={styles.headerBackText}>Reports</Text>
                </TouchableOpacity>
                <View style={styles.headerTitleSpacer} />
                <TouchableOpacity onPress={() => {/* TODO: generate and forward PDF report via email */ }} style={styles.headerButtonRight} activeOpacity={0.6} hitSlop={{ top: 16, bottom: 16, left: 16, right: 16 }}>
                    <Ionicons name="share-outline" size={26} color="#C0C0C0" />
                </TouchableOpacity>
            </View>

            {/* NEW: Top Status Banner */}
            <View style={[styles.statusBanner, { backgroundColor: bannerColor }]}>
                <Text style={[styles.statusBannerText, { color: isYellow ? '#000000' : '#FFFFFF' }]}>
                    {getOverallRatingString(report.overallRating)}
                </Text>
            </View>

            {mode && (
                <View style={styles.modeBanner}>
                    <Text style={styles.modeBannerText}>
                        {/* PLACEHOLDER: section will reorder based on mode in next sprint */}
                        Viewing: {mode.toUpperCase()}
                    </Text>
                </View>
            )}

            {/* 2. Title Block */}
            <View style={styles.titleBlock}>
                <View style={styles.titleRow}>
                    <Text style={styles.titleText}>{report.title}</Text>
                    <View style={[styles.badgePill, { backgroundColor: severityStyle.bg }]}>
                        <Text style={[styles.badgeText, { color: severityStyle.color }]}>{report.severity}</Text>
                    </View>
                </View>
                <Text style={styles.formTypeText}>{report.formType}</Text>
            </View>

            {/* 3. Asset Info Card */}
            <View style={styles.card}>
                <View style={styles.gridRow}>
                    <Text style={styles.gridLabel}>Asset ID</Text>
                    <Text style={styles.gridValue}>{report.assetId}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.gridRow}>
                    <Text style={styles.gridLabel}>Serial No.</Text>
                    <Text style={styles.gridValue}>{report.serialNumber}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.gridRow}>
                    <Text style={styles.gridLabel}>Model</Text>
                    <Text style={styles.gridValue}>{report.model}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.gridRow}>
                    <Text style={styles.gridLabel}>Form No.</Text>
                    <Text style={styles.gridValue}>{report.formNumber}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.gridRow}>
                    <Text style={styles.gridLabel}>Submitted</Text>
                    <Text style={styles.gridValue}>
                        {new Date(report.submittedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </Text>
                </View>
                <View style={styles.divider} />
                <View style={[styles.gridRow, !report.customer && { marginBottom: 0 }]}>
                    <Text style={styles.gridLabel}>Submitted By</Text>
                    <Text style={styles.gridValue}>{report.submittedBy}</Text>
                </View>

                {report.customer && (
                    <>
                        <View style={styles.divider} />
                        <View style={[styles.gridRow, { marginBottom: 0 }]}>
                            <Text style={styles.gridLabel}>Customer</Text>
                            <Text style={styles.gridValue}>{report.customer}</Text>
                        </View>
                    </>
                )}
            </View>

            {/* 4. Count Pills Card */}
            <View style={[styles.card, { marginTop: 12 }]}>
                <Text style={styles.sectionLabelCard}>ITEM COUNTS</Text>
                <View style={styles.pillRow}>
                    <View style={[styles.pill, { backgroundColor: '#D32F2F' }]}><Text style={styles.pillText}>{criticalCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#F59E0B' }]}><Text style={styles.pillText}>{warningCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#4CAF50' }]}><Text style={styles.pillText}>{okCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#9CA3AF' }]}><Text style={styles.pillText}>{naCount}</Text></View>
                </View>
            </View>

            {/* 5. AI Summary Section */}
            <View style={styles.sectionHeaderContainer}>
                <Ionicons name="hardware-chip-outline" size={14} color="#FFCD11" style={{ marginRight: 6 }} />
                <Text style={styles.sectionLabel}>AI SUMMARY</Text>
            </View>
            <View style={[styles.card, { marginTop: 8 }]}>
                {report.summary ? (
                    <Text style={styles.aiSummaryText}>{report.summary}</Text>
                ) : (
                    <Text style={styles.placeholderMuted}>No AI summary available for this inspection. // PLACEHOLDER</Text>
                )}
            </View>

            {/* 6. Actionable Items Section */}
            <View style={styles.sectionHeaderContainer}>
                <Text style={styles.sectionLabel}>ACTIONABLE ITEMS</Text>
            </View>
            {report.actionableItems.length === 0 ? (
                <View style={{ paddingHorizontal: 20 }}>
                    <Text style={[styles.placeholderMuted, { marginTop: 8 }]}>No actionable items flagged. // PLACEHOLDER</Text>
                </View>
            ) : (
                <View style={[styles.card, { marginTop: 8, paddingVertical: 0 }]}>
                    {report.actionableItems.map((item, idx) => (
                        <View key={idx}>
                            <View style={styles.actionItemRow}>
                                <Ionicons name="warning-outline" size={20} color="#FFCD11" style={styles.actionIcon} />
                                <Text style={styles.actionText}>{item}</Text>
                            </View>
                            {idx < report.actionableItems.length - 1 && <View style={styles.actionDivider} />}
                        </View>
                    ))}
                </View>
            )}

            {/* 7. Inspection Items Breakdown */}
            <View style={styles.sectionHeaderContainer}>
                <Text style={styles.sectionLabel}>INSPECTION ITEMS</Text>
            </View>
            {report.items.length === 0 ? (
                <View style={{ paddingHorizontal: 20 }}>
                    <Text style={[styles.placeholderMuted, { marginTop: 8, marginBottom: 32 }]}>
                        Individual item breakdown not available. // PLACEHOLDER
                    </Text>
                </View>
            ) : (
                <View style={styles.itemsContainer}>
                    {report.items.map(item => (
                        <View key={item.id} style={styles.itemCard}>
                            <View style={styles.itemRowTop}>
                                <View style={[styles.smallDot, { backgroundColor: getStatusColor(item.status) }]} />
                                <Text style={styles.itemNameText}>{item.name}</Text>
                                <Text style={styles.itemCategoryText}>{item.category}</Text>
                            </View>

                            {item.aiPreliminaryStatus && (
                                <View style={styles.itemPillContainer}>
                                    <View style={[styles.smallPill, { backgroundColor: getStatusColor(item.aiPreliminaryStatus) }]}>
                                        <Text style={[styles.smallPillText, { color: item.aiPreliminaryStatus === 'CAUTION' ? '#000000' : '#FFFFFF' }]}>
                                            {item.aiPreliminaryStatus}
                                        </Text>
                                    </View>
                                </View>
                            )}

                            {item.globalSafetyOverridePresent && (
                                <Text style={styles.criticalItemText}>⚠ CRITICAL</Text>
                            )}
                        </View>
                    ))}
                </View>
            )}

        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    scrollContent: {
        paddingBottom: 80,
    },
    header: {
        paddingTop: 52,
        paddingHorizontal: 20,
        height: 108, // 52 + 56
        flexDirection: 'row',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#333333',
    },
    headerButton: {
        flexDirection: 'row',
        alignItems: 'center',
        minHeight: 56,
        marginLeft: -8, // Offset padding to align visually
    },
    headerBackText: {
        fontSize: 16,
        color: '#FFFFFF',
        marginLeft: 4,
    },
    headerTitleSpacer: {
        flex: 1,
    },
    headerButtonRight: {
        minHeight: 56,
        justifyContent: 'center',
        alignItems: 'flex-end',
        marginRight: -8,
    },
    statusBanner: {
        width: '100%',
        height: 52,
        justifyContent: 'center',
        alignItems: 'center',
    },
    statusBannerText: {
        fontSize: 18,
        fontWeight: '900',
        letterSpacing: 1,
    },
    titleBlock: {
        paddingHorizontal: 20,
        paddingTop: 24,
        paddingBottom: 8,
    },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        marginBottom: 8,
    },
    titleText: {
        fontSize: 22,
        fontWeight: '700',
        color: '#FFFFFF',
        flex: 1,
        marginRight: 12,
        lineHeight: 28,
    },
    formTypeText: {
        fontSize: 15,
        color: '#C0C0C0',
    },
    card: {
        backgroundColor: '#2A2A2A',
        borderRadius: 10,
        marginHorizontal: 20,
        padding: 20,
    },
    gridRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        minHeight: 44,
    },
    gridLabel: {
        color: '#C0C0C0',
        fontSize: 14,
        width: 110,
    },
    gridValue: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '600',
        flex: 1,
        textAlign: 'right',
    },
    divider: {
        height: 1,
        backgroundColor: '#333333',
        width: '100%',
    },
    sectionHeaderContainer: {
        paddingHorizontal: 20,
        marginTop: 24,
        flexDirection: 'row',
        alignItems: 'center',
    },
    sectionLabel: {
        fontSize: 13,
        fontWeight: '700',
        color: '#C0C0C0',
        letterSpacing: 1,
        textTransform: 'uppercase',
    },
    sectionLabelCard: {
        fontSize: 13,
        fontWeight: '700',
        color: '#C0C0C0',
        letterSpacing: 1,
        textTransform: 'uppercase',
        marginBottom: 8,
    },
    badgePill: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 999,
        marginTop: 2,
    },
    badgeText: {
        fontSize: 13,
        fontWeight: '700',
    },
    modeBanner: {
        backgroundColor: '#242424',
        paddingHorizontal: 16,
        paddingVertical: 8,
        marginHorizontal: 16,
        marginBottom: 4,
        borderRadius: 6,
    },
    modeBannerText: {
        fontSize: 12,
        color: '#FFCD11',
        fontWeight: '700',
        letterSpacing: 1,
    },
    pillRow: {
        flexDirection: 'row',
        gap: 6,
    },
    pill: {
        width: 48,
        height: 36,
        borderRadius: 6,
        justifyContent: 'center',
        alignItems: 'center',
    },
    pillText: {
        fontSize: 15,
        fontWeight: '800',
        color: '#FFFFFF',
    },
    aiSummaryText: {
        fontSize: 15,
        color: '#FFFFFF',
        lineHeight: 24,
    },
    placeholderMuted: {
        fontSize: 15,
        color: '#C0C0C0',
        lineHeight: 24,
    },
    actionItemRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        minHeight: 56,
        paddingVertical: 12,
    },
    actionIcon: {
        marginTop: 2,
        marginRight: 12,
    },
    actionText: {
        fontSize: 15,
        color: '#FFFFFF',
        flex: 1,
        lineHeight: 24,
    },
    actionDivider: {
        height: 1,
        backgroundColor: '#333333',
        marginLeft: 32,
    },
    itemsContainer: {
        paddingHorizontal: 20,
        marginBottom: 32,
    },
    itemCard: {
        backgroundColor: '#2A2A2A',
        borderRadius: 10,
        padding: 16,
        marginTop: 12,
        minHeight: 64,
        justifyContent: 'center',
    },
    itemRowTop: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    smallDot: {
        width: 14,
        height: 14,
        borderRadius: 7,
        marginRight: 12,
    },
    itemNameText: {
        fontWeight: '700',
        color: '#FFFFFF',
        flex: 1,
        fontSize: 15,
    },
    itemCategoryText: {
        color: '#C0C0C0',
        fontSize: 14,
    },
    itemPillContainer: {
        flexDirection: 'row',
        marginTop: 10,
        paddingLeft: 26, // Indent past dot
    },
    smallPill: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 999,
    },
    smallPillText: {
        fontSize: 12,
        fontWeight: '700',
    },
    criticalItemText: {
        color: '#D32F2F',
        fontSize: 13,
        fontWeight: 'bold',
        marginTop: 6,
        paddingLeft: 26,
    }
});
