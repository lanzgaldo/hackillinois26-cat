import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, FlatList, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { CompletedInspection } from '../../../types/inspection';

// PLACEHOLDER
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
        items: [],
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

export default function ReportsListScreen() {
    const [searchQuery, setSearchQuery] = useState('');
    const router = useRouter();

    // FRONTEND FILTER: filters in-memory from local placeholder data.
    // Filters across title, assetId, model, serialNumber, and customer fields.
    // Sufficient for expected offline list sizes (<200 records).
    // TODO: If paginated server results are introduced, migrate to debounced query param.
    const filteredReports = PLACEHOLDER_REPORTS.filter(r => {
        const q = searchQuery.toLowerCase();
        return (
            r.title.toLowerCase().includes(q) ||
            r.assetId.toLowerCase().includes(q) ||
            r.model.toLowerCase().includes(q) ||
            r.serialNumber.toLowerCase().includes(q) ||
            (r.customer ?? '').toLowerCase().includes(q)
        );
    });

    const renderItem = ({ item }: { item: CompletedInspection }) => {
        // PLACEHOLDER: until real items are wired, use hardcoded placeholder counts
        // TODO: replace with real computed values from report.items
        let criticalCount = 0;
        let warningCount = 0;
        let okCount = 0;
        let naCount = 0;

        if (item.id === '1') { criticalCount = 1; warningCount = 2; okCount = 3; naCount = 0; }
        else if (item.id === '2') { criticalCount = 0; warningCount = 0; okCount = 6; naCount = 0; }
        else if (item.id === '3') { criticalCount = 2; warningCount = 1; okCount = 4; naCount = 1; }
        else if (item.id === '4') { criticalCount = 0; warningCount = 3; okCount = 2; naCount = 0; }
        else if (item.id === '5') { criticalCount = 1; warningCount = 0; okCount = 5; naCount = 0; }

        return (
            <View style={styles.card}>
                <Text style={styles.cardTitle}>{item.title || item.formType}</Text>

                {/* COUNT PILLS */}
                <View style={styles.pillRow}>
                    <View style={[styles.pill, { backgroundColor: '#D32F2F' }]}><Text style={styles.pillText}>{criticalCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#F59E0B' }]}><Text style={styles.pillText}>{warningCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#4CAF50' }]}><Text style={styles.pillText}>{okCount}</Text></View>
                    <View style={[styles.pill, { backgroundColor: '#9CA3AF' }]}><Text style={styles.pillText}>{naCount}</Text></View>
                </View>

                {/* METADATA BLOCK */}
                <Text style={styles.metadataText}>{item.formNumber}</Text>
                <Text style={styles.metadataText}>Asset ID: {item.assetId}</Text>
                <Text style={styles.metadataText}>Model: {item.model}</Text>
                {item.customer ? <Text style={styles.metadataText}>Customer: {item.customer}</Text> : null}
                <Text style={styles.metadataText}>{new Date(item.submittedAt).toLocaleString()}</Text>

                <View style={{ height: 12 }} />

                {/* SUB-REPORT ROWS */}
                <TouchableOpacity style={styles.subReportRow} onPress={() => router.push({ pathname: '/(tabs)/reports/[id]', params: { id: item.id, mode: 'form' } })} activeOpacity={0.65}>
                    <Ionicons name="document-text-outline" size={22} color="#555555" />
                    <Text style={styles.subReportText}>Form Order</Text>
                    <Ionicons name="chevron-forward" size={20} color="#CCCCCC" />
                </TouchableOpacity>
                <View style={styles.divider} />

                <TouchableOpacity style={styles.subReportRow} onPress={() => router.push({ pathname: '/(tabs)/reports/[id]', params: { id: item.id, mode: 'severity' } })} activeOpacity={0.65}>
                    <Ionicons name="document-text-outline" size={22} color="#555555" />
                    <Text style={styles.subReportText}>Severity Order</Text>
                    <Ionicons name="chevron-forward" size={20} color="#CCCCCC" />
                </TouchableOpacity>
                <View style={styles.divider} />

                <TouchableOpacity style={styles.subReportRow} onPress={() => router.push({ pathname: '/(tabs)/reports/[id]', params: { id: item.id, mode: 'summary' } })} activeOpacity={0.65}>
                    <Ionicons name="document-text-outline" size={22} color="#555555" />
                    <Text style={styles.subReportText}>Summary Report</Text>
                    <Ionicons name="chevron-forward" size={20} color="#CCCCCC" />
                </TouchableOpacity>
                <View style={styles.divider} />

                <TouchableOpacity style={styles.subReportRow} onPress={() => router.push({ pathname: '/(tabs)/reports/[id]', params: { id: item.id, mode: 'actionable' } })} activeOpacity={0.65}>
                    <Ionicons name="alert-circle-outline" size={22} color="#D32F2F" />
                    <Text style={styles.subReportText}>Actionable Items</Text>
                    <Ionicons name="chevron-forward" size={20} color="#CCCCCC" />
                </TouchableOpacity>

                {/* EMAIL BUTTON */}
                <TouchableOpacity style={styles.emailButton} onPress={() => {/* TODO */ }} activeOpacity={0.65} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                    <Ionicons name="mail" size={20} color="#FFFFFF" />
                </TouchableOpacity>
            </View>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Reports</Text>
                <TouchableOpacity onPress={() => {/* TODO: bulk forward reports via email */ }} style={styles.iconButtonHeader} activeOpacity={0.6} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                    <Ionicons name="mail-outline" size={24} color="#C0C0C0" />
                </TouchableOpacity>
            </View>

            <View style={styles.searchContainer}>
                <Ionicons name="search" size={18} color="#9CA3AF" />
                <TextInput
                    style={styles.searchInput}
                    placeholder="Search"
                    placeholderTextColor="#9CA3AF"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                />
                {searchQuery.length > 0 && (
                    <TouchableOpacity onPress={() => setSearchQuery('')} activeOpacity={0.65} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                        <Ionicons name="close-circle" size={18} color="#9CA3AF" />
                    </TouchableOpacity>
                )}
            </View>

            <FlatList
                data={filteredReports}
                keyExtractor={(item) => item.id}
                renderItem={renderItem}
                contentContainerStyle={styles.listContent}
                ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
                ListEmptyComponent={() => (
                    <View style={styles.emptyContainer}>
                        <Ionicons name="receipt-outline" size={64} color="#9CA3AF" />
                        <Text style={styles.emptyHeading}>No Reports Found</Text>
                        <Text style={styles.emptySubtext}>
                            {searchQuery === '' ? 'Submitted inspections will appear here.' : 'No reports match your search.'}
                        </Text>
                    </View>
                )}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingTop: 52,
        paddingBottom: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#333333',
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    iconButtonHeader: {
        minWidth: 48,
        minHeight: 48,
        justifyContent: 'center',
        alignItems: 'flex-end',
    },
    searchContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#F2F2F2',
        borderRadius: 12,
        marginHorizontal: 16,
        marginVertical: 12,
        paddingHorizontal: 16,
        height: 48,
    },
    searchInput: {
        flex: 1,
        marginLeft: 8,
        color: '#111111',
        fontSize: 16,
        height: '100%',
    },
    listContent: {
        paddingHorizontal: 0,
        paddingBottom: 100,
        flexGrow: 1,
    },
    card: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        marginHorizontal: 16,
        marginBottom: 12,
        padding: 16,
        shadowColor: '#000',
        shadowOpacity: 0.08,
        shadowRadius: 6,
        shadowOffset: { width: 0, height: 2 },
        elevation: 3,
    },
    cardTitle: {
        fontSize: 17,
        fontWeight: '700',
        color: '#111111',
        marginBottom: 8,
    },
    pillRow: {
        flexDirection: 'row',
        gap: 6,
        marginBottom: 10,
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
    metadataText: {
        fontSize: 14,
        color: '#444444',
        lineHeight: 22,
        marginBottom: 12,
    },
    subReportRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 14,
        minHeight: 52,
    },
    subReportText: {
        fontSize: 16,
        color: '#111111',
        flex: 1,
        marginLeft: 12,
    },
    divider: {
        height: 1,
        backgroundColor: '#F0F0F0',
    },
    emailButton: {
        alignSelf: 'flex-end',
        marginTop: 12,
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#222222',
        justifyContent: 'center',
        alignItems: 'center',
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        gap: 12,
        paddingHorizontal: 32,
        marginTop: 64,
    },
    emptyHeading: {
        fontSize: 18,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    emptySubtext: {
        fontSize: 15,
        color: '#C0C0C0',
        textAlign: 'center',
        lineHeight: 24, // 1.6x of 15
    }
});
