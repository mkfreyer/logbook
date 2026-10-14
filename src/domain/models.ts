/** A user-created program. Completed training sessions will have separate models. */
export interface Program {
  id: string;
  name: string;
  description: string;
  sportType: 'musculation';
  createdAt: string;
  updatedAt: string;
  workoutCount: number;
}

/** An editable plan, never a record of a completed workout. */
export interface WorkoutTemplate {
  id: string;
  programId: string;
  name: string;
  notes: string;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProgramInput {
  name: string;
  description?: string;
}

export interface WorkoutInput {
  name: string;
  notes?: string;
}
