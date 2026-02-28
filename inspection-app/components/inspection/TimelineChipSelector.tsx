import React from 'react';
import { ScrollView, View, Text, Pressable, StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface Props {
    selected: string | undefined;
    onSelect: (val: string) => void;
}

const OPTIONS = ['24 hrs', '1 week', '30 days', 'Next PM'];

export default function TimelineChipSelector({ selected, onSelect }: Props) {
    return (
        <View style={styles.container}>
            <Text style={styles.headerText}>ESTIMATED TIME TO FAILURE</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
                {OPTIONS.map(opt => {
                    const isActive = selected === opt;
                    return (
                        <Pressable
                            key={opt}
                            onPress={() => onSelect(opt)}
                            style={[
                                styles.chip,
                                { backgroundColor: isActive ? colors.primary : colors.border }
                            ]}
                            accessibilityRole="button"
                        >
                            <Text style={[styles.chipText, { color: isActive ? '#000000' : colors.textSecondary }]}>
                                {opt}
                            </Text>
                        </Pressable>
                    );
                })}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        marginTop: 16,
        width: '100%',
    },
    headerText: {
        fontFamily: typography.families.ui,
        fontSize: typography.sizes.minimumLabel,
        color: colors.textSecondary,
        marginBottom: 8,
    },
    scrollContent: {
        gap: 12,
    },
    chip: {
        height: 48,
        minWidth: 80,
        paddingHorizontal: 16,
        borderRadius: 24,
        alignItems: 'center',
        justifyContent: 'center',
    },
    chipText: {
        fontFamily: typography.families.ui,
        fontSize: 15,
    }
});
