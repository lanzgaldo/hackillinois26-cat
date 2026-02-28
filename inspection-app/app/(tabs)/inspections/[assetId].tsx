import React, { useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useInspection } from '../../../context/InspectionContext';
import { CATEGORIES } from '../../../constants/inspectionCategories';
import { colors } from '../../../constants/colors';

import StickyInspectionHeader from '../../../components/inspection/StickyInspectionHeader';
import AccordionSection from '../../../components/inspection/AccordionSection';
import FloatingActionTab from '../../../components/inspection/FloatingActionTab';
import BottomActionBar from '../../../components/inspection/BottomActionBar';

export default function ActiveInspectionScreen() {
    const { assetId } = useLocalSearchParams<{ assetId: string }>();
    const router = useRouter();
    const { state, resetInspection, submitInspection } = useInspection();

    useEffect(() => {
        if (assetId && state.assetId !== assetId) {
            resetInspection(assetId);
        }
    }, [assetId]);

    const handleSubmit = () => {
        submitInspection();
        router.replace('/inspections/review');
    };

    return (
        <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            <View style={styles.container}>
                <StickyInspectionHeader />

                <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
                    {CATEGORIES.map(category => (
                        <AccordionSection key={category.id} category={category} />
                    ))}
                </ScrollView>

                <FloatingActionTab />
                <BottomActionBar onSubmit={handleSubmit} onDraft={() => router.back()} />
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: colors.background,
    },
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollContent: {
        paddingBottom: 220, // Enough Space for the floating tab and bottom bar
    }
});
