import type { ExercisePerformance } from './history';

export interface PreviousPerformance {
  performance: ExercisePerformance;
  comparison: 'same_series' | 'same_type' | 'exercise';
}
export interface ActivityDay { key: string; label: string; count: number; today: boolean }
export interface HomeActivity { sessionCount: number; totalCompleted: number; days: ActivityDay[] }

export function localDayKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
/** Monday through Sunday in the device timezone. Calendar arithmetic includes DST. */
export function localWeek(now: Date) {
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (now.getDay() + 6) % 7);
  const nextMonday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 7);
  const days: ActivityDay[] = ['L', 'M', 'M', 'J', 'V', 'S', 'D'].map((label, index) => {
    const key = localDayKey(new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + index));
    return { key, label, count: 0, today: key === localDayKey(now) };
  });
  return { from: monday.toISOString(), until: nextMonday.toISOString(), days };
}
