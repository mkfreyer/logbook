import { DarkTheme, Stack, ThemeProvider } from 'expo-router';
import { SQLiteProvider } from 'expo-sqlite';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useState } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { initializeDatabase } from '../src/db/migrations';
import { LogbookProvider } from '../src/store/LogbookProvider';
import { Button, Card, colors, EmptyState, Screen } from '../src/ui';

const theme = { ...DarkTheme, colors: { ...DarkTheme.colors, background: colors.background, card: colors.surface, text: colors.text, primary: colors.blue, border: colors.border } };

export default function RootLayout() {
  const [databaseError, setDatabaseError] = useState<Error | null>(null);
  const [attempt, setAttempt] = useState(0);
  // Expo can call onError while its provider renders. Defer our state update.
  const onDatabaseError = useCallback((error: Error) => { setTimeout(() => setDatabaseError(error), 0); }, []);
  return <GestureHandlerRootView style={{ flex: 1, backgroundColor: colors.background }}><SafeAreaProvider><ThemeProvider value={theme}>
    <StatusBar style="light" />
    {databaseError ? <Screen><Card>
      <EmptyState icon="lock-closed-outline" title="Stockage indisponible" description="Vos données locales n’ont pas pu être ouvertes. Fermez puis rouvrez l’application ou réessayez." />
      <Button label="Réessayer" onPress={() => { setDatabaseError(null); setAttempt(value => value + 1); }} />
    </Card></Screen> : <SQLiteProvider key={attempt} databaseName="logbook.db" onInit={initializeDatabase} onError={onDatabaseError}>
      <LogbookProvider>
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }}>
          <Stack.Screen name="programs/index" options={{ animation: 'none' }} />
        </Stack>
      </LogbookProvider>
    </SQLiteProvider>}
  </ThemeProvider></SafeAreaProvider></GestureHandlerRootView>;
}
