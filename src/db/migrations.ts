import type { Database } from './types';

export const DATABASE_VERSION = 1;

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

/** No demo content: a new database contains no programs or workout templates. */
export async function initializeDatabase(db: Database): Promise<void> {
  // Foreign keys must be enabled before a transaction, on every connection.
  await db.execAsync('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;');
  const version = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
  const currentVersion = version?.user_version ?? 0;

  if (currentVersion > DATABASE_VERSION) {
    throw new Error('Cette base utilise une version plus récente. Mettez l’application à jour.');
  }

  if (currentVersion < 1) {
    await db.withTransactionAsync(async () => {
      await db.execAsync(versionOne);
      await db.execAsync('PRAGMA user_version = 1;');
    });
  }
}
