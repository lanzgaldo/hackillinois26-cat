import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator, Alert } from 'react-native';
import { LegacyCompletedInspection } from '../../types/inspection';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { generateActionableItemsPDF, generateFormOrderPDF, generateSeverityOrderPDF, generateSummaryReportPDF } from '../../services/pdfReportService';

export default function InspectionReceiptCard({ inspection }: { inspection: LegacyCompletedInspection }) {

    const [generating, setGenerating] = useState<string | null>(null);

    let redCount = 0;
    let yellowCount = 0;
    let greenCount = 0;
    let skippedCount = 0;

    inspection.items.forEach(item => {
        if (item.status === 'red') redCount++;
        else if (item.status === 'yellow') yellowCount++;
        else if (item.status === 'green') greenCount++;
        else skippedCount++;
    });

    const hasActionableItems = redCount > 0 || yellowCount > 0;

    const formattedDate = new Date(inspection.submittedAt).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
    }).toUpperCase();

    const formattedTime = new Date(inspection.submittedAt).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit'
    });

    const inspectionShortId = inspection.inspectionId.slice(-6).toUpperCase();

    const handleGeneratePDF = async (type: 'form' | 'severity' | 'summary' | 'actionable') => {
        setGenerating(type);
        try {
            switch (type) {
                case 'form': await generateFormOrderPDF(inspection); break;
                case 'severity': await generateSeverityOrderPDF(inspection); break;
                case 'summary': await generateSummaryReportPDF(inspection); break;
                case 'actionable': await generateActionableItemsPDF(inspection); break;
            }
        } catch (error) {
            Alert.alert('Report generation failed. Please try again.');
        } finally {
            setGenerating(null);
        }
    }

    return (
        <View style={styles.card}>
            {/* SECTION A: CARD HEADER */}
            <View style={styles.headerRow}>
                <View style={styles.headerLeft}>
                    <Text style={styles.title}>DAILY INSPECTION</Text>
                    <Text style={styles.subtitle}>{formattedDate}  ·  {formattedTime}</Text>
                </View>
                <View style={styles.badge}>
                    <Text style={styles.badgeText}>#{inspectionShortId}</Text>
                </View>
            </View>

            {/* SECTION B: STATUS BLOCKS ROW */}
            <View style={styles.statusBlocksContainer}>
                <View style={styles.statusBlock}>
                    <Text style={[styles.statusNumber, { color: colors.statusRed }]}>{redCount}</Text>
                    <Text style={[styles.statusLabel, { color: 'rgba(229, 57, 53, 0.6)' }]}>RED</Text>
                </View>
                <View style={[styles.statusBlock, styles.borderLeft]}>
                    <Text style={[styles.statusNumber, { color: colors.statusYellow }]}>{yellowCount}</Text>
                    <Text style={[styles.statusLabel, { color: 'rgba(255, 205, 17, 0.6)' }]}>YELLOW</Text>
                </View>
                <View style={[styles.statusBlock, styles.borderLeft]}>
                    <Text style={[styles.statusNumber, { color: colors.statusGreen }]}>{greenCount}</Text>
                    <Text style={[styles.statusLabel, { color: 'rgba(67, 160, 71, 0.6)' }]}>GREEN</Text>
                </View>
                <View style={[styles.statusBlock, styles.borderLeft]}>
                    <Text style={[styles.statusNumber, { color: '#444444' }]}>{skippedCount}</Text>
                    <Text style={[styles.statusLabel, { color: 'rgba(68, 68, 68, 0.6)' }]}>SKIPPED</Text>
                </View>
            </View>

            {/* SECTION C: ASSET INFO */}
            <View style={styles.assetInfoContainer}>
                <View style={styles.assetRow}>
                    <View style={styles.assetColumn}>
                        <Text style={styles.assetLabel}>SERIAL</Text>
                        <Text style={styles.assetMonoValue}>{inspection.serialNumber}</Text>
                    </View>
                    <View style={styles.assetColumn}>
                        <Text style={styles.assetLabel}>ASSET ID</Text>
                        <Text style={styles.assetMonoValue}>{inspection.assetId}</Text>
                    </View>
                </View>
                <View style={[styles.assetRow, { marginTop: 12 }]}>
                    <View style={styles.assetColumn}>
                        <Text style={styles.assetLabel}>MODEL</Text>
                        <Text style={styles.assetModelValue}>{inspection.model}</Text>
                    </View>
                    <View style={styles.assetColumn}>
                        <Text style={styles.assetLabel}>CUSTOMER</Text>
                        <Text style={inspection.customerName ? styles.assetCustomerValue : styles.assetEmptyCustomer}>
                            {inspection.customerName || '—'}
                        </Text>
                    </View>
                </View>
            </View>

            {/* SECTION D: REPORT FORMAT TABS */}
            <View style={styles.tabsSection}>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsScrollContent}>

                    <Pressable
                        style={[styles.tabButton, generating === 'form' && { backgroundColor: colors.primary }]}
                        onPress={() => handleGeneratePDF('form')}
                        disabled={generating !== null}
                    >
                        {generating === 'form' ? <ActivityIndicator size="small" color="#080808" /> : (
                            <Text style={[styles.tabText, generating === 'form' && { color: '#080808' }]}>FORM ORDER</Text>
                        )}
                    </Pressable>

                    <Pressable
                        style={[styles.tabButton, generating === 'severity' && { backgroundColor: colors.primary }]}
                        onPress={() => handleGeneratePDF('severity')}
                        disabled={generating !== null}
                    >
                        {generating === 'severity' ? <ActivityIndicator size="small" color="#080808" /> : (
                            <Text style={[styles.tabText, generating === 'severity' && { color: '#080808' }]}>SEVERITY ORDER</Text>
                        )}
                    </Pressable>

                    <Pressable
                        style={[styles.tabButton, generating === 'summary' && { backgroundColor: colors.primary }]}
                        onPress={() => handleGeneratePDF('summary')}
                        disabled={generating !== null}
                    >
                        {generating === 'summary' ? <ActivityIndicator size="small" color="#080808" /> : (
                            <Text style={[styles.tabText, generating === 'summary' && { color: '#080808' }]}>SUMMARY REPORT</Text>
                        )}
                    </Pressable>

                    {hasActionableItems && (
                        <Pressable
                            style={[
                                styles.tabButton,
                                generating === 'actionable' && { backgroundColor: colors.statusRed }
                            ]}
                            onPress={() => handleGeneratePDF('actionable')}
                            disabled={generating !== null}
                        >
                            {generating === 'actionable' ? <ActivityIndicator size="small" color="#F2F0EB" /> : (
                                <Text style={[
                                    styles.tabText,
                                    generating === 'actionable' && { color: '#F2F0EB' }
                                ]}>ACTIONABLE ITEMS</Text>
                            )}
                        </Pressable>
                    )}
                </ScrollView>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: '#141414',
        borderWidth: 1,
        borderColor: '#2A2A2A',
        borderRadius: 14,
        overflow: 'hidden',
        marginBottom: 16,
    },
    headerRow: {
        flexDirection: 'row',
        backgroundColor: '#1A1A1A',
        paddingHorizontal: 16,
        paddingVertical: 14,
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
        alignItems: 'center',
    },
    headerLeft: {
        flex: 1,
    },
    title: {
        fontFamily: typography.families.display,
        fontSize: 18,
        color: '#F2F0EB',
        textTransform: 'uppercase',
    },
    subtitle: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#888888',
        marginTop: 2,
    },
    badge: {
        backgroundColor: 'rgba(255, 205, 17, 0.1)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: 'rgba(255, 205, 17, 0.3)',
    },
    badgeText: {
        fontFamily: typography.families.mono,
        fontSize: 11,
        color: colors.primary,
    },
    statusBlocksContainer: {
        flexDirection: 'row',
        paddingHorizontal: 14,
        paddingVertical: 12,
    },
    statusBlock: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
    borderLeft: {
        borderLeftWidth: 1,
        borderLeftColor: '#2A2A2A',
    },
    statusNumber: {
        fontFamily: typography.families.display,
        fontSize: 28,
        lineHeight: 34,
    },
    statusLabel: {
        fontFamily: typography.families.ui,
        fontSize: 10,
        textTransform: 'uppercase',
        letterSpacing: 0.8,
        marginTop: 2,
    },
    assetInfoContainer: {
        paddingHorizontal: 14,
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
        borderTopWidth: 1,
        borderTopColor: '#2A2A2A',
    },
    assetRow: {
        flexDirection: 'row',
    },
    assetColumn: {
        flex: 1,
    },
    assetLabel: {
        fontFamily: typography.families.ui,
        fontSize: 10,
        color: '#888888',
        marginBottom: 4,
    },
    assetMonoValue: {
        fontFamily: typography.families.mono,
        fontSize: 13,
        color: '#F2F0EB',
    },
    assetModelValue: {
        fontFamily: typography.families.bodyMedium, // 600 weight not available from fonts, using Medium ~500
        fontSize: 13,
        color: '#F2F0EB',
    },
    assetCustomerValue: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#F2F0EB',
    },
    assetEmptyCustomer: {
        fontFamily: typography.families.body,
        fontSize: 13,
        color: '#444444',
    },
    tabsSection: {
        backgroundColor: '#0F0F0F',
        paddingVertical: 10,
    },
    tabsScrollContent: {
        paddingHorizontal: 12,
        gap: 8,
    },
    tabButton: {
        height: 36,
        paddingHorizontal: 14,
        backgroundColor: '#1E1E1E',
        borderRadius: 6,
        justifyContent: 'center',
        alignItems: 'center',
        minWidth: 100,
    },
    tabText: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        color: '#888888',
        textTransform: 'uppercase',
        letterSpacing: 0.9,
    }
});
