import React, { useState, useEffect } from 'react';
import {
    View, Text, StyleSheet, Pressable, TextInput, KeyboardAvoidingView, Platform, Modal,
    TouchableWithoutFeedback, Keyboard, ScrollView
} from 'react-native';
import Animated, {
    useSharedValue, useAnimatedStyle, withSpring, withTiming, runOnJS
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface Props {
    visible: boolean;
    itemName: string;
    transcript: string;
    isLoading: boolean;
    error: string | null;
    aiContext: any | null;
    onSave: (finalText: string, wasEdited: boolean, aiContext: any | null) => void;
    onRetry?: () => void;
    onCancel: () => void;
}

export default function TranscriptReviewSheet({ visible, itemName, transcript, isLoading, error, aiContext, onSave, onRetry, onCancel }: Props) {
    const insets = useSafeAreaInsets();
    const [isEditing, setIsEditing] = useState(false);
    const [text, setText] = useState(transcript);
    const translateY = useSharedValue(1000);
    const backdropOpacity = useSharedValue(0);

    useEffect(() => {
        if (visible) {
            setText(transcript);
            setIsEditing(false);
            backdropOpacity.value = withTiming(1, { duration: 300 });
            translateY.value = withSpring(0, { damping: 20, stiffness: 200 });
        } else {
            backdropOpacity.value = withTiming(0, { duration: 200 });
            translateY.value = withTiming(1000, { duration: 200 }, () => {
                runOnJS(setIsEditing)(false);
            });
        }
    }, [visible, transcript]);

    const handleClose = () => {
        Keyboard.dismiss();
        backdropOpacity.value = withTiming(0, { duration: 200 });
        translateY.value = withTiming(1000, { duration: 200 }, () => {
            runOnJS(onCancel)();
        });
    };

    const handlePrimaryAction = () => {
        Keyboard.dismiss();
        backdropOpacity.value = withTiming(0, { duration: 200 });
        translateY.value = withTiming(1000, { duration: 200 }, () => {
            runOnJS(onSave)(text, isEditing, aiContext);
        });
    };

    const handleSecondaryAction = () => {
        if (isEditing) {
            // Cancel edit
            Keyboard.dismiss();
            setIsEditing(false);
            setText(transcript);
        } else {
            // Enter edit mode
            setIsEditing(true);
        }
    };

    const sheetStyle = useAnimatedStyle(() => ({
        transform: [{ translateY: translateY.value }]
    }));
    const backdropStyle = useAnimatedStyle(() => ({
        opacity: backdropOpacity.value
    }));

    if (!visible) return null;

    return (
        <Modal visible={visible} transparent={true} animationType="none" statusBarTranslucent>
            <KeyboardAvoidingView
                style={styles.container}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                <TouchableWithoutFeedback onPress={handleClose}>
                    <Animated.View style={[styles.backdrop, backdropStyle]} />
                </TouchableWithoutFeedback>

                <Animated.View style={[styles.sheet, sheetStyle, { paddingBottom: Math.max(insets.bottom, 20) }]}>
                    <View style={styles.dragHandle} />

                    <View style={styles.headerRow}>
                        <Text style={styles.headerTitle}>{isLoading ? 'TRANSCRIBING...' : (error ? 'TRANSCRIPTION FAILED' : 'AI TRANSCRIPT')}</Text>
                        <Text style={styles.headerItemName} numberOfLines={1}>{itemName}</Text>
                    </View>

                    {isLoading ? (
                        <View style={styles.loadingContainer}>
                            <Text style={styles.staticText}>Analyzing your voice note...</Text>
                        </View>
                    ) : error ? (
                        <View style={styles.errorContainer}>
                            <Text style={styles.errorText}>{error}</Text>
                            <Text style={styles.errorSubText}>Your recording was saved.</Text>
                        </View>
                    ) : (
                        <View style={[
                            styles.textContainer,
                            isEditing && styles.textContainerEditing
                        ]}>
                            {isEditing ? (
                                <TextInput
                                    style={styles.textInput}
                                    value={text}
                                    onChangeText={setText}
                                    multiline
                                    scrollEnabled
                                    autoFocus
                                    selectionColor={colors.primary}
                                />
                            ) : (
                                <ScrollView style={{ minHeight: 100 }} showsVerticalScrollIndicator={false}>
                                    <Text style={styles.staticText}>{text}</Text>
                                </ScrollView>
                            )}
                            {isEditing && (
                                <Text style={styles.charCount}>{text.length} chars</Text>
                            )}
                        </View>
                    )}

                    <View style={styles.actionsRow}>
                        {isLoading ? (
                            <Pressable style={styles.secondaryButton} onPress={handleClose} accessibilityRole="button">
                                <Text style={styles.secondaryButtonText}>CANCEL</Text>
                            </Pressable>
                        ) : error ? (
                            <>
                                <Pressable style={styles.secondaryButton} onPress={onRetry} accessibilityRole="button">
                                    <Text style={styles.secondaryButtonText}>RETRY</Text>
                                </Pressable>
                                <View style={{ width: 12 }} />
                                <Pressable style={styles.primaryButton} onPress={() => { setText(""); handlePrimaryAction(); }} accessibilityRole="button">
                                    <Text style={styles.primaryButtonText}>SAVE WITHOUT AI</Text>
                                </Pressable>
                            </>
                        ) : (
                            <>
                                <Pressable style={styles.secondaryButton} onPress={handleSecondaryAction} accessibilityRole="button">
                                    <Text style={styles.secondaryButtonText}>{isEditing ? 'SAVE' : 'EDIT'}</Text>
                                </Pressable>
                                <View style={{ width: 12 }} />
                                <Pressable style={styles.primaryButton} onPress={isEditing ? handleClose : handlePrimaryAction} accessibilityRole="button">
                                    <Text style={styles.primaryButtonText}>{isEditing ? 'CANCEL' : 'OK'}</Text>
                                </Pressable>
                            </>
                        )}
                    </View>
                </Animated.View>
            </KeyboardAvoidingView>
        </Modal>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'flex-end',
    },
    backdrop: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0,0,0,0.72)',
    },
    sheet: {
        backgroundColor: colors.surfaceCard,
        borderTopLeftRadius: 16,
        borderTopRightRadius: 16,
        paddingHorizontal: 20,
        paddingTop: 12,
        maxHeight: '52%',
        borderTopWidth: 1,
        borderTopColor: colors.border,
    },
    dragHandle: {
        width: 36,
        height: 4,
        backgroundColor: '#2A2A2A',
        borderRadius: 2,
        alignSelf: 'center',
        marginBottom: 20,
    },
    headerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    headerTitle: {
        fontFamily: typography.families.ui,
        fontSize: 12,
        color: '#888',
    },
    headerItemName: {
        fontFamily: typography.families.mono,
        fontSize: 12,
        color: colors.primary,
        flex: 1,
        textAlign: 'right',
        marginLeft: 12,
    },
    textContainer: {
        backgroundColor: '#141414',
        borderWidth: 1,
        borderColor: '#2A2A2A',
        borderRadius: 10,
        padding: 16,
        minHeight: 100,
        maxHeight: 200,
        marginBottom: 24,
    },
    textContainerEditing: {
        backgroundColor: '#222',
        borderColor: colors.primary,
    },
    staticText: {
        fontFamily: typography.families.body,
        fontSize: 16,
        color: '#F2F0EB',
        lineHeight: 24,
    },
    textInput: {
        fontFamily: typography.families.body,
        fontSize: 16,
        color: '#F2F0EB',
        minHeight: 100,
        textAlignVertical: 'top',
    },
    charCount: {
        fontFamily: typography.families.mono,
        fontSize: 11,
        color: '#666',
        position: 'absolute',
        bottom: 8,
        right: 12,
    },
    actionsRow: {
        flexDirection: 'row',
        height: 56,
    },
    secondaryButton: {
        flex: 1,
        backgroundColor: '#1E1E1E',
        borderWidth: 1,
        borderColor: colors.primary,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    secondaryButtonText: {
        fontFamily: typography.families.ui,
        fontSize: 15,
        color: colors.primary,
    },
    primaryButton: {
        flex: 1,
        backgroundColor: colors.primary,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },
    primaryButtonText: {
        fontFamily: typography.families.ui,
        fontSize: 15,
        color: '#080808',
    },
    loadingContainer: {
        minHeight: 100,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 24,
    },
    errorContainer: {
        minHeight: 100,
        justifyContent: 'center',
        marginBottom: 24,
        padding: 16,
        backgroundColor: 'rgba(229, 57, 53, 0.08)',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: colors.statusRed,
    },
    errorText: {
        fontFamily: typography.families.body,
        fontSize: 16,
        color: colors.statusRed,
        marginBottom: 8,
    },
    errorSubText: {
        fontFamily: typography.families.body,
        fontSize: 14,
        color: '#888',
    }
});
