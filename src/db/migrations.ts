import type { Database } from './types';
import { CATALOG_CREATED_AT, INITIAL_EXERCISES } from './exerciseCatalog';

export const DATABASE_VERSION = 2;

const versionOne = `
  CREATE TABLE programs (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 1000),
    sport_type TEXT NOT NULL DEFAULT 'musculation' CHECK(sport_type = 'musculation'),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE workout_templates (
    id TEXT PRIMARY KEY NOT NULL,
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(program_id, sort_order)
  );

  CREATE INDEX programs_updated_at ON programs(updated_at DESC, created_at DESC, id);
  CREATE INDEX workouts_program_order ON workout_templates(program_id, sort_order, id);
`;

/** Preparation data only. Performed sessions will use independent snapshots;
 * do not add cascading history foreign keys to these editable templates. */
const versionTwo = `
  CREATE TABLE exercise_catalog (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    muscle_group TEXT NOT NULL CHECK(length(trim(muscle_group)) BETWEEN 1 AND 80),
    equipment TEXT NOT NULL CHECK(length(trim(equipment)) BETWEEN 1 AND 80),
    instructions TEXT NOT NULL DEFAULT '' CHECK(length(instructions) <= 1000),
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total', 'per_hand', 'additional')),
    is_custom INTEGER NOT NULL CHECK(is_custom IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE workout_exercises (
    id TEXT PRIMARY KEY NOT NULL,
    workout_template_id TEXT NOT NULL REFERENCES workout_templates(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL REFERENCES exercise_catalog(id) ON DELETE RESTRICT,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_template_id, sort_order)
  );

  CREATE TABLE set_templates (
    id TEXT PRIMARY KEY NOT NULL,
    workout_exercise_id TEXT NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    label TEXT NOT NULL DEFAULT '' CHECK(length(label) <= 80),
    kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real', 'integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_exercise_id, sort_order)
  );

  CREATE INDEX exercises_workout_order ON workout_exercises(workout_template_id, sort_order, id);
  CREATE INDEX sets_exercise_order ON set_templates(workout_exercise_id, sort_order, id);
`;

/** No demo content: a new database contains no programs or workout templates. */
export async function initializeDatabase(db: Database): Promise<void> {
  // Foreign keys must be enabled before a transaction, on every connection.
  await db.execAsync('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;');
  const version = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
  const currentVersion = version?.user_version ?? 0;

  if (currentVersion > DATABASE_VERSION) {
    throw new Error('Cette base utilise une version plus récente. Mettez l’application à jour.');
  }

  if (currentVersion < DATABASE_VERSION) {
    await db.withTransactionAsync(async () => {
      if (currentVersion < 1) await db.execAsync(versionOne);
      if (currentVersion < 2) {
        await db.execAsync(versionTwo);
        for (const exercise of INITIAL_EXERCISES) {
          await db.runAsync(
            `INSERT INTO exercise_catalog (id, name, muscle_group, equipment, instructions, weight_mode, is_custom, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)`,
            exercise.id, exercise.name, exercise.muscleGroup, exercise.equipment,
            exercise.instructions ?? '', exercise.weightMode, CATALOG_CREATED_AT, CATALOG_CREATED_AT,
          );
        }
      }
      await db.execAsync(`PRAGMA user_version = ${DATABASE_VERSION};`);
    });
  }
}
