import type { Database } from './types';
import type { SetTemplate } from '../domain/training';
import { percentageWeight } from '../domain/series';

export const plannedSetColumns = `s.id, s.workout_exercise_id AS workoutExerciseId, s.sort_order AS sortOrder,
  s.label, s.kind, s.reps_min AS repsMin, s.reps_max AS repsMax, s.target_weight_kg AS targetWeightKg,
  s.target_rir AS targetRir, s.rest_after_sec AS restAfterSec, s.notes, s.created_at AS createdAt, s.updated_at AS updatedAt,
  r.set_template_id AS ruleId, r.reference_set_id AS referenceSetId, r.percent,
  ref.target_weight_kg AS referenceWeightKg`;
export const plannedSetJoins = `FROM set_templates s LEFT JOIN set_load_rules r ON r.set_template_id = s.id
  LEFT JOIN set_templates ref ON ref.id = r.reference_set_id`;
type Row = SetTemplate & { ruleId: string | null; referenceSetId: string | null; percent: number | null; referenceWeightKg: number | null };
export function plannedSetFrom({ ruleId, referenceSetId, percent, referenceWeightKg, ...row }: Row): SetTemplate {
  return { ...row, loadRule: ruleId ? { basis: 'planned_target', referenceSetId, percent: percent! } : null,
    targetWeightKg: ruleId ? percentageWeight(referenceWeightKg, percent!) : row.targetWeightKg };
}
export async function readPlannedSets(db: Database, exerciseId: string): Promise<SetTemplate[]> {
  const rows = await db.getAllAsync<Row>(`SELECT ${plannedSetColumns} ${plannedSetJoins}
    WHERE s.workout_exercise_id = ? ORDER BY s.sort_order, s.id`, exerciseId);
  return rows.map(plannedSetFrom);
}
export async function readPlannedSet(db: Database, id: string): Promise<SetTemplate | null> {
  const row = await db.getFirstAsync<Row>(`SELECT ${plannedSetColumns} ${plannedSetJoins} WHERE s.id = ?`, id);
  return row ? plannedSetFrom(row) : null;
}
