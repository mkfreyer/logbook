import type { Database } from './types';
import { CATALOG_CREATED_AT, INITIAL_EXERCISES } from './exerciseCatalog';

export const DATABASE_VERSION = 6;

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

/** Executions own their snapshots. Source IDs are provenance only, never cascading
 * references to editable preparation. Deleting any program cannot erase training. */
const versionThree = `
  CREATE TABLE workout_sessions (
    id TEXT PRIMARY KEY NOT NULL,
    source_workout_template_id TEXT NOT NULL,
    source_program_id TEXT NOT NULL,
    workout_name TEXT NOT NULL,
    program_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'completed')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    CHECK((status = 'active' AND finished_at IS NULL) OR (status = 'completed' AND finished_at IS NOT NULL AND finished_at >= started_at))
  );
  CREATE UNIQUE INDEX one_active_session ON workout_sessions((1)) WHERE status = 'active';
  CREATE TABLE session_exercises (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    source_workout_exercise_id TEXT NOT NULL,
    source_catalog_exercise_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    name TEXT NOT NULL, muscle_group TEXT NOT NULL, equipment TEXT NOT NULL,
    instructions TEXT NOT NULL, notes TEXT NOT NULL,
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total', 'per_hand', 'additional')),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id)
  );
  CREATE TABLE session_sets (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_exercise_id TEXT NOT NULL,
    source_set_template_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    series_index INTEGER NOT NULL CHECK(typeof(series_index) = 'integer' AND series_index >= 0),
    label TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    notes TEXT NOT NULL,
    original_targets TEXT NOT NULL CHECK(json_valid(original_targets)),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real','integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id),
    FOREIGN KEY(session_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE CASCADE
  );
  CREATE TABLE performed_sets (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_set_id TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    weight_kg REAL CHECK(weight_kg IS NULL OR (typeof(weight_kg) IN ('real','integer') AND weight_kg >= 0 AND weight_kg <= 1.7976931348623157e308)),
    reps INTEGER NOT NULL CHECK(typeof(reps) = 'integer' AND reps >= 0),
    rir INTEGER CHECK(rir IS NULL OR (typeof(rir) = 'integer' AND rir BETWEEN 0 AND 10)),
    performed_at TEXT NOT NULL, advanced_at TEXT CHECK(advanced_at IS NULL OR advanced_at >= performed_at),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id),
    FOREIGN KEY(session_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
  CREATE TABLE rest_intervals (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    performed_set_id TEXT NOT NULL UNIQUE,
    planned_seconds INTEGER NOT NULL CHECK(typeof(planned_seconds) = 'integer' AND planned_seconds BETWEEN 1 AND 86400),
    started_at TEXT NOT NULL, ended_at TEXT CHECK(ended_at IS NULL OR ended_at >= started_at),
    chronological_ms INTEGER CHECK(chronological_ms IS NULL OR (typeof(chronological_ms) = 'integer' AND chronological_ms >= 0)),
    active_ms INTEGER CHECK(active_ms IS NULL OR (typeof(active_ms) = 'integer' AND active_ms >= 0 AND active_ms <= chronological_ms)),
    CHECK((ended_at IS NULL AND chronological_ms IS NULL AND active_ms IS NULL) OR
      (ended_at IS NOT NULL AND chronological_ms IS NOT NULL AND active_ms IS NOT NULL)),
    FOREIGN KEY(performed_set_id, session_id) REFERENCES performed_sets(id, session_id) ON DELETE RESTRICT
  );
  CREATE UNIQUE INDEX one_open_rest_per_session ON rest_intervals(session_id) WHERE ended_at IS NULL;
  CREATE TABLE rest_pauses (
    id TEXT PRIMARY KEY NOT NULL,
    rest_interval_id TEXT NOT NULL REFERENCES rest_intervals(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL, ended_at TEXT CHECK(ended_at IS NULL OR ended_at >= started_at)
  );
  CREATE UNIQUE INDEX one_open_pause ON rest_pauses(rest_interval_id) WHERE ended_at IS NULL;
  CREATE INDEX pauses_interval ON rest_pauses(rest_interval_id, started_at, id);
  CREATE TRIGGER preserve_original_targets BEFORE UPDATE OF original_targets ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Original session targets are immutable'); END;
  CREATE TRIGGER preserve_performed_targets BEFORE UPDATE ON session_sets
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.id)
    BEGIN SELECT RAISE(ABORT, 'Performed session targets are immutable'); END;
  CREATE TRIGGER preserve_performance BEFORE UPDATE OF session_id, session_set_id, sort_order, weight_kg, reps, rir, performed_at ON performed_sets
    BEGIN SELECT RAISE(ABORT, 'Performed values are immutable'); END;
`;

/** Keep every v3 record and the clock schema intact; execution choices are additive. */
const versionFour = `
  ALTER TABLE workout_sessions ADD COLUMN selected_exercise_id TEXT;
  ALTER TABLE session_exercises ADD COLUMN planned_order INTEGER NOT NULL DEFAULT 0 CHECK(typeof(planned_order) = 'integer' AND planned_order >= 0);
  UPDATE session_exercises SET planned_order = sort_order;

  CREATE TABLE session_exercise_replacements (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    from_exercise_id TEXT NOT NULL,
    to_exercise_id TEXT NOT NULL,
    active_set_id TEXT NOT NULL,
    remaining_set_count INTEGER NOT NULL CHECK(typeof(remaining_set_count) = 'integer' AND remaining_set_count > 0),
    changed_at TEXT NOT NULL,
    CHECK(from_exercise_id != to_exercise_id),
    UNIQUE(session_id, from_exercise_id),
    UNIQUE(session_id, to_exercise_id),
    FOREIGN KEY(from_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(to_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(active_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
  CREATE TABLE session_exercise_choices (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL,
    expected_set_id TEXT NOT NULL,
    chosen_at TEXT NOT NULL,
    FOREIGN KEY(exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(expected_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
  CREATE INDEX replacements_session ON session_exercise_replacements(session_id, changed_at, id);
  CREATE INDEX choices_session ON session_exercise_choices(session_id, chosen_at, id);
  CREATE INDEX completed_sessions ON workout_sessions(finished_at DESC, id) WHERE status = 'completed';
  CREATE TRIGGER selected_exercise_belongs_to_session BEFORE UPDATE OF selected_exercise_id ON workout_sessions
    WHEN NEW.selected_exercise_id IS NOT NULL AND NOT EXISTS
      (SELECT 1 FROM session_exercises WHERE id = NEW.selected_exercise_id AND session_id = NEW.id)
    BEGIN SELECT RAISE(ABORT, 'Selected exercise belongs to another session'); END;
  CREATE TRIGGER preserve_execution_exercise BEFORE UPDATE ON session_exercises
    BEGIN SELECT RAISE(ABORT, 'Execution exercise identity is immutable'); END;
`;

const versionFive = `
  CREATE TABLE app_preferences (
    key TEXT PRIMARY KEY NOT NULL CHECK(length(key) BETWEEN 1 AND 80),
    value_json TEXT NOT NULL CHECK(json_valid(value_json)),
    updated_at TEXT NOT NULL
  );
`;

const versionSix = `
  CREATE TABLE set_load_rules (
    set_template_id TEXT PRIMARY KEY NOT NULL REFERENCES set_templates(id) ON DELETE CASCADE,
    reference_set_id TEXT REFERENCES set_templates(id) ON DELETE SET NULL,
    percent REAL NOT NULL CHECK(typeof(percent) IN ('real', 'integer') AND percent > 0 AND percent <= 100),
    basis TEXT NOT NULL DEFAULT 'planned_target' CHECK(basis = 'planned_target')
  );
  CREATE INDEX load_rules_reference ON set_load_rules(reference_set_id);
  CREATE TRIGGER validate_load_rule_insert BEFORE INSERT ON set_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup', 'back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work', 'top_set', 'custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid planned load reference'); END;
  CREATE TRIGGER validate_load_rule_update BEFORE UPDATE ON set_load_rules
  WHEN NEW.set_template_id != OLD.set_template_id OR NEW.basis != 'planned_target'
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work', 'top_set', 'custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid planned load reference'); END;
  CREATE TRIGGER preserve_load_reference BEFORE UPDATE OF kind, workout_exercise_id ON set_templates
  WHEN EXISTS (SELECT 1 FROM set_load_rules r JOIN set_templates dependent ON dependent.id = r.set_template_id
    WHERE r.reference_set_id = OLD.id AND (NEW.workout_exercise_id != dependent.workout_exercise_id
      OR NEW.kind NOT IN ('work', 'top_set', 'custom') OR (dependent.kind = 'back_off' AND NEW.kind != 'top_set')))
    OR EXISTS (SELECT 1 FROM set_load_rules r WHERE r.set_template_id = OLD.id
      AND (NEW.kind != OLD.kind OR NEW.workout_exercise_id != OLD.workout_exercise_id))
  BEGIN SELECT RAISE(ABORT, 'Remove dependent load rules before changing this reference'); END;
  CREATE TRIGGER calculated_weight_is_derived BEFORE UPDATE OF target_weight_kg ON set_templates
  WHEN NEW.target_weight_kg IS NOT NULL AND EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = NEW.id)
  BEGIN SELECT RAISE(ABORT, 'Calculated weight must remain derived'); END;
  ALTER TABLE session_sets ADD COLUMN load_rule_snapshot TEXT CHECK(load_rule_snapshot IS NULL OR json_valid(load_rule_snapshot));
  CREATE TRIGGER preserve_load_rule_snapshot BEFORE UPDATE OF load_rule_snapshot ON session_sets
  BEGIN SELECT RAISE(ABORT, 'Original load rule snapshot is immutable'); END;
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
      if (currentVersion < 3) await db.execAsync(versionThree);
      if (currentVersion < 4) await db.execAsync(versionFour);
      if (currentVersion < 5) await db.execAsync(versionFive);
      if (currentVersion < 6) await db.execAsync(versionSix);
      await db.execAsync(`PRAGMA user_version = ${DATABASE_VERSION};`);
    });
  }
}
