import React, { useState } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { InspectionCategory } from '../../constants/inspectionCategories';
import { useInspection } from '../../context/InspectionContext';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import ChecklistItemCard from './ChecklistItemCard';

interface Props {
    category: InspectionCategory;
}

export default function AccordionSection({ category }: Props) {
    const { state } = useInspection();
    const [expanded, setExpanded] = useState(false);

    const totalItems = category.items.length;
    let completedCount = 0;
    let hasRed = false;
    let hasYellow = false;

    category.items.forEach(item => {
        const itemState = state.itemStates[item.id];
        if (itemState?.status) {
            completedCount++;
            if (itemState.status === 'red') hasRed = true;
            if (itemState.status === 'yellow') hasYellow = true;
        }
    });

    const isComplete = completedCount === totalItems;

    let statusDotColor = colors.textSecondary;
    if (hasRed) statusDotColor = colors.statusRed;
    else if (hasYellow) statusDotColor = colors.statusYellow;
    else if (isComplete && completedCount > 0) statusDotColor = colors.statusGreen;

    return (
        <View style={styles.container}>
            <Pressable
                style={styles.headerRow}
                onPress={() => setExpanded(!expanded)}
                accessibilityRole="button"
                accessibilityState={{ expanded }}
            >
                <View style={styles.headerLeft}>
                    <MaterialCommunityIcons name={category.icon as any} size={28} color={colors.textPrimary} />
                    <Text style={styles.titleText}>{category.name}</Text>
                    {completedCount > 0 && (
                        <View style={[styles.statusDot, { backgroundColor: statusDotColor }]} />
                    )}
                </View>

                <View style={styles.headerRight}>
                    <View style={styles.badge}>
                        <Text style={styles.badgeText}>{completedCount} OF {totalItems}</Text>
                    </View>
                    <Ionicons
                        name={expanded ? "chevron-up" : "chevron-down"}
                        size={24}
                        color={colors.textSecondary}
                    />
                </View>
            </Pressable>

            {expanded && (
                <View style={styles.content}>
                    {category.items.map(item => (
                        <ChecklistItemCard key={item.id} item={item} />
                    ))}
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: colors.background,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    headerRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        minHeight: 72,
        paddingHorizontal: 20,
        backgroundColor: colors.surfaceCard,
    },
    headerLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    titleText: {
        fontFamily: typography.families.ui,
        fontSize: 18,
        color: colors.textPrimary,
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginLeft: 4,
    },
    headerRight: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    badge: {
        backgroundColor: colors.elevatedSurface,
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
    },
    badgeText: {
        fontFamily: typography.families.mono,
        fontSize: 12,
        color: colors.textSecondary,
    },
    content: {
        padding: 20,
        backgroundColor: '#0a0a0a',
    }
});
