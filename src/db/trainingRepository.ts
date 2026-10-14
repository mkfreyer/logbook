import type {
  CatalogExerciseInput, ExerciseCatalogItem, SetKind, SetTemplate, SetTemplateInput,
  WeightMode, WorkoutExercise, WorkoutExerciseInput,
} from '../domain/training';
import type { Database } from './types';

export class TrainingValidationError extends Error {
  constructor(public readonly field: string, message: string) {
    super(message); this.name = 'TrainingValidationError';
  }
}

export class TrainingNotFoundError extends Error {
  constructor(public readonly entity: 'catalog' | 'workout' | 'exercise' | 'set') {
    const messages = { catalog: 'Cet exercice est introuvable.', workout: 'Cette séance est introuvable.', exercise: 'Cet exercice prévu est introuvable.', set: 'Cette série est introuvable.' };
    super(messages[entity]); this.name = 'TrainingNotFoundError';
  }
}

const catalogColumns = `id, name, muscle_group AS muscleGroup, equipment, instructions,
  weight_mode AS weightMode, is_custom AS isCustom, created_at AS createdAt, updated_at AS updatedAt`;
const setColumns = `id, workout_exercise_id AS workoutExerciseId, sort_order AS sortOrder,
  label, kind, reps_min AS repsMin, reps_max AS repsMax, target_weight_kg AS targetWeightKg,
  target_rir AS targetRir, rest_after_sec AS restAfterSec, notes, created_at AS createdAt, updated_at AS updatedAt`;
const occurrenceColumns = `w.id, w.workout_template_id AS workoutTemplateId, w.exercise_id AS exerciseId,
  w.sort_order AS sortOrder, w.notes, w.created_at AS createdAt, w.updated_at AS updatedAt,
  e.name AS exerciseName, e.muscle_group AS muscleGroup, e.equipment, e.instructions,
  e.weight_mode AS weightMode, e.is_custom AS isCustom, e.created_at AS exerciseCreatedAt,
  e.updated_at AS exerciseUpdatedAt`;

type CatalogRow = Omit<ExerciseCatalogItem, 'isCustom'> & { isCustom: number };
type OccurrenceRow = Omit<WorkoutExercise, 'exercise'> & {
  exerciseName: string; muscleGroup: string; equipment: string; instructions: string;
  weightMode: WeightMode; isCustom: number; exerciseCreatedAt: string; exerciseUpdatedAt: string;
};

function catalogFrom(row: CatalogRow): ExerciseCatalogItem { return { ...row, isCustom: Boolean(row.isCustom) }; }
function occurrenceFrom(row: OccurrenceRow): WorkoutExercise {
  return {
    id: row.id, workoutTemplateId: row.workoutTemplateId, exerciseId: row.exerciseId,
    sortOrder: row.sortOrder, notes: row.notes, createdAt: row.createdAt, updatedAt: row.updatedAt,
    exercise: { id: row.exerciseId, name: row.exerciseName, muscleGroup: row.muscleGroup,
      equipment: row.equipment, instructions: row.instructions, weightMode: row.weightMode,
      isCustom: Boolean(row.isCustom), createdAt: row.exerciseCreatedAt, updatedAt: row.exerciseUpdatedAt },
  };
}

function text(value: unknown, field: string, max: number, required = false): string {
  const clean = value === undefined && !required ? '' : typeof value === 'string' ? value.trim() : null;
  if (clean === null || (required && !clean) || clean.length > max) {
    throw new TrainingValidationError(field, required
      ? `Renseignez ce champ (1 à ${max} caractères).`
      : `Ce texte doit contenir au maximum ${max} caractères.`);
  }
  return clean;
}

function integer(value: unknown, field: string, max = Number.MAX_SAFE_INTEGER): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0 || value > max) {
    throw new TrainingValidationError(field, `Indiquez un nombre entier entre 0 et ${max}.`);
  }
  return value;
}

function cleanCatalog(input: CatalogExerciseInput) {
  const weightMode = input.weightMode;
  if (!['total', 'per_hand', 'additional'].includes(weightMode)) {
    throw new TrainingValidationError('weightMode', 'Choisissez la manière de renseigner la charge.');
  }
  return { name: text(input.name, 'name', 80, true), muscleGroup: text(input.muscleGroup, 'muscleGroup', 80, true),
    equipment: text(input.equipment, 'equipment', 80, true), instructions: text(input.instructions, 'instructions', 1000), weightMode };
}

function cleanSet(input: SetTemplateInput) {
  const kind: SetKind = input.kind;
  if (!['work', 'warmup', 'top_set', 'back_off', 'custom'].includes(kind)) {
    throw new TrainingValidationError('kind', 'Choisissez un type de série.');
  }
  const repsMin = integer(input.repsMin, 'repsMin');
  const repsMax = integer(input.repsMax, 'repsMax');
  if (repsMax < repsMin) throw new TrainingValidationError('repsMax', 'Le maximum doit être supérieur ou égal au minimum.');
  const targetWeightKg = input.targetWeightKg ?? null;
  if (targetWeightKg !== null && (typeof targetWeightKg !== 'number' || !Number.isFinite(targetWeightKg) || targetWeightKg < 0)) {
    throw new TrainingValidationError('targetWeightKg', 'Indiquez une charge positive ou nulle, ou laissez ce champ vide.');
  }
  const targetRir = input.targetRir == null ? null : integer(input.targetRir, 'targetRir', 10);
  return { label: text(input.label, 'label', 80), kind, repsMin, repsMax, targetWeightKg, targetRir,
    restAfterSec: integer(input.restAfterSec, 'restAfterSec', 86400), notes: text(input.notes, 'notes', 1000) };
}

const searchable = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr').trim();

/** Only programmable targets live here. Performed values in M1.2 must be separate
 * snapshots, never mutable aliases or cascading children of these preparations. */
export class TrainingRepository {
  private pendingWrite: Promise<void> = Promise.resolve();

  constructor(private readonly db: Database, private readonly idFactory: () => string,
    private readonly now: () => string = () => new Date().toISOString()) {}

  private write<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.pendingWrite.then(operation);
    this.pendingWrite = result.then(() => undefined, () => undefined);
    return result;
  }

  /** Exclusive Expo transactions open a fresh connection. This helper is reserved
   * for order/timestamp updates, with no foreign-key changes or cascading deletes. */
  private async reorderTransaction(task: (db: Database) => Promise<void>): Promise<void> {
    if (this.db.withExclusiveTransactionAsync) await this.db.withExclusiveTransactionAsync(task);
    else await this.db.withTransactionAsync(() => task(this.db));
  }

  private async requireWorkout(id: string, db = this.db): Promise<void> {
    if (!await db.getFirstAsync('SELECT id FROM workout_templates WHERE id = ?', id)) throw new TrainingNotFoundError('workout');
  }

  async listCatalog(search = ''): Promise<ExerciseCatalogItem[]> {
    const rows = await this.db.getAllAsync<CatalogRow>(`SELECT ${catalogColumns} FROM exercise_catalog`);
    const terms = searchable(search).split(/\s+/).filter(Boolean);
    return rows.map(catalogFrom).filter(item => {
      const haystack = searchable(`${item.name} ${item.muscleGroup} ${item.equipment}`);
      return terms.every(term => haystack.includes(term));
    }).sort((a, b) => a.name.localeCompare(b.name, 'fr') || a.id.localeCompare(b.id));
  }

  async getCatalogExercise(id: string): Promise<ExerciseCatalogItem> {
    const row = await this.db.getFirstAsync<CatalogRow>(`SELECT ${catalogColumns} FROM exercise_catalog WHERE id = ?`, id);
    if (!row) throw new TrainingNotFoundError('catalog');
    return catalogFrom(row);
  }

  createCustomExercise(input: CatalogExerciseInput): Promise<ExerciseCatalogItem> {
    return this.write(async () => {
      const clean = cleanCatalog(input), id = this.idFactory(), stamp = this.now();
      await this.db.runAsync(`INSERT INTO exercise_catalog
        (id, name, muscle_group, equipment, instructions, weight_mode, is_custom, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)`,
      id, clean.name, clean.muscleGroup, clean.equipment, clean.instructions, clean.weightMode, stamp, stamp);
      return this.getCatalogExercise(id);
    });
  }

  updateCustomExercise(id: string, input: CatalogExerciseInput): Promise<ExerciseCatalogItem> {
    return this.write(async () => {
      const clean = cleanCatalog(input), previous = await this.getCatalogExercise(id);
      if (!previous.isCustom) throw new TrainingValidationError('id', 'Seuls vos exercices personnalisés peuvent être modifiés.');
      const result = await this.db.runAsync(`UPDATE exercise_catalog SET name = ?, muscle_group = ?, equipment = ?,
        instructions = ?, weight_mode = ?, updated_at = ? WHERE id = ? AND is_custom = 1`,
      clean.name, clean.muscleGroup, clean.equipment, clean.instructions, clean.weightMode, this.now(), id);
      if (!result.changes) throw new TrainingNotFoundError('catalog');
      return this.getCatalogExercise(id);
    });
  }

  async getWorkoutExercise(id: string): Promise<WorkoutExercise> {
    const row = await this.db.getFirstAsync<OccurrenceRow>(`SELECT ${occurrenceColumns}
      FROM workout_exercises w JOIN exercise_catalog e ON e.id = w.exercise_id WHERE w.id = ?`, id);
    if (!row) throw new TrainingNotFoundError('exercise');
    return occurrenceFrom(row);
  }

  async listWorkoutExercises(workoutId: string): Promise<WorkoutExercise[]> {
    await this.requireWorkout(workoutId);
    const rows = await this.db.getAllAsync<OccurrenceRow>(`SELECT ${occurrenceColumns}
      FROM workout_exercises w JOIN exercise_catalog e ON e.id = w.exercise_id
      WHERE w.workout_template_id = ? ORDER BY w.sort_order, w.id`, workoutId);
    return rows.map(occurrenceFrom);
  }

  addWorkoutExercise(workoutId: string, input: WorkoutExerciseInput): Promise<WorkoutExercise> {
    return this.write(async () => {
      const notes = text(input.notes, 'notes', 1000);
      await this.requireWorkout(workoutId); await this.getCatalogExercise(input.exerciseId);
      const id = this.idFactory(), stamp = this.now();
      await this.db.runAsync(`INSERT INTO workout_exercises
        (id, workout_template_id, exercise_id, sort_order, notes, created_at, updated_at)
        SELECT ?, ?, ?, COALESCE(MAX(sort_order), -1) + 1, ?, ?, ? FROM workout_exercises WHERE workout_template_id = ?`,
      id, workoutId, input.exerciseId, notes, stamp, stamp, workoutId);
      return this.getWorkoutExercise(id);
    });
  }

  updateWorkoutExercise(id: string, input: WorkoutExerciseInput): Promise<WorkoutExercise> {
    return this.write(async () => {
      const notes = text(input.notes, 'notes', 1000);
      await this.getCatalogExercise(input.exerciseId);
      const result = await this.db.runAsync('UPDATE workout_exercises SET exercise_id = ?, notes = ?, updated_at = ? WHERE id = ?',
        input.exerciseId, notes, this.now(), id);
      if (!result.changes) throw new TrainingNotFoundError('exercise');
      return this.getWorkoutExercise(id);
    });
  }

  deleteWorkoutExercise(id: string): Promise<void> {
    return this.write(async () => {
      const result = await this.db.runAsync('DELETE FROM workout_exercises WHERE id = ?', id);
      if (!result.changes) throw new TrainingNotFoundError('exercise');
    });
  }

  async getSet(id: string): Promise<SetTemplate> {
    const row = await this.db.getFirstAsync<SetTemplate>(`SELECT ${setColumns} FROM set_templates WHERE id = ?`, id);
    if (!row) throw new TrainingNotFoundError('set');
    return row;
  }

  async listSets(workoutExerciseId: string): Promise<SetTemplate[]> {
    await this.getWorkoutExercise(workoutExerciseId);
    return this.db.getAllAsync<SetTemplate>(`SELECT ${setColumns} FROM set_templates
      WHERE workout_exercise_id = ? ORDER BY sort_order, id`, workoutExerciseId);
  }

  createSet(workoutExerciseId: string, input: SetTemplateInput): Promise<SetTemplate> {
    return this.write(async () => {
      const clean = cleanSet(input);
      await this.getWorkoutExercise(workoutExerciseId);
      const id = this.idFactory(), stamp = this.now();
      await this.db.runAsync(`INSERT INTO set_templates
        (id, workout_exercise_id, sort_order, label, kind, reps_min, reps_max, target_weight_kg,
         target_rir, rest_after_sec, notes, created_at, updated_at)
        SELECT ?, ?, COALESCE(MAX(sort_order), -1) + 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        FROM set_templates WHERE workout_exercise_id = ?`, id, workoutExerciseId, clean.label, clean.kind,
      clean.repsMin, clean.repsMax, clean.targetWeightKg, clean.targetRir, clean.restAfterSec, clean.notes, stamp, stamp, workoutExerciseId);
      return this.getSet(id);
    });
  }

  updateSet(id: string, input: SetTemplateInput): Promise<SetTemplate> {
    return this.write(async () => {
      const clean = cleanSet(input);
      const result = await this.db.runAsync(`UPDATE set_templates SET label = ?, kind = ?, reps_min = ?, reps_max = ?,
        target_weight_kg = ?, target_rir = ?, rest_after_sec = ?, notes = ?, updated_at = ? WHERE id = ?`,
      clean.label, clean.kind, clean.repsMin, clean.repsMax, clean.targetWeightKg, clean.targetRir,
      clean.restAfterSec, clean.notes, this.now(), id);
      if (!result.changes) throw new TrainingNotFoundError('set');
      return this.getSet(id);
    });
  }

  deleteSet(id: string): Promise<void> {
    return this.write(async () => {
      const result = await this.db.runAsync('DELETE FROM set_templates WHERE id = ?', id);
      if (!result.changes) throw new TrainingNotFoundError('set');
    });
  }

  reorderWorkoutExercises(workoutId: string, orderedIds: string[]): Promise<void> {
    return this.reorder('workout_exercises', 'workout_template_id', workoutId, orderedIds);
  }

  reorderSets(workoutExerciseId: string, orderedIds: string[]): Promise<void> {
    return this.reorder('set_templates', 'workout_exercise_id', workoutExerciseId, orderedIds);
  }

  /** A full parent-scoped permutation: moving records across parents is forbidden.
   * Temporary positions above the current maximum avoid UNIQUE collisions; any
   * failed update rolls back all positions, including the temporary shift. */
  private reorder(table: 'workout_exercises' | 'set_templates', parentColumn: 'workout_template_id' | 'workout_exercise_id', parentId: string, orderedIds: string[]): Promise<void> {
    return this.write(async () => {
      await this.reorderTransaction(async db => {
        if (table === 'workout_exercises') await this.requireWorkout(parentId, db);
        else if (!await db.getFirstAsync('SELECT id FROM workout_exercises WHERE id = ?', parentId)) throw new TrainingNotFoundError('exercise');
        const current = await db.getAllAsync<{ id: string; sortOrder: number }>(`SELECT id, sort_order AS sortOrder FROM ${table} WHERE ${parentColumn} = ?`, parentId);
        if (!Array.isArray(orderedIds) || orderedIds.some(id => typeof id !== 'string') || orderedIds.length !== current.length ||
          new Set(orderedIds).size !== current.length || current.some(item => !orderedIds.includes(item.id))) {
          throw new TrainingValidationError('order', 'L’ordre doit contenir chaque élément de cette liste, une seule fois. Actualisez puis réessayez.');
        }
        if (!current.length) return;
        const shift = Math.max(...current.map(item => item.sortOrder)) + current.length + 1;
        if (!Number.isSafeInteger(shift + Math.max(...current.map(item => item.sortOrder)))) {
          throw new TrainingValidationError('order', 'Impossible de réorganiser cette liste.');
        }
        await db.runAsync(`UPDATE ${table} SET sort_order = sort_order + ? WHERE ${parentColumn} = ?`, shift, parentId);
        const stamp = this.now();
        for (const [position, id] of orderedIds.entries()) {
          await db.runAsync(`UPDATE ${table} SET sort_order = ?, updated_at = ? WHERE id = ? AND ${parentColumn} = ?`, position, stamp, id, parentId);
        }
      });
    });
  }
}
