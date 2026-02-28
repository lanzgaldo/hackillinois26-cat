import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Audio } from 'expo-av';
import { theme } from '../theme';

const CHECKLIST_ITEMS = [
    { id: 'engine', label: 'Engine Bay & Fluids' },
    { id: 'tires', label: 'Tires & Tracks' },
    { id: 'hydraulics', label: 'Hydraulics & Cylinders' },
    { id: 'cabin', label: 'Cabin Controls & Safety' },
    { id: 'attachments', label: 'Attachments & Linkages' },
];

export default function ChecklistScreen() {
    const navigation = useNavigation();
    const [statuses, setStatuses] = useState({});

    // Audio state
    const [recording, setRecording] = useState();
    const [permissionResponse, requestPermission] = Audio.usePermissions();
    const [hasRecording, setHasRecording] = useState(false);

    const setItemStatus = (id, status) => {
        setStatuses(prev => ({ ...prev, [id]: status }));
    };

    async function startRecording() {
        try {
            if (permissionResponse.status !== 'granted') {
                console.log('Requesting permission..');
                await requestPermission();
            }
            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
            });

            console.log('Starting recording..');
            const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY
            );
            setRecording(recording);
            console.log('Recording started');
        } catch (err) {
            console.error('Failed to start recording', err);
            Alert.alert("Microphone Error", "Failed to start recording.");
        }
    }

    async function stopRecording() {
        console.log('Stopping recording..');
        setRecording(undefined);
        await recording.stopAndUnloadAsync();
        await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
        });
        const uri = recording.getURI();
        console.log('Recording stopped and stored at', uri);
        setHasRecording(true);
    }

    const handleFinish = () => {
        // Check if all items have a status
        if (Object.keys(statuses).length < CHECKLIST_ITEMS.length) {
            Alert.alert('Incomplete', 'Please provide a status for all checklist items before finishing.');
            return;
        }

        // Calculate final status
        let finalStatus = 'green';
        const statusValues = Object.values(statuses);

        if (statusValues.includes('fail')) {
            finalStatus = 'red';
        } else if (statusValues.includes('warning')) {
            finalStatus = 'yellow';
        }

        navigation.navigate('Summary', {
            status: finalStatus,
            recordedNotes: hasRecording
        });
    };

    const getButtonStyles = (itemId, buttonType) => {
        const isSelected = statuses[itemId] === buttonType;
        let backgroundColor = theme.colors.surface;
        let textColor = theme.colors.text;
        let borderColor = theme.colors.border;

        if (isSelected) {
            textColor = 'white';
            borderColor = 'transparent';
            if (buttonType === 'pass') backgroundColor = theme.colors.success;
            if (buttonType === 'warning') backgroundColor = theme.colors.warning;
            if (buttonType === 'fail') backgroundColor = theme.colors.danger;

            // Override warning text color for better contrast
            if (buttonType === 'warning') textColor = theme.colors.text;
        }

        return { backgroundColor, textColor, borderColor };
    };

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Text style={styles.header}>Daily Inspection</Text>

                {CHECKLIST_ITEMS.map(item => (
                    <View key={item.id} style={styles.itemCard}>
                        <Text style={styles.itemLabel}>{item.label}</Text>

                        <View style={styles.buttonGroup}>
                            <TouchableOpacity
                                style={[
                                    styles.statusButton,
                                    {
                                        backgroundColor: getButtonStyles(item.id, 'pass').backgroundColor,
                                        borderColor: getButtonStyles(item.id, 'pass').borderColor
                                    }
                                ]}
                                onPress={() => setItemStatus(item.id, 'pass')}
                            >
                                <Text style={[styles.statusText, { color: getButtonStyles(item.id, 'pass').textColor }]}>
                                    Pass
                                </Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={[
                                    styles.statusButton,
                                    {
                                        backgroundColor: getButtonStyles(item.id, 'warning').backgroundColor,
                                        borderColor: getButtonStyles(item.id, 'warning').borderColor
                                    }
                                ]}
                                onPress={() => setItemStatus(item.id, 'warning')}
                            >
                                <Text style={[styles.statusText, { color: getButtonStyles(item.id, 'warning').textColor }]}>
                                    Warn
                                </Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={[
                                    styles.statusButton,
                                    {
                                        backgroundColor: getButtonStyles(item.id, 'fail').backgroundColor,
                                        borderColor: getButtonStyles(item.id, 'fail').borderColor
                                    }
                                ]}
                                onPress={() => setItemStatus(item.id, 'fail')}
                            >
                                <Text style={[styles.statusText, { color: getButtonStyles(item.id, 'fail').textColor }]}>
                                    Fail
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                ))}

                <View style={styles.audioSection}>
                    <Text style={styles.audioTitle}>Voice Notes</Text>
                    <TouchableOpacity
                        style={[styles.recordButton, recording && styles.recordingActive]}
                        onPress={recording ? stopRecording : startRecording}
                    >
                        <Text style={styles.recordButtonText}>
                            {recording ? 'Stop Recording' : (hasRecording ? 'Re-record Notes' : 'Record Voice Notes')}
                        </Text>
                    </TouchableOpacity>
                    {hasRecording && !recording && (
                        <Text style={styles.audioStatusText}>Audio note saved.</Text>
                    )}
                </View>

            </ScrollView>

            <View style={styles.footer}>
                <TouchableOpacity style={styles.finishButton} onPress={handleFinish}>
                    <Text style={styles.finishButtonText}>Finish Inspection</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: theme.colors.background,
    },
    scrollContent: {
        padding: theme.spacing.m,
        paddingBottom: 100, // Space for the fixed footer
    },
    header: {
        fontSize: 28,
        fontWeight: 'bold',
        color: theme.colors.text,
        marginBottom: theme.spacing.l,
        marginTop: theme.spacing.s,
    },
    itemCard: {
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.m,
        borderRadius: theme.borderRadius.l,
        marginBottom: theme.spacing.m,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    itemLabel: {
        fontSize: 18,
        fontWeight: '600',
        color: theme.colors.text,
        marginBottom: theme.spacing.m,
    },
    buttonGroup: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: theme.spacing.s,
    },
    statusButton: {
        flex: 1,
        paddingVertical: theme.spacing.s,
        alignItems: 'center',
        borderRadius: theme.borderRadius.m,
        borderWidth: 1,
    },
    statusText: {
        fontWeight: '600',
        fontSize: 14,
    },
    audioSection: {
        marginTop: theme.spacing.m,
        padding: theme.spacing.m,
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius.l,
    },
    audioTitle: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: theme.spacing.m,
        color: theme.colors.text,
    },
    recordButton: {
        backgroundColor: theme.colors.surface,
        borderWidth: 2,
        borderColor: theme.colors.primary,
        padding: theme.spacing.m,
        borderRadius: theme.borderRadius.m,
        alignItems: 'center',
    },
    recordingActive: {
        backgroundColor: '#fff0f0',
        borderColor: theme.colors.danger,
    },
    recordButtonText: {
        color: theme.colors.text,
        fontWeight: 'bold',
        fontSize: 16,
    },
    audioStatusText: {
        marginTop: theme.spacing.s,
        color: theme.colors.success,
        textAlign: 'center',
        fontWeight: '500',
    },
    footer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.m,
        paddingBottom: 30, // Extra padding for safe area
        borderTopWidth: 1,
        borderTopColor: theme.colors.border,
    },
    finishButton: {
        backgroundColor: theme.colors.primary,
        padding: theme.spacing.m,
        borderRadius: theme.borderRadius.l,
        alignItems: 'center',
    },
    finishButtonText: {
        color: '#000000', // Black text for high contrast on yellow
        fontSize: 18,
        fontWeight: 'bold',
    }
});
