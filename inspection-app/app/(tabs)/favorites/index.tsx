import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

// PLACEHOLDER
interface FavoriteInspection {
    id: string;
    name: string;
    formNumber: string;
    status: 'Active' | 'Draft' | 'Submitted';
    category: string; // e.g. "Daily", "PM", "Annual"
}

const PLACEHOLDER_FAVORITES: FavoriteInspection[] = [
    {
        id: '1',
        name: 'Daily Inspection',
        formNumber: '124611',
        status: 'Active',
        category: 'Daily',
    },
    {
        id: '2',
        name: 'D6 Dozer Pre-Op',
        formNumber: 'PM-2025-00847',
        status: 'Draft',
        category: 'Preventive Maintenance',
    },
];

// PLACEHOLDER
interface HistoryInspection {
    id: string;
    name: string;
    category: string;
    status: 'green' | 'yellow' | 'red';
    submittedAt: string; // ISO date string
    formNumber: string;
}

const PLACEHOLDER_HISTORY: HistoryInspection[] = [
    {
        id: 'h1',
        name: 'D6 Dozer Pre-Op',
        category: 'Preventive Maintenance',
        status: 'red',
        submittedAt: '2025-03-14T08:32:00Z',
        formNumber: 'PM-2025-00847',
    },
    {
        id: 'h2',
        name: '966 Wheel Loader PM',
        category: 'Preventive Maintenance',
        status: 'yellow',
        submittedAt: '2025-02-28T14:10:00Z',
        formNumber: 'PM-2025-00731',
    },
    {
        id: 'h3',
        name: 'Cat 320 Excavator Annual',
        category: 'Technical Analysis',
        status: 'green',
        submittedAt: '2025-01-15T09:45:00Z',
        formNumber: 'TA-2025-00412',
    },
    {
        id: 'h4',
        name: 'D8 Dozer Daily Walkaround',
        category: 'Daily Safety',
        status: 'yellow',
        submittedAt: '2025-03-01T06:20:00Z',
        formNumber: 'DW-2025-01003',
    },
    {
        id: 'h5',
        name: 'CB13 Compactor Pre-Season',
        category: 'Preventive Maintenance',
        status: 'green',
        submittedAt: '2025-02-05T11:00:00Z',
        formNumber: 'PM-2025-00290',
    },
];

function FavoritesList() {
    const router = useRouter();

    if (PLACEHOLDER_FAVORITES.length === 0) {
        return (
            <View style={styles.emptyState}>
                <Ionicons name="star-outline" size={56} color="#4B5563" />
                <Text style={styles.emptyHeading}>No Favorites Yet</Text>
                <Text style={styles.emptySubtext}>
                    Star an inspection to save it here for quick access.
                </Text>
            </View>
        );
    }

    return (
        <FlatList
            data={PLACEHOLDER_FAVORITES}
            keyExtractor={item => item.id}
            contentContainerStyle={{
                paddingHorizontal: 16,
                paddingBottom: 80,
                flexGrow: 1,
            }}
            ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
            renderItem={({ item }) => (
                <TouchableOpacity
                    style={styles.favoriteCard}
                    activeOpacity={0.7}
                    onPress={() => {/* TODO: router.push to inspection detail */ }}
                >
                    {/* Star button */}
                    <TouchableOpacity
                        style={styles.starBtn}
                        hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                        onPress={() => {/* TODO: remove from favorites */ }}
                        activeOpacity={0.6}
                    >
                        <Ionicons name="star" size={24} color="#FFCD11" />
                    </TouchableOpacity>

                    {/* Content */}
                    <View style={styles.favoriteContent}>
                        <Text style={styles.favoriteName}>{item.name}</Text>
                        <Text style={styles.favoriteMetaRow}>
                            {item.category}{'  ·  '}Form Number: {item.formNumber}
                        </Text>
                    </View>

                    {/* Status pill + chevron */}
                    <View style={styles.favoriteRight}>
                        <View style={[
                            styles.statusPill,
                            item.status === 'Active' && { backgroundColor: '#4CAF50' },
                            item.status === 'Draft' && { backgroundColor: '#F59E0B' },
                            item.status === 'Submitted' && { backgroundColor: '#374151' },
                        ]}>
                            <Text style={styles.statusPillText}>{item.status}</Text>
                        </View>
                        <Ionicons
                            name="chevron-forward"
                            size={18}
                            color="#9CA3AF"
                            style={{ marginLeft: 8 }}
                        />
                    </View>
                </TouchableOpacity>
            )}
        />
    );
}

function HistoryList() {
    const router = useRouter();

    if (PLACEHOLDER_HISTORY.length === 0) {
        return (
            <View style={styles.emptyState}>
                <Ionicons name="time-outline" size={56} color="#4B5563" />
                <Text style={styles.emptyHeading}>No History Yet</Text>
                <Text style={styles.emptySubtext}>
                    Completed inspections will appear here.
                </Text>
            </View>
        );
    }

    return (
        <FlatList
            data={PLACEHOLDER_HISTORY}
            keyExtractor={item => item.id}
            contentContainerStyle={{
                paddingHorizontal: 16,
                paddingBottom: 80,
                flexGrow: 1,
            }}
            ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
            renderItem={({ item }) => (
                <TouchableOpacity
                    style={styles.historyCard}
                    activeOpacity={0.7}
                    onPress={() => {/* TODO: router.push to report detail */ }}
                >
                    {/* Status dot */}
                    <View style={[
                        styles.statusDot,
                        item.status === 'green' && { backgroundColor: '#4CAF50' },
                        item.status === 'yellow' && { backgroundColor: '#F59E0B' },
                        item.status === 'red' && { backgroundColor: '#D32F2F' },
                    ]} />

                    {/* Content */}
                    <View style={styles.historyContent}>
                        <Text style={styles.historyName}>{item.name}</Text>
                        <Text style={styles.historyMeta}>{item.category}</Text>
                        <Text style={styles.historyMeta}>Form: {item.formNumber}</Text>
                    </View>

                    {/* Date + chevron */}
                    <View style={styles.historyRight}>
                        <Text style={styles.historyDate}>
                            {new Date(item.submittedAt).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                            })}
                        </Text>
                        <Ionicons
                            name="chevron-forward"
                            size={18}
                            color="#9CA3AF"
                            style={{ marginTop: 4 }}
                        />
                    </View>
                </TouchableOpacity>
            )}
        />
    );
}

export default function FavoritesScreen() {
    const [activeTab, setActiveTab] = useState<'favorites' | 'history'>('favorites');

    const openDrawer = () => {
        // TODO: wire to drawer context
    };

    return (
        <View style={styles.screen}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity
                    onPress={openDrawer}
                    hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                    style={styles.headerIconBtn}
                >
                    <Ionicons name="menu" size={26} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Favorites</Text>
                <View style={styles.headerIconBtn} /> {/* spacer to center title */}
            </View>

            {/* Segmented control */}
            <View style={styles.segmentRow}>
                {(['favorites', 'history'] as const).map(tab => (
                    <TouchableOpacity
                        key={tab}
                        style={[
                            styles.segmentBtn,
                            activeTab === tab && styles.segmentBtnActive,
                        ]}
                        onPress={() => setActiveTab(tab)}
                        activeOpacity={0.7}
                    >
                        <Text style={[
                            styles.segmentLabel,
                            activeTab === tab && styles.segmentLabelActive,
                        ]}>
                            {tab === 'favorites' ? 'Favorites' : 'History'}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Conditional FlatList based on activeTab */}
            {activeTab === 'favorites' ? <FavoritesList /> : <HistoryList />}
        </View>
    );
}

const styles = StyleSheet.create({
    screen: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 52,
        paddingBottom: 14,
        backgroundColor: '#1A1A1A',
        borderBottomWidth: 1,
        borderBottomColor: '#333333',
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    headerIconBtn: {
        width: 44,
        height: 44,
        justifyContent: 'center',
        alignItems: 'center',
    },
    segmentRow: {
        flexDirection: 'row',
        marginHorizontal: 16,
        marginTop: 14,
        marginBottom: 10,
        backgroundColor: '#242424',
        borderRadius: 8,
        padding: 4,
    },
    segmentBtn: {
        flex: 1,
        height: 40,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 6,
    },
    segmentBtnActive: {
        backgroundColor: '#333333',
        borderBottomWidth: 2,
        borderBottomColor: '#FFCD11',
    },
    segmentLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#9CA3AF',
    },
    segmentLabelActive: {
        color: '#FFFFFF',
    },
    favoriteCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#242424',
        borderRadius: 8,
        paddingVertical: 14,
        paddingHorizontal: 16,
        minHeight: 64,
    },
    starBtn: {
        width: 36,
        height: 36,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    favoriteContent: {
        flex: 1,
    },
    favoriteName: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFFFFF',
        marginBottom: 3,
    },
    favoriteMetaRow: {
        fontSize: 13,
        color: '#9CA3AF',
        lineHeight: 18,
    },
    favoriteRight: {
        flexDirection: 'row',
        alignItems: 'center',
        marginLeft: 12,
    },
    statusPill: {
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 999,
    },
    statusPillText: {
        fontSize: 11,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    historyCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#242424',
        borderRadius: 8,
        paddingVertical: 14,
        paddingHorizontal: 16,
        minHeight: 64,
    },
    statusDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 14,
        marginTop: 2,
        flexShrink: 0,
    },
    historyContent: {
        flex: 1,
    },
    historyName: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFFFFF',
        marginBottom: 3,
    },
    historyMeta: {
        fontSize: 13,
        color: '#9CA3AF',
        lineHeight: 18,
    },
    historyRight: {
        alignItems: 'flex-end',
        marginLeft: 12,
    },
    historyDate: {
        fontSize: 12,
        color: '#9CA3AF',
        textAlign: 'right',
    },
    emptyState: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        gap: 12,
        paddingHorizontal: 40,
        paddingBottom: 80, // clears tab bar
    },
    emptyHeading: {
        fontSize: 17,
        fontWeight: '700',
        color: '#FFFFFF',
        textAlign: 'center',
    },
    emptySubtext: {
        fontSize: 14,
        color: '#9CA3AF',
        textAlign: 'center',
        lineHeight: 21,
    },
});
