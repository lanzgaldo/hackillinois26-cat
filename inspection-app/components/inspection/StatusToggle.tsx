import React, { useEffect } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { Status } from '../../constants/inspectionCategories';

interface StatusToggleProps {
    value: Status;
    onChange: (value: Status) => void;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export default function StatusToggle({ value, onChange }: StatusToggleProps) {
    return (
        <View style={styles.container}>
            <ToggleButton type="green" currentValue={value} onPress={onChange} />
            <ToggleButton type="yellow" currentValue={value} onPress={onChange} />
            <ToggleButton type="red" currentValue={value} onPress={onChange} />
        </View>
    );
}

interface ToggleButtonProps {
    type: 'green' | 'yellow' | 'red';
    currentValue: Status;
    onPress: (val: Status) => void;
}

function ToggleButton({ type, currentValue, onPress }: ToggleButtonProps) {
    const isActive = currentValue === type;
    const scale = useSharedValue(isActive ? 1.05 : 1);

    useEffect(() => {
        scale.value = withSpring(isActive ? 1.05 : 1, { mass: 0.5, damping: 12 });
    }, [isActive]);

    const handlePressIn = () => {
        scale.value = withSpring(0.97);
    };

    const handlePressOut = () => {
        scale.value = withSpring(isActive ? 1.05 : 1);
    };

    const handlePress = () => {
        if (!isActive) {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            onPress(type);
        }
    };

    const animatedStyle = useAnimatedStyle(() => {
        return {
            transform: [{ scale: scale.value }],
        };
    });

    let bgColor = colors.surfaceCard;
    let activeBgColor = '';
    let iconName: keyof typeof Ionicons.glyphMap = 'checkmark-circle';
    let label = '';

    switch (type) {
        case 'green':
            activeBgColor = colors.statusGreen;
            iconName = 'checkmark-circle';
            label = 'PASS';
            break;
        case 'yellow':
            activeBgColor = colors.statusYellow;
            iconName = 'warning';
            label = 'WARN';
            break;
        case 'red':
            activeBgColor = colors.statusRed;
            iconName = 'close-circle';
            label = 'FAIL';
            break;
    }

    const contentColor = isActive && type === 'yellow' ? '#000000' : (isActive ? '#FFFFFF' : colors.textSecondary);

    return (
        <AnimatedPressable
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            onPress={handlePress}
            style={[
                styles.button,
                animatedStyle,
                {
                    backgroundColor: isActive ? activeBgColor : bgColor,
                    borderColor: isActive ? activeBgColor : colors.border,
                }
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={`Mark as ${label}`}
        >
            <Ionicons name={iconName} size={24} color={contentColor} />
            <Text style={[styles.label, { color: contentColor }]}>
                {label}
            </Text>
        </AnimatedPressable>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        gap: 8,
    },
    button: {
        flex: 1,
        height: 64, // Greater than the 56px minimum touch target
        minHeight: 56,
        borderRadius: 8,
        borderWidth: 1,
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    },
    label: {
        fontFamily: typography.families.ui,
        fontSize: typography.sizes.minimumLabel,
        marginTop: 4,
    }
});
