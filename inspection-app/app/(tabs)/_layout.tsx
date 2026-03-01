import { Tabs } from 'expo-router';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

function CustomTabBar({ state, descriptors, navigation }: any) {
    const insets = useSafeAreaInsets();

    return (
        <View style={[styles.tabBar, { paddingBottom: Math.max(insets.bottom, 8) }]}>
            {state.routes.map((route: any, index: number) => {
                const { options } = descriptors[route.key];
                const label =
                    options.tabBarLabel !== undefined
                        ? options.tabBarLabel
                        : options.title !== undefined
                            ? options.title
                            : route.name;

                const isFocused = state.index === index;

                const onPress = () => {
                    const event = navigation.emit({
                        type: 'tabPress',
                        target: route.key,
                        canPreventDefault: true,
                    });

                    if (!isFocused && !event.defaultPrevented) {
                        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                        navigation.navigate(route.name, route.params);
                    }
                };

                const onLongPress = () => {
                    navigation.emit({
                        type: 'tabLongPress',
                        target: route.key,
                    });
                };

                let iconName: keyof typeof MaterialCommunityIcons.glyphMap = 'help';
                if (route.name === 'inspections') iconName = 'clipboard-list-outline';
                else if (route.name === 'reports') iconName = 'file-document-outline';

                return (
                    <Pressable
                        key={route.key}
                        accessibilityRole="button"
                        accessibilityState={isFocused ? { selected: true } : {}}
                        accessibilityLabel={options.tabBarAccessibilityLabel}
                        testID={options.tabBarTestID}
                        onPress={onPress}
                        onLongPress={onLongPress}
                        style={styles.tabItem}
                    >
                        {isFocused && <View style={styles.activeIndicator} />}
                        <MaterialCommunityIcons
                            name={iconName}
                            size={24}
                            color={isFocused ? colors.primary : '#444'}
                        />
                        <Text style={[styles.tabLabel, { color: isFocused ? colors.primary : '#444' }]}>
                            {label}
                        </Text>
                    </Pressable>
                );
            })}
        </View>
    );
}

export default function TabLayout() {
    return (
        <Tabs tabBar={props => <CustomTabBar {...props} />} screenOptions={{ headerShown: false }}>
            <Tabs.Screen
                name="inspections"
                options={{
                    tabBarLabel: 'INSPECTIONS',
                    href: '/(tabs)/inspections' as any,
                }}
            />
            <Tabs.Screen
                name="reports"
                options={{
                    tabBarLabel: 'REPORTS',
                    href: '/(tabs)/reports' as any,
                }}
            />
        </Tabs>
    );
}

const styles = StyleSheet.create({
    tabBar: {
        backgroundColor: '#0F0F0F',
        borderTopWidth: 1,
        borderTopColor: '#2A2A2A',
        flexDirection: 'row',
        position: 'absolute',
        bottom: 0,
        width: '100%',
    },
    tabItem: {
        flex: 1,
        height: 64,
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        gap: 4,
    },
    activeIndicator: {
        position: 'absolute',
        left: 0,
        top: 20,
        width: 2,
        height: 24,
        backgroundColor: colors.primary,
    },
    tabLabel: {
        fontFamily: typography.families.ui,
        fontSize: 11,
        textTransform: 'uppercase',
        letterSpacing: 1.1, // ~0.1em estimate given 11px font size
    },
});
