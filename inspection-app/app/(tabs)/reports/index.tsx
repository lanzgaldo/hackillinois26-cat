import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CompletedInspection } from '../../../types/inspection';
import { colors } from '../../../constants/colors';
import { typography } from '../../../constants/typography';
import InspectionReceiptCard from '../../../components/reports/InspectionReceiptCard';

export default function ReportsScreen() {
    const [reports, setReports] = useState<CompletedInspection[]>([]);

    useFocusEffect(
        React.useCallback(() => {
            let isActive = true;

            const loadReports = async () => {
                try {
                    const raw = await AsyncStorage.getItem('cat_track_completed_inspections');
                    if (isActive && raw) {
                        setReports(JSON.parse(raw));
                    }
                } catch (e) {
                    console.error('Failed to load inspection history', e);
                }
            };

            loadReports();

            return () => {
                isActive = false;
            };
        }, [])
    );

    const renderEmptyState = () => (
        <View style={styles.emptyContainer}>
            <MaterialCommunityIcons name="clipboard-off-outline" size={48} color="#2A2A2A" />
            <Text style={styles.emptyText}>NO INSPECTIONS YET</Text>
            <Text style={styles.emptySubtext}>Completed inspections will appear here.</Text>
        </View>
    );

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>INSPECTION REPORTS</Text>
                <Text style={styles.headerSubtitle}>{reports.length} COMPLETED</Text>
            </View>

            <FlatList
                data={reports}
                keyExtractor={(item) => item.inspectionId}
                renderItem={({ item }) => <InspectionReceiptCard inspection={item} />}
                contentContainerStyle={styles.listContent}
                ListEmptyComponent={renderEmptyState}
                showsVerticalScrollIndicator={false}
            />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#080808',
    },
    header: {
        paddingHorizontal: 20,
        paddingVertical: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
    },
    headerTitle: {
        fontFamily: typography.families.display,
        fontSize: 26,
        color: '#F2F0EB',
        textTransform: 'uppercase',
    },
    headerSubtitle: {
        fontFamily: typography.families.mono,
        fontSize: 12,
        color: colors.primary,
        marginTop: 4,
    },
    listContent: {
        paddingHorizontal: 16,
        paddingTop: 16,
        paddingBottom: 32 + 64, // accounting for tab bar
        flexGrow: 1,
    },
    emptyContainer: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
    },
    emptyText: {
        fontFamily: typography.families.ui,
        fontSize: 16,
        color: '#444444',
        textTransform: 'uppercase',
        marginTop: 8,
    },
    emptySubtext: {
        fontFamily: typography.families.body,
        fontSize: 14,
        color: '#333333',
    }
});
