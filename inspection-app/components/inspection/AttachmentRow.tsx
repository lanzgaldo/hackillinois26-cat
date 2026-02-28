import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable, Image, ScrollView, Modal, Alert, Linking } from 'react-native';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface Props {
    itemId: string;
    voiceNoteUri: string | null;
    voiceNoteTranscript: string | null;
    photos: string[];
    onVoiceStart: () => void;
    onVoiceStop: (uri: string | null) => void;
    onPhotoCapture: (uri: string) => void;
    onPhotoRemove: (uri: string) => void;
    onTranscriptReady: (transcript: string) => void;
}

export default function AttachmentRow({
    itemId,
    voiceNoteUri,
    voiceNoteTranscript,
    photos,
    onVoiceStart,
    onVoiceStop,
    onPhotoCapture,
    onPhotoRemove,
    onTranscriptReady
}: Props) {
    const [recording, setRecording] = useState<Audio.Recording | null>(null);
    const [fullScreenPhoto, setFullScreenPhoto] = useState<string | null>(null);

    const handleVoiceTap = async () => {
        if (recording) {
            // stop recording
            setRecording(null);
            await recording.stopAndUnloadAsync();
            await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
            const uri = recording.getURI();
            onVoiceStop(uri);
            // Mock transcription latency
            setTimeout(() => {
                onTranscriptReady("This is an AI generated mock transcript for the voice note.");
            }, 1500);
            return;
        }

        try {
            const response = await Audio.requestPermissionsAsync();
            if (response.status !== 'granted') {
                Alert.alert(
                    'Microphone Required',
                    'Microphone access required. Tap to enable in Settings.',
                    [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Settings', onPress: () => Linking.openSettings() }
                    ]
                );
                return;
            }

            await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
            const { recording: newRecording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
            setRecording(newRecording);
            onVoiceStart();
        } catch (err) {
            console.error(err);
            Alert.alert('Error', 'Failed to start recording');
        }
    };

    const handleCamera = async () => {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Camera Required', 'Camera access is required.');
            return;
        }
        const result = await ImagePicker.launchCameraAsync({ quality: 0.7 });
        if (!result.canceled && result.assets.length > 0) {
            onPhotoCapture(result.assets[0].uri);
        }
    };

    const handleLibrary = async () => {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Library Required', 'Photo library access is required.');
            return;
        }
        const result = await ImagePicker.launchImageLibraryAsync({ quality: 0.7 });
        if (!result.canceled && result.assets.length > 0) {
            onPhotoCapture(result.assets[0].uri);
        }
    };

    const hasVoice = !!voiceNoteUri || !!voiceNoteTranscript;
    const isRecording = !!recording;

    return (
        <View style={styles.container}>
            <View style={styles.row}>
                {/* VOICE ZONE */}
                <Pressable style={styles.actionZone} onPress={handleVoiceTap} accessibilityRole="button">
                    {hasVoice && !isRecording && <View style={styles.yellowDot} />}
                    <MaterialCommunityIcons
                        name={isRecording ? "stop-circle-outline" : "microphone-outline"}
                        size={24}
                        color={isRecording ? colors.statusRed : (hasVoice ? colors.primary : '#888')}
                    />
                    <Text style={[styles.label, { color: isRecording ? colors.statusRed : (hasVoice ? colors.primary : '#888') }]}>
                        {isRecording ? "RECORDING..." : (hasVoice ? "RECORDED" : "VOICE NOTE")}
                    </Text>
                </Pressable>

                <View style={styles.divider} />

                {/* CAMERA ZONE */}
                <Pressable style={styles.actionZone} onPress={handleCamera} accessibilityRole="button">
                    <MaterialCommunityIcons
                        name="camera-outline"
                        size={24}
                        color={photos.length > 0 ? colors.primary : '#888'}
                    />
                    <Text style={[styles.label, { color: photos.length > 0 ? colors.primary : '#888' }]}>
                        {photos.length > 0 ? `${photos.length} PHOTO${photos.length > 1 ? 'S' : ''}` : "PHOTO"}
                    </Text>
                </Pressable>

                <View style={styles.divider} />

                {/* LIBRARY ZONE */}
                <Pressable style={styles.actionZone} onPress={handleLibrary} accessibilityRole="button">
                    <MaterialCommunityIcons name="image-outline" size={24} color="#888" />
                    <Text style={styles.label}>LIBRARY</Text>
                </Pressable>
            </View>

            {/* PHOTO PREVIEWS */}
            {photos.length > 0 && (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.previewScroll}>
                    {photos.map(p => (
                        <Pressable key={p} onPress={() => setFullScreenPhoto(p)} style={styles.previewContainer}>
                            <Image source={{ uri: p }} style={styles.previewImage} />
                            <Pressable
                                style={styles.deleteButton}
                                onPress={() => onPhotoRemove(p)}
                                hitSlop={12}
                                accessibilityRole="button"
                            >
                                <Ionicons name="close" size={16} color="#FFF" />
                            </Pressable>
                        </Pressable>
                    ))}
                </ScrollView>
            )}

            {/* FULLSCREEN MODAL */}
            <Modal visible={!!fullScreenPhoto} transparent={true} animationType="fade">
                <View style={styles.modalContainer}>
                    <Pressable style={styles.modalClose} onPress={() => setFullScreenPhoto(null)}>
                        <Ionicons name="close" size={32} color="#FFF" />
                    </Pressable>
                    {fullScreenPhoto && <Image source={{ uri: fullScreenPhoto }} style={styles.fullImage} resizeMode="contain" />}
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        width: '100%',
        marginTop: 16,
    },
    row: {
        flexDirection: 'row',
        height: 56,
        backgroundColor: '#1E1E1E',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#2A2A2A',
        overflow: 'hidden',
    },
    actionZone: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        position: 'relative',
    },
    divider: {
        width: 1,
        backgroundColor: '#2A2A2A',
        height: '100%',
    },
    label: {
        fontFamily: typography.families.ui,
        fontSize: 11,
        marginTop: 4,
    },
    yellowDot: {
        position: 'absolute',
        top: 8,
        right: 28,
        width: 6,
        height: 6,
        borderRadius: 3,
        backgroundColor: colors.primary,
    },
    previewScroll: {
        marginTop: 12,
    },
    previewContainer: {
        marginRight: 12,
        position: 'relative',
        height: 64,
        width: 64,
    },
    previewImage: {
        width: 64,
        height: 64,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#2A2A2A',
    },
    deleteButton: {
        position: 'absolute',
        top: -6,
        right: -6,
        backgroundColor: colors.statusRed,
        width: 24,
        height: 24,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2,
        borderWidth: 1,
        borderColor: '#1E1E1E',
    },
    modalContainer: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.95)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    fullImage: {
        width: '100%',
        height: '80%',
    },
    modalClose: {
        position: 'absolute',
        top: 60,
        right: 24,
        zIndex: 10,
        padding: 8,
    }
});
