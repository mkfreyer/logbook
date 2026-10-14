import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useMemo } from 'react';
import HomeScreen from '../src/features/home/HomeScreen';
import ProgramsScreen from '../src/features/programs/ProgramsScreen';
import type { UniverseId } from '../src/navigation/UniverseContext';
import { UniversePager, type UniversePage } from '../src/navigation/UniversePager';

export default function UniversesScreen() {
  const { universe } = useLocalSearchParams<{ universe?: string }>();
  const pages = useMemo<UniversePage[]>(() => [
    { id: 'home', label: 'Accueil', content: <HomeScreen /> },
    { id: 'musculation', label: 'Musculation', content: <ProgramsScreen /> },
  ], []);
  const selectedId: UniverseId = pages.find(page => page.id === universe)?.id ?? 'home';
  const select = useCallback((id: UniverseId) => router.setParams({ universe: id }), []);
  return <UniversePager pages={pages} selectedId={selectedId} onSelect={select} />;
}
