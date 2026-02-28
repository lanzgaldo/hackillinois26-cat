import { useEffect } from 'react';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useFonts, Barlow_400Regular, Barlow_500Medium } from '@expo-google-fonts/barlow';
import { BarlowCondensed_700Bold, BarlowCondensed_900Black } from '@expo-google-fonts/barlow-condensed';
import { ShareTechMono_400Regular } from '@expo-google-fonts/share-tech-mono';
import { InspectionProvider } from '../context/InspectionContext';
import { colors } from '../constants/colors';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
    const [loaded] = useFonts({
        Barlow_400Regular,
        Barlow_500Medium,
        BarlowCondensed_700Bold,
        BarlowCondensed_900Black,
        ShareTechMono_400Regular,
    });

    useEffect(() => {
        if (loaded) {
            SplashScreen.hideAsync();
        }
    }, [loaded]);

    if (!loaded) {
        return null;
    }

    return (
        <InspectionProvider>
            <Stack
                screenOptions={{
                    headerStyle: { backgroundColor: colors.background },
                    headerTintColor: colors.textPrimary,
                    headerShadowVisible: false,
                    contentStyle: { backgroundColor: colors.background },
                }}
            >
                <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
                <Stack.Screen name="parts/index" options={{ title: 'Parts Order' }} />
            </Stack>
        </InspectionProvider>
    );
}
