import React, { useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Animated, {
    useSharedValue,
    useAnimatedStyle,
    withRepeat,
    withSequence,
    withTiming
} from 'react-native-reanimated';
import { colors } from '../../constants/colors';

export default function FloatingActionTab() {
    const [isRecording, setIsRecording] = useState(false);
    const pulseScale = useSharedValue(1);

    const toggleRecording = () => {
        const newState = !isRecording;
        setIsRecording(newState);
        if (newState) {
            pulseScale.value = withRepeat(
                withSequence(
                    withTiming(1.2, { duration: 500 }),
                    withTiming(1, { duration: 500 })
                ),
                -1,
                true
            );
        } else {
            pulseScale.value = withTiming(1);
        }
    };

    const animatedStyle = useAnimatedStyle(() => ({
        transform: [{ scale: pulseScale.value }],
    }));

    return (
        <View style={styles.container}>
            <Animated.View style={animatedStyle}>
                <Pressable
                    style={[styles.actionButton, { backgroundColor: isRecording ? colors.statusRedDim : 'transparent' }]}
                    onPress={toggleRecording}
                    accessibilityRole="button"
                    accessibilityLabel="Record Voice Note"
                >
                    <Ionicons
                        name={isRecording ? "stop" : "mic"}
                        size={24}
                        color={isRecording ? colors.statusRed : colors.primary}
                    />
                </Pressable>
            </Animated.View>
            <View style={styles.divider} />
            <Pressable
                style={styles.actionButton}
                accessibilityRole="button"
                accessibilityLabel="Open Notes"
            >
                <Ionicons name="pencil" size={24} color={colors.textPrimary} />
            </Pressable>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        bottom: 120, // Above the footer
        right: 20,
        backgroundColor: colors.elevatedSurface,
        borderRadius: 32,
        flexDirection: 'row',
        alignItems: 'center',
        padding: 4,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.5,
        shadowRadius: 8,
        elevation: 8,
        borderWidth: 1,
        borderColor: colors.border,
        zIndex: 5,
    },
    actionButton: {
        width: 56,
        height: 56,
        borderRadius: 28,
        alignItems: 'center',
        justifyContent: 'center',
    },
    divider: {
        width: 1,
        height: 32,
        backgroundColor: colors.border,
        marginHorizontal: 4,
    }
});
