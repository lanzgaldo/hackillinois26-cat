import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import Animated, {
    useAnimatedStyle,
    useAnimatedGestureHandler,
    useSharedValue,
    withSpring,
    withTiming,
    runOnJS
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface Props {
    suggestion: string;
    onAccept: () => void;
    onDismiss: () => void;
}

const SWIPE_THRESHOLD = -80;

export default function AISuggestionChip({ suggestion, onAccept, onDismiss }: Props) {
    const translateX = useSharedValue(0);
    const opacity = useSharedValue(1);
    const [isDismissed, setIsDismissed] = useState(false);

    // useAnimatedGestureHandler is technically deprecated in latest Reanimated 3 but we'll use standard 2 approaches since Expo 54 supports it
    // or use basic interpolation
    const panGesture = useAnimatedGestureHandler({
        onActive: (event) => {
            if (event.translationX < 0) {
                translateX.value = event.translationX;
            }
        },
        onEnd: (event) => {
            if (event.translationX < SWIPE_THRESHOLD) {
                translateX.value = withTiming(-500, { duration: 200 });
                opacity.value = withTiming(0, { duration: 200 }, () => {
                    runOnJS(setIsDismissed)(true);
                    runOnJS(onDismiss)();
                });
            } else {
                translateX.value = withSpring(0);
            }
        }
    });

    const animatedStyle = useAnimatedStyle(() => ({
        transform: [{ translateX: translateX.value }],
        opacity: opacity.value,
        display: isDismissed ? 'none' : 'flex'
    }));

    const handleDismiss = () => {
        setIsDismissed(true);
        onDismiss();
    };

    if (isDismissed) return null;

    return (
        <View style={styles.container}>
            <PanGestureHandler onGestureEvent={panGesture}>
                <Animated.View style={[styles.chip, animatedStyle]}>
                    <View style={styles.contentRow}>
                        <Ionicons name="sparkles" size={16} color={colors.primary} />
                        <Text style={styles.suggestionText} numberOfLines={2}>
                            {suggestion}
                        </Text>
                    </View>

                    <View style={styles.actionsRow}>
                        <Pressable onPress={handleDismiss} style={styles.actionButton} accessibilityRole="button">
                            <Text style={styles.dismissText}>DISMISS</Text>
                        </Pressable>
                        <View style={styles.divider} />
                        <Pressable onPress={onAccept} style={styles.actionButton} accessibilityRole="button">
                            <Text style={styles.acceptText}>ACCEPT</Text>
                        </Pressable>
                    </View>
                </Animated.View>
            </PanGestureHandler>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        marginVertical: 12,
    },
    chip: {
        backgroundColor: colors.surfaceCard,
        borderWidth: 1,
        borderColor: colors.primaryBorder,
        borderRadius: 8,
        overflow: 'hidden',
    },
    contentRow: {
        flexDirection: 'row',
        padding: 16,
        gap: 12,
        alignItems: 'center',
    },
    suggestionText: {
        flex: 1,
        fontFamily: typography.families.bodyMedium,
        fontSize: 14,
        color: colors.textPrimary,
    },
    actionsRow: {
        flexDirection: 'row',
        borderTopWidth: 1,
        borderTopColor: colors.border,
        height: 48,
    },
    actionButton: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
    divider: {
        width: 1,
        backgroundColor: colors.border,
    },
    dismissText: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: colors.textSecondary,
    },
    acceptText: {
        fontFamily: typography.families.ui,
        fontSize: 14,
        color: colors.primary,
    }
});
