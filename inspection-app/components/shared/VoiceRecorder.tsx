import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, StyleSheet, Alert } from 'react-native';
import { Audio } from 'expo-av';
import Animated, {
    useAnimatedStyle,
    useSharedValue,
    withRepeat,
    withTiming,
    withSequence
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { useInspection } from '../../context/InspectionContext';

interface Props {
    itemId: string;
}

export default function VoiceRecorder({ itemId }: Props) {
    const { addNote } = useInspection();
    const [recording, setRecording] = useState<Audio.Recording | null>(null);
    const [permissionResponse, requestPermission] = Audio.usePermissions();

    const pulseScale = useSharedValue(1);

    useEffect(() => {
        if (recording) {
            pulseScale.value = withRepeat(
                withSequence(
                    withTiming(1.15, { duration: 500 }),
                    withTiming(1, { duration: 500 })
                ),
                -1,
                true
            );
        } else {
            pulseScale.value = withTiming(1);
        }
    }, [recording]);

    const animatedStyle = useAnimatedStyle(() => ({
        transform: [{ scale: pulseScale.value }],
        opacity: recording ? 0.9 : 1
    }));

    async function startRecording() {
        try {
            if (permissionResponse?.status !== 'granted') {
                const response = await requestPermission();
                if (response.status !== 'granted') return;
            }

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
            });

            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY
            );
            setRecording(recording);
        } catch (err) {
            console.error('Failed to start recording', err);
            Alert.alert('Microphone Error', 'Failed to start recording.');
        }
    }

    async function stopRecording() {
        if (!recording) return;

        setRecording(null);
        await recording.stopAndUnloadAsync();
        await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
        const uri = recording.getURI();

        // Simulate AI transcription for now
        setTimeout(() => {
            addNote(itemId, `[Voice Note Transcribed] Requires attention. Audio saved at ${uri}`, 'voice');
        }, 1500);
    }

    return (
        <View style={styles.container}>
            <Animated.View style={[styles.iconContainer, animatedStyle]}>
                <Pressable
                    onPress={recording ? stopRecording : startRecording}
                    style={[styles.button, { backgroundColor: recording ? colors.statusRedDim : colors.surfaceCard }]}
                    accessibilityRole="button"
                    accessibilityLabel={recording ? 'Stop Recording' : 'Start Voice Recording'}
                >
                    <Ionicons
                        name={recording ? "stop" : "mic"}
                        size={32}
                        color={recording ? colors.statusRed : colors.primary}
                    />
                </Pressable>
            </Animated.View>
            <Text style={styles.label}>
                {recording ? 'RECORDING...' : 'VOICE NOTE'}
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        alignItems: 'center',
        gap: 8,
    },
    iconContainer: {
        borderRadius: 32,
    },
    button: {
        width: 64, // Big touch target
        height: 64,
        borderRadius: 32,
        borderWidth: 1,
        borderColor: colors.border,
        alignItems: 'center',
        justifyContent: 'center',
    },
    label: {
        fontFamily: typography.families.ui,
        fontSize: typography.sizes.minimumLabel,
        color: colors.textSecondary,
    }
});
