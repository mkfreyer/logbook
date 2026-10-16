import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { SeriesDisplayProvider } from '../src/store/SeriesDisplayProvider';
import { SeriesDisplaySettings } from '../src/features/settings/SeriesDisplaySettings';
import { SetTargetSummary } from '../src/features/training/shared';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionSummaryView } from '../src/features/sessions/SessionSummaryView';
import type { SetTemplate } from '../src/domain/training';
import type { WorkoutSession } from '../src/domain/session';
import type { ReactNode } from 'react';

const mockValues = new Map<string, string>();
const mockRead = jest.fn<(sql: string, key: string) => Promise<{ value: string } | null>>();
const mockWrite = jest.fn<(sql: string, key: string, value: string) => Promise<void>>();
const mockDb = { getFirstAsync: mockRead, runAsync: mockWrite };
const mockSessions = { getSession: jest.fn<(id: string) => Promise<WorkoutSession | null>>(), history: { previousPerformance: jest.fn<() => Promise<null>>() } };
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDb }));
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), replace: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: () => true },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(effect, [effect]) };
});
jest.mock('../src/store/SessionProvider', () => ({ useSessions: () => mockSessions }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);
const targets = { repsMin: 5, repsMax: 5, targetWeightKg: 40, targetRir: null, restAfterSec: 60 };
const planned: SetTemplate = { id: 'st', workoutExerciseId: 'we', sortOrder: 0, label: 'Montée', kind: 'warmup', notes: '', createdAt: '2026', updatedAt: '2026', ...targets };
const session: WorkoutSession = { id: 's', sourceWorkoutTemplateId: 'w', sourceProgramId: 'p', workoutName: 'Séance', programName: 'Programme',
  status: 'active', startedAt: '2026-10-16T12:00:00Z', finishedAt: null, rests: [], performances: [],
  exercises: [{ id: 'e', sessionId: 's', sourceWorkoutExerciseId: 'we', sourceCatalogExerciseId: 'bar', sortOrder: 0, name: 'Développé', muscleGroup: 'Pectoraux', equipment: 'Barre', instructions: '', notes: '', weightMode: 'total' }],
  sets: [{ id: 'set', sessionId: 's', sessionExerciseId: 'e', sourceSetTemplateId: 'st', seriesIndex: 0, sortOrder: 0, label: 'Montée', kind: 'warmup', notes: '', originalTargets: targets, targets }],
};
function App({ children }: { children?: ReactNode }) { return <SeriesDisplayProvider><SeriesDisplaySettings />{children}</SeriesDisplayProvider>; }
async function loaded(view: ReturnType<typeof render>) { await waitFor(() => expect(view.getByRole('radio', { name: 'Nom uniquement' }).props.accessibilityState.disabled).toBe(false)); }
beforeEach(() => {
  jest.resetAllMocks(); mockValues.clear(); mockValues.set('rest_sound_enabled', 'false');
  mockRead.mockImplementation(async (_sql, key) => mockValues.has(key) ? { value: mockValues.get(key)! } : null);
  mockWrite.mockImplementation(async (_sql, key, value) => { mockValues.set(key, value); });
  mockSessions.getSession.mockResolvedValue(session); mockSessions.history.previousPerformance.mockResolvedValue(null);
});
afterEach(cleanup);
test('display choice updates planned cards and the single active series without copying goals into actual fields', async () => {
  const view = render(<App><SetTargetSummary series={planned} mode="total" index={0} /><SessionScreen sessionId="s" /></App>); await loaded(view);
  await view.findByText('Montée · 1 / 1');
  fireEvent.press(view.getByRole('radio', { name: 'Numéro et nom' }));
  expect(view.getByText('Série 1 · Montée')).toBeTruthy(); expect(view.getByText('Série 1 · Montée · 1 / 1')).toBeTruthy();
  for (const label of ['Charge réelle (kg)', 'Répétitions réelles', 'RIR réel']) expect(view.getByLabelText(label).props.value).toBe('');
  expect(view.getAllByLabelText('Répétitions réelles')).toHaveLength(1);
  await waitFor(() => expect(mockValues.get('series_display')).toBe('"both"'));
  fireEvent.press(view.getByRole('radio', { name: 'Numéro uniquement' }));
  expect(view.getByText('Série 1 · 1 / 1')).toBeTruthy(); expect(view.queryByText('Série 1 · Montée')).toBeNull();
  await waitFor(() => expect(mockValues.get('series_display')).toBe('"number"'));
  expect(mockValues.get('rest_sound_enabled')).toBe('false');
});
test('the stored display choice is read after unmount/reopen, preserving the sound preference', async () => {
  const view = render(<App />); await loaded(view); fireEvent.press(view.getByRole('radio', { name: 'Numéro et nom' }));
  await waitFor(() => expect(mockValues.get('series_display')).toBe('"both"')); view.unmount();
  const reopened = render(<App />); await loaded(reopened);
  expect(reopened.getByRole('radio', { name: 'Numéro et nom' }).props.accessibilityState.checked).toBe(true);
  expect(mockValues.get('rest_sound_enabled')).toBe('false');
});
test('historical series use the display choice without changing their stored name, type, targets or performance', async () => {
  const completed: WorkoutSession = { ...session, status: 'completed', finishedAt: '2026-10-16T13:00:00Z',
    performances: [{ id: 'p', sessionId: 's', sessionSetId: 'set', sortOrder: 0, weightKg: 35, reps: 5, rir: null, performedAt: '2026-10-16T12:01:00Z', advancedAt: '2026-10-16T12:01:00Z' }] };
  const before = JSON.stringify(completed);
  const view = render(<App><SessionSummaryView session={completed} historical onExit={() => {}} onRetry={() => {}} /></App>); await loaded(view);
  fireEvent.press(view.getByRole('radio', { name: 'Numéro et nom' })); expect(view.getByText('1. Série 1 · Montée')).toBeTruthy();
  await waitFor(() => expect(mockValues.get('series_display')).toBe('"both"')); expect(JSON.stringify(completed)).toBe(before);
  expect(mockWrite.mock.calls.every(([, key]) => key === 'series_display')).toBe(true);
});
test('rapid choices persist in order while older completions never replace the latest visible intent', async () => {
  const jobs: (() => void)[] = [];
  mockWrite.mockImplementation((_sql, key, value) => new Promise(resolve => { jobs.push(() => { mockValues.set(key, value); resolve(); }); }));
  const view = render(<App />); await loaded(view);
  fireEvent.press(view.getByRole('radio', { name: 'Numéro uniquement' })); fireEvent.press(view.getByRole('radio', { name: 'Nom uniquement' })); fireEvent.press(view.getByRole('radio', { name: 'Numéro et nom' }));
  for (let i = 0; i < 3; i++) {
    await waitFor(() => expect(jobs.length).toBeGreaterThan(i)); await act(async () => { jobs[i]!(); });
    expect(view.getByRole('radio', { name: 'Numéro et nom' }).props.accessibilityState.checked).toBe(true);
  }
  expect(mockValues.get('series_display')).toBe('"both"'); expect(mockValues.get('rest_sound_enabled')).toBe('false');
});
test('failed display save rolls back to the confirmed mode, exposes retry and never changes sound', async () => {
  const view = render(<App />); await loaded(view); mockWrite.mockRejectedValueOnce(new Error('stockage indisponible'));
  fireEvent.press(view.getByRole('radio', { name: 'Numéro et nom' })); await view.findByRole('button', { name: 'Réessayer l’affichage des séries' });
  expect(view.getByRole('radio', { name: 'Nom uniquement' }).props.accessibilityState.checked).toBe(true);
  fireEvent.press(view.getByRole('button', { name: 'Réessayer l’affichage des séries' })); await loaded(view);
  expect(view.queryByRole('button', { name: 'Réessayer l’affichage des séries' })).toBeNull(); expect(mockValues.get('rest_sound_enabled')).toBe('false');
});
