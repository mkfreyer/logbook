import type { Database } from './types';
import type { WeightMode } from '../domain/training';
import { localDayKey, localWeek, type HomeActivity, type PreviousPerformance } from '../domain/activity';
import { exercisePoints, type ExerciseHistory, type ExercisePerformance, type ExerciseVisit,
  type HistoricalExercise, type HistoryFilter, type HistoryOverview, type HistoryProgram,
  type HistoryRange, type HistorySession, type HistoryStats } from '../domain/history';

const PAGE_SIZE = 20;
export const HISTORY_CHART_LIMIT = 120;
type Read = <T>(operation: (db: Database) => Promise<T>) => Promise<T>;
type Param = string | number | null;
function scope(filter: HistoryFilter) {
  const clauses = ["s.status = 'completed'", 's.finished_at < ?'], params: Param[] = [filter.until];
  if (!Number.isFinite(Date.parse(filter.until)) || filter.from && !Number.isFinite(Date.parse(filter.from))) throw new Error('Période invalide.');
  if (filter.from) { clauses.push('s.finished_at >= ?'); params.push(filter.from); }
  if (filter.programId) { clauses.push('s.source_program_id = ?'); params.push(filter.programId); }
  return { sql: clauses.join(' AND '), params };
}
const sessionFields = `s.id, s.source_program_id AS sourceProgramId, s.source_workout_template_id AS sourceWorkoutTemplateId,
  s.workout_name AS workoutName, s.program_name AS programName, s.started_at AS startedAt, s.finished_at AS finishedAt,
  ROUND((julianday(s.finished_at) - julianday(s.started_at)) * 86400000) AS durationMs`;
const actualFields = `COUNT(p.id) AS performedSetCount, SUM(p.weight_kg * p.reps) AS loggedTonnageKg,
  COUNT(p.weight_kg) AS chargedSetCount, COUNT(p.id) - COUNT(p.weight_kg) AS unchargedSetCount`;
function checkedStats<T extends HistoryStats | HistorySession>(row: T): T {
  for (const value of [row.durationMs, row.performedSetCount, row.loggedTonnageKg, row.chargedSetCount, row.unchargedSetCount]) {
    if (value !== null && (!Number.isFinite(value) || value < 0)) throw new Error('Les données de cet historique dépassent la plage de calcul ou ont des horaires incohérents.');
  }
  if (row.durationMs === null) throw new Error('Les horaires de cet historique sont incohérents.');
  return row;
}
function boundedPage(value: number, count: number) {
  if (!Number.isSafeInteger(value) || value < 0) throw new Error('Page invalide.');
  return Math.max(0, Math.min(value, count - 1));
}

/** Read-only actual snapshots. Shares the execution queue, without loading all
 * workouts: SQL aggregates, 20 visits/page and at most 120 chart sessions. */
export class HistoryRepository {
  constructor(private readonly read: Read) {}
  /** Context comes from the active snapshot, never from mutable catalog targets.
   * Rank exact type+position first, then same type, then last non-warmup result.
   * Within a rank, use the latest completed execution, across all programs. */
  previousPerformance(sessionId: string, setId: string): Promise<PreviousPerformance | null> {
    return this.read(async db => {
      const current = await db.getFirstAsync<{ exerciseId: string; mode: WeightMode; kind: string; position: number; startedAt: string }>(
        `SELECT e.source_catalog_exercise_id AS exerciseId, e.weight_mode AS mode,
          t.kind, t.series_index AS position, s.started_at AS startedAt
         FROM workout_sessions s JOIN session_sets t ON t.session_id = s.id
         JOIN session_exercises e ON e.id = t.session_exercise_id AND e.session_id = s.id
         WHERE s.id = ? AND t.id = ? AND s.status = 'active'
           AND NOT EXISTS (SELECT 1 FROM performed_sets p WHERE p.session_set_id = t.id)`, sessionId, setId);
      if (!current) return null;
      const row = await db.getFirstAsync<ExercisePerformance>(`SELECT p.id, s.id AS sessionId,
        e.id AS sessionExerciseId, e.name AS exerciseName, s.workout_name AS workoutName,
        s.program_name AS programName, s.finished_at AS finishedAt, p.performed_at AS performedAt,
        p.sort_order AS sortOrder, t.series_index AS seriesIndex, t.label, t.kind,
        p.weight_kg AS weightKg, p.reps, p.rir, e.weight_mode AS weightMode
        FROM workout_sessions s JOIN performed_sets p ON p.session_id = s.id
        JOIN session_sets t ON t.id = p.session_set_id AND t.session_id = s.id
        JOIN session_exercises e ON e.id = t.session_exercise_id AND e.session_id = s.id
        WHERE s.status = 'completed' AND s.id != ? AND s.finished_at <= ?
          AND e.source_catalog_exercise_id = ? AND e.weight_mode = ?
          AND ${current.kind === 'warmup' ? "t.kind = 'warmup'" : "t.kind != 'warmup'"}
        ORDER BY CASE WHEN t.kind = ? AND t.series_index = ? THEN 0 WHEN t.kind = ? THEN 1 ELSE 2 END,
          s.finished_at DESC, s.id DESC,
          CASE WHEN t.kind = ? THEN ABS(t.series_index - ?) ELSE 0 END, p.sort_order DESC LIMIT 1`,
      sessionId, current.startedAt, current.exerciseId, current.mode, current.kind, current.position, current.kind, current.kind, current.position);
      return row ? { performance: row, comparison: row.kind === current.kind
        ? row.seriesIndex === current.position ? 'same_series' : 'same_type' : 'exercise' } : null;
    });
  }

  homeActivity(now = new Date()): Promise<HomeActivity> {
    return this.read(async db => {
      const week = localWeek(now);
      const rows = await db.getAllAsync<{ finishedAt: string }>(`SELECT finished_at AS finishedAt FROM workout_sessions
        WHERE status = 'completed' AND finished_at >= ? AND finished_at < ?`, week.from, week.until);
      const total = await db.getFirstAsync<{ count: number }>("SELECT COUNT(*) AS count FROM workout_sessions WHERE status = 'completed'");
      const days = week.days.map(day => ({ ...day }));
      for (const row of rows) {
        const day = days.find(item => item.key === localDayKey(new Date(row.finishedAt)));
        if (day) day.count++;
      }
      return { sessionCount: rows.length, totalCompleted: total!.count, days };
    });
  }
  private async stats(db: Database, filter: HistoryFilter): Promise<HistoryStats> {
    const where = scope(filter);
    const row = await db.getFirstAsync<HistoryStats>(`WITH visits AS (
      SELECT ${sessionFields}, ${actualFields} FROM workout_sessions s
      LEFT JOIN performed_sets p ON p.session_id = s.id WHERE ${where.sql} GROUP BY s.id)
      SELECT COUNT(*) AS sessionCount,
      CASE WHEN COUNT(*) = COUNT(durationMs) AND COALESCE(MIN(durationMs), 0) >= 0
        THEN COALESCE(SUM(durationMs), 0) ELSE NULL END AS durationMs,
      COALESCE(SUM(performedSetCount), 0) AS performedSetCount, SUM(loggedTonnageKg) AS loggedTonnageKg,
      COALESCE(SUM(chargedSetCount), 0) AS chargedSetCount, COALESCE(SUM(unchargedSetCount), 0) AS unchargedSetCount FROM visits`, ...where.params);
    return checkedStats(row!);
  }
  overview(filter: HistoryFilter, requestedPage = 0, previous?: HistoryRange | null): Promise<HistoryOverview> {
    return this.read(async db => {
      const where = scope(filter), stats = await this.stats(db, filter);
      const pageCount = Math.ceil(stats.sessionCount / PAGE_SIZE), page = boundedPage(requestedPage, pageCount);
      const select = `SELECT ${sessionFields}, ${actualFields} FROM workout_sessions s LEFT JOIN performed_sets p ON p.session_id = s.id
        WHERE ${where.sql} GROUP BY s.id ORDER BY s.finished_at DESC, s.id DESC`;
      const sessions = await db.getAllAsync<HistorySession>(`${select} LIMIT ? OFFSET ?`, ...where.params, PAGE_SIZE, page * PAGE_SIZE);
      const points = await db.getAllAsync<HistorySession>(`${select} LIMIT ?`, ...where.params, HISTORY_CHART_LIMIT);
      const programs = await db.getAllAsync<HistoryProgram>(`SELECT s.source_program_id AS id,
        (SELECT latest.program_name FROM workout_sessions latest WHERE latest.status = 'completed'
          AND latest.source_program_id = s.source_program_id ORDER BY latest.finished_at DESC, latest.id DESC LIMIT 1) AS name,
        COUNT(*) AS sessionCount, CASE WHEN p.id IS NULL THEN 1 ELSE 0 END AS deleted
        FROM workout_sessions s LEFT JOIN programs p ON p.id = s.source_program_id
        WHERE ${where.sql} GROUP BY s.source_program_id ORDER BY MAX(s.finished_at) DESC, s.source_program_id`, ...where.params);
      return { stats, previous: previous ? await this.stats(db, { ...previous, programId: filter.programId }) : null,
        programs, sessions: sessions.map(checkedStats), points: points.reverse().map(checkedStats), page, pageCount };
    });
  }
  exercises(range: HistoryRange): Promise<HistoricalExercise[]> {
    return this.read(async db => {
      const where = scope(range);
      const rows = await db.getAllAsync<HistoricalExercise>(`WITH actual AS (SELECT e.source_catalog_exercise_id AS id,
        e.name, e.muscle_group AS muscleGroup, e.equipment, e.instructions, s.id AS sessionId,
        ROW_NUMBER() OVER (PARTITION BY e.source_catalog_exercise_id ORDER BY s.finished_at DESC, s.id DESC, p.sort_order DESC) AS position
        FROM workout_sessions s
        JOIN performed_sets p ON p.session_id = s.id
        JOIN session_sets t ON t.id = p.session_set_id AND t.session_id = s.id
        JOIN session_exercises e ON e.id = t.session_exercise_id AND e.session_id = s.id
        WHERE ${where.sql}), counts AS (SELECT id, COUNT(DISTINCT sessionId) AS sessionCount FROM actual GROUP BY id)
        SELECT a.id, a.name, a.muscleGroup, a.equipment, a.instructions, c.sessionCount FROM actual a
        JOIN counts c ON c.id = a.id WHERE a.position = 1`, ...where.params);
      return rows.sort((a, b) => a.name.localeCompare(b.name, 'fr'));
    });
  }
  exercise(exerciseId: string, range: HistoryRange, requestedMode?: WeightMode, requestedPage = 0): Promise<ExerciseHistory> {
    return this.read(async db => {
      const where = scope(range);
      const joins = `FROM workout_sessions s JOIN performed_sets p ON p.session_id = s.id
        JOIN session_sets t ON t.id = p.session_set_id AND t.session_id = s.id
        JOIN session_exercises e ON e.id = t.session_exercise_id AND e.session_id = s.id`;
      const base = `${where.sql} AND e.source_catalog_exercise_id = ?`, params: Param[] = [...where.params, exerciseId];
      // Available modes and metadata are stable across period changes. Never
      // silently switch an explicitly selected mode when that period is empty.
      const identity = "s.status = 'completed' AND e.source_catalog_exercise_id = ?";
      const modes = (await db.getAllAsync<{ mode: WeightMode }>(`SELECT e.weight_mode AS mode ${joins}
        WHERE ${identity} GROUP BY e.weight_mode ORDER BY MAX(s.finished_at) DESC, e.weight_mode`, exerciseId)).map(row => row.mode);
      const mode = requestedMode ?? modes[0] ?? null;
      const exercise = await db.getFirstAsync<HistoricalExercise>(`SELECT e.source_catalog_exercise_id AS id, e.name,
        e.muscle_group AS muscleGroup, e.equipment, e.instructions, 0 AS sessionCount ${joins}
        WHERE ${identity} AND e.weight_mode = ? ORDER BY s.finished_at DESC, s.id DESC, p.sort_order DESC LIMIT 1`, exerciseId, mode);
      const count = await db.getFirstAsync<{ count: number }>(`SELECT COUNT(DISTINCT s.id) AS count ${joins}
        WHERE ${base} AND e.weight_mode = ?`, ...params, mode);
      const sessionCount = count!.count, pageCount = Math.ceil(sessionCount / PAGE_SIZE), page = boundedPage(requestedPage, pageCount);
      if (exercise) exercise.sessionCount = sessionCount;
      const visitIds = async (limit: number, offset: number) => (await db.getAllAsync<{ id: string }>(
        `SELECT s.id ${joins} WHERE ${base} AND e.weight_mode = ? GROUP BY s.id
          ORDER BY s.finished_at DESC, s.id DESC LIMIT ? OFFSET ?`, ...params, mode, limit, offset)).map(row => row.id);
      const pageIds = await visitIds(PAGE_SIZE, page * PAGE_SIZE), chartIds = await visitIds(HISTORY_CHART_LIMIT, 0);
      const ids = [...new Set([...pageIds, ...chartIds])];
      const rows = ids.length ? await db.getAllAsync<ExercisePerformance>(`SELECT p.id, s.id AS sessionId, e.id AS sessionExerciseId,
        e.name AS exerciseName, s.workout_name AS workoutName, s.program_name AS programName, s.finished_at AS finishedAt,
        p.performed_at AS performedAt, p.sort_order AS sortOrder, t.series_index AS seriesIndex, t.label, t.kind,
        p.weight_kg AS weightKg, p.reps, p.rir, e.weight_mode AS weightMode ${joins}
        WHERE s.id IN (${ids.map(() => '?').join(',')}) AND s.status = 'completed'
          AND e.source_catalog_exercise_id = ? AND e.weight_mode = ?
        ORDER BY s.finished_at DESC, s.id DESC, p.sort_order`, ...ids, exerciseId, mode) : [];
      const visits: ExerciseVisit[] = pageIds.map(id => {
        const group = rows.filter(row => row.sessionId === id), first = group[0]!;
        return { sessionId: id, finishedAt: first.finishedAt, workoutName: first.workoutName, programName: first.programName, performances: group };
      });
      const points = exercisePoints(rows.filter(row => chartIds.includes(row.sessionId)));
      for (const point of points) if (point.loggedTonnageKg !== null && !Number.isFinite(point.loggedTonnageKg)) throw new Error('Le tonnage dépasse la plage de calcul.');
      return { exercise, modes, mode, sessionCount, visits, points, page, pageCount,
        lastPerformance: rows.filter(row => row.sessionId === chartIds[0]).at(-1) ?? null };
    });
  }
}
