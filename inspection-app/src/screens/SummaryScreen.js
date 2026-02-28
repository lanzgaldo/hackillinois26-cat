import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { theme } from '../theme';

export default function SummaryScreen() {
    const navigation = useNavigation();
    const route = useRoute();

    // Default to green if missing
    const status = route.params?.status || 'green';
    const recordedNotes = route.params?.recordedNotes || false;

    let backgroundColor = theme.colors.success;
    let statusText = 'READY TO OPERATE';
    let subText = 'All inspection items passed successfully.';

    if (status === 'yellow') {
        backgroundColor = theme.colors.warning;
        statusText = 'CAUTION ADVISED';
        subText = 'Some warnings were noted. Review items before operation.';
    } else if (status === 'red') {
        backgroundColor = theme.colors.danger;
        statusText = 'DO NOT OPERATE';
        subText = 'Critical failures found. Maintenance required immediately.';
    }

    return (
        <View style={[styles.container, { backgroundColor }]}>
            <View style={styles.card}>
                <Text style={[styles.statusHeader, { color: backgroundColor }]}>
                    {statusText}
                </Text>
                <Text style={styles.subText}>{subText}</Text>

                {recordedNotes && (
                    <View style={styles.audioNoteContainer}>
                        <Text style={styles.audioText}>🎤 Voice notes attached</Text>
                    </View>
                )}
            </View>

            <TouchableOpacity
                style={styles.doneButton}
                onPress={() => navigation.navigate('Checklist')}
            >
                <Text style={styles.doneButtonText}>Start New Inspection</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        padding: theme.spacing.l,
    },
    card: {
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.xl,
        borderRadius: theme.borderRadius.xl,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 5,
        elevation: 8,
    },
    statusHeader: {
        fontSize: 28,
        fontWeight: '900',
        textAlign: 'center',
        marginBottom: theme.spacing.m,
    },
    subText: {
        fontSize: 16,
        color: theme.colors.textSecondary,
        textAlign: 'center',
        lineHeight: 22,
    },
    audioNoteContainer: {
        marginTop: theme.spacing.l,
        padding: theme.spacing.s,
        backgroundColor: '#f2f2f7',
        borderRadius: theme.borderRadius.m,
        width: '100%',
        alignItems: 'center',
    },
    audioText: {
        fontSize: 14,
        color: theme.colors.text,
        fontWeight: '600',
    },
    doneButton: {
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.l,
        borderRadius: theme.borderRadius.round,
        marginTop: theme.spacing.xl,
        alignItems: 'center',
    },
    doneButtonText: {
        fontSize: 18,
        fontWeight: 'bold',
        color: theme.colors.text,
    }
});
