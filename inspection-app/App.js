import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import ChecklistScreen from './src/screens/ChecklistScreen';
import SummaryScreen from './src/screens/SummaryScreen';
import { theme } from './src/theme';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Checklist"
          screenOptions={{
            headerStyle: {
              backgroundColor: theme.colors.primary,
            },
            headerTintColor: '#000000',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen
            name="Checklist"
            component={ChecklistScreen}
            options={{ title: 'Machine Inspection' }}
          />
          <Stack.Screen
            name="Summary"
            component={SummaryScreen}
            options={{
              title: 'Inspection Results',
              headerBackVisible: false // Prevent going back to checklist without pressing New Inspection
            }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
