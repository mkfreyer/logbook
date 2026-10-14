import type { Program, ProgramInput, WorkoutInput, WorkoutTemplate } from '../domain/models';
import type { Database } from './types';

export class ValidationError extends Error {
  constructor(public readonly field: 'name' | 'description' | 'notes', message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends Error {
  constructor(public readonly entity: 'program' | 'workout') {
    super(entity === 'program' ? 'Ce programme est introuvable.' : 'Cette séance est introuvable.');
    this.name = 'NotFoundError';
  }
}

const programColumns = `
  p.id, p.name, p.description, p.sport_type AS sportType,
  p.created_at AS createdAt, p.updated_at AS updatedAt,
  (SELECT COUNT(*) FROM workout_templates w WHERE w.program_id = p.id) AS workoutCount
`;

const workoutColumns = `
  id, program_id AS programId, name, notes, sort_order AS sortOrder,
  created_at AS createdAt, updated_at AS updatedAt
`;

function cleanName(value: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new ValidationError('name', 'Donnez un nom à votre programme ou à votre séance.');
  }
  const cleaned = value.trim();
  if (cleaned.length > 80) {
    throw new ValidationError('name', 'Le nom doit contenir au maximum 80 caractères.');
  }
  return cleaned;
}

function cleanOptionalText(value: string | undefined, field: 'description' | 'notes'): string {
  const cleaned = value === undefined ? '' : typeof value === 'string' ? value.trim() : null;
  if (cleaned === null || cleaned.length > 1000) {
    throw new ValidationError(field, 'Ce texte doit contenir au maximum 1 000 caractères.');
  }
  return cleaned;
}

export class ProgramRepository {
  constructor(
    private readonly db: Database,
    private readonly idFactory: () => string,
    private readonly now: () => string = () => new Date().toISOString(),
  ) {}

  listPrograms(): Promise<Program[]> {
    return this.db.getAllAsync<Program>(
      `SELECT ${programColumns} FROM programs p ORDER BY p.updated_at DESC, p.created_at DESC, p.id ASC`,
    );
  }

  async getProgram(id: string): Promise<Program> {
    const program = await this.db.getFirstAsync<Program>(
      `SELECT ${programColumns} FROM programs p WHERE p.id = ?`,
      id,
    );
    if (!program) throw new NotFoundError('program');
    return program;
  }

  async createProgram(input: ProgramInput): Promise<Program> {
    const name = cleanName(input.name);
    const description = cleanOptionalText(input.description, 'description');
    const id = this.idFactory();
    const timestamp = this.now();
    await this.db.runAsync(
      `INSERT INTO programs (id, name, description, sport_type, created_at, updated_at)
       VALUES (?, ?, ?, 'musculation', ?, ?)`,
      id,
      name,
      description,
      timestamp,
      timestamp,
    );
    return this.getProgram(id);
  }

  async updateProgram(id: string, input: ProgramInput): Promise<Program> {
    const name = cleanName(input.name);
    const description = cleanOptionalText(input.description, 'description');
    const result = await this.db.runAsync(
      'UPDATE programs SET name = ?, description = ?, updated_at = ? WHERE id = ?',
      name,
      description,
      this.now(),
      id,
    );
    if (!result.changes) throw new NotFoundError('program');
    return this.getProgram(id);
  }

  /** Delete preparation only. SQLite cascades to workout_templates atomically.
   * Future completed-session records must retain independent snapshots, without
   * a cascading foreign key to either preparation table. */
  async deleteProgram(id: string): Promise<void> {
    const result = await this.db.runAsync('DELETE FROM programs WHERE id = ?', id);
    if (!result.changes) throw new NotFoundError('program');
  }

  async listWorkouts(programId: string): Promise<WorkoutTemplate[]> {
    await this.getProgram(programId);
    return this.db.getAllAsync<WorkoutTemplate>(
      `SELECT ${workoutColumns} FROM workout_templates
       WHERE program_id = ? ORDER BY sort_order ASC, created_at ASC, id ASC`,
      programId,
    );
  }

  async getWorkout(id: string): Promise<WorkoutTemplate> {
    const workout = await this.db.getFirstAsync<WorkoutTemplate>(
      `SELECT ${workoutColumns} FROM workout_templates WHERE id = ?`,
      id,
    );
    if (!workout) throw new NotFoundError('workout');
    return workout;
  }

  async createWorkout(programId: string, input: WorkoutInput): Promise<WorkoutTemplate> {
    const name = cleanName(input.name);
    const notes = cleanOptionalText(input.notes, 'notes');
    await this.getProgram(programId);
    const id = this.idFactory();
    const timestamp = this.now();
    // MAX and INSERT share one SQLite statement; simultaneous saves cannot reuse an order.
    await this.db.runAsync(
      `INSERT INTO workout_templates (id, program_id, name, notes, sort_order, created_at, updated_at)
       SELECT ?, ?, ?, ?, COALESCE(MAX(sort_order), -1) + 1, ?, ?
       FROM workout_templates WHERE program_id = ?`,
      id,
      programId,
      name,
      notes,
      timestamp,
      timestamp,
      programId,
    );
    return this.getWorkout(id);
  }

  async updateWorkout(id: string, input: WorkoutInput): Promise<WorkoutTemplate> {
    const name = cleanName(input.name);
    const notes = cleanOptionalText(input.notes, 'notes');
    const result = await this.db.runAsync(
      'UPDATE workout_templates SET name = ?, notes = ?, updated_at = ? WHERE id = ?',
      name,
      notes,
      this.now(),
      id,
    );
    if (!result.changes) throw new NotFoundError('workout');
    return this.getWorkout(id);
  }

  /** Do not renumber siblings: their identities, order and timestamps stay intact. */
  async deleteWorkout(id: string): Promise<void> {
    const result = await this.db.runAsync('DELETE FROM workout_templates WHERE id = ?', id);
    if (!result.changes) throw new NotFoundError('workout');
  }
}
