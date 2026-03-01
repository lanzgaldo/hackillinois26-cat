import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../../constants/colors';
import { StyleSheet } from 'react-native';

/**
 * CAT TRACK — TAB NAVIGATOR STABILITY RULES
 * ==========================================
 * These rules must be preserved whenever new screens or components are added.
 * Violating them causes tab bar buttons to become untappable.
 *
 * 1. Every tab screen root View must have `flex: 1`
 * 2. Every ScrollView/FlatList must have `contentContainerStyle.paddingBottom: 80`
 * 3. No in-screen absolutely positioned element may have `zIndex` above 7
 * 4. DrawerMenu Animated.View must have `pointerEvents={isOpen ? 'auto' : 'none'}`
 * 5. KeyboardAvoidingView must only wrap individual screen content, never the Tabs
 * 6. SafeAreaProvider must be the outermost wrapper in app/_layout.tsx
 * 7. tabBarStyle must not have position absolute, allow auto layout
 * 8. After adding any new screen: run `npx expo start --clear` to flush route cache
 */

export default function TabLayout() {
    return (
        <Tabs
            screenOptions={{
                headerShown: false,
                tabBarHideOnKeyboard: true,
                tabBarActiveTintColor: colors.primary,
                tabBarInactiveTintColor: '#444',
                tabBarStyle: styles.tabBar,
                tabBarLabelStyle: {
                    fontSize: 11,
                    textTransform: 'uppercase',
                    letterSpacing: 1.1,
                    fontWeight: 'bold',
                }
            }}
        >
            <Tabs.Screen
                name="inspections"
                options={{
                    tabBarLabel: 'INSPECTIONS',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="clipboard-list-outline" size={24} color={color} />
                    )
                }}
            />
            <Tabs.Screen
                name="reports/index"
                options={{
                    tabBarLabel: 'REPORTS',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="file-document-outline" size={24} color={color} />
                    )
                }}
            />
            <Tabs.Screen
                name="favorites/index"
                options={{
                    tabBarLabel: 'FAVORITES',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="star-outline" size={24} color={color} />
                    )
                }}
            />
        </Tabs>
    );
}

const styles = StyleSheet.create({
    tabBar: {
        backgroundColor: '#1A1A1A',
        borderTopColor: '#333333',
        borderTopWidth: 1,
        height: 64,
        paddingBottom: 8,
        paddingTop: 4,
        elevation: 8,
        zIndex: 8,
    },
});
