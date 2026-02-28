import React from 'react';
import { View, Text, Pressable, StyleSheet, Image, ScrollView, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { useInspection } from '../../context/InspectionContext';

interface Props {
    itemId: string;
}

export default function PhotoCapture({ itemId }: Props) {
    const { state, addPhoto, removePhoto } = useInspection();
    const photos = state.photos[itemId] || [];

    const takePhoto = async () => {
        const permissionResult = await ImagePicker.requestCameraPermissionsAsync();
        if (permissionResult.granted === false) {
            Alert.alert("Permission Refused", "You've refused to allow this app to access your camera!");
            return;
        }
        const result = await ImagePicker.launchCameraAsync({
            quality: 0.7,
        });
        if (!result.canceled) {
            addPhoto(itemId, result.assets[0].uri);
        }
    };

    const pickImage = async () => {
        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            quality: 0.7,
        });
        if (!result.canceled) {
            addPhoto(itemId, result.assets[0].uri);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.actionRow}>
                <Pressable style={styles.captureButton} onPress={takePhoto} accessibilityRole="button">
                    <Ionicons name="camera" size={28} color={colors.primary} />
                    <Text style={styles.buttonLabel}>CAMERA</Text>
                </Pressable>
                <Pressable style={styles.captureButton} onPress={pickImage} accessibilityRole="button">
                    <Ionicons name="images" size={28} color={colors.textSecondary} />
                    <Text style={styles.buttonLabel}>LIBRARY</Text>
                </Pressable>
            </View>

            {photos.length > 0 && (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.previewScroll}>
                    {photos.map(p => (
                        <View key={p.id} style={styles.previewContainer}>
                            <Image source={{ uri: p.uri }} style={styles.previewImage} />
                            <Pressable
                                style={styles.deleteButton}
                                onPress={() => removePhoto(itemId, p.id)}
                            >
                                <Ionicons name="close-circle" size={24} color={colors.statusRed} />
                            </Pressable>
                        </View>
                    ))}
                </ScrollView>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        width: '100%',
    },
    actionRow: {
        flexDirection: 'row',
        gap: 12,
    },
    captureButton: {
        flex: 1,
        height: 56, // Accessible height constraint
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: colors.surfaceCard,
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: 8,
    },
    buttonLabel: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: colors.textPrimary,
    },
    previewScroll: {
        marginTop: 16,
    },
    previewContainer: {
        marginRight: 12,
        position: 'relative',
    },
    previewImage: {
        width: 80,
        height: 80,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: colors.border,
    },
    deleteButton: {
        position: 'absolute',
        top: -8,
        right: -8,
        backgroundColor: colors.background,
        borderRadius: 12,
    }
});
