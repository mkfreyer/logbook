import type { Database } from '../db/types';
import { DATABASE_VERSION } from '../db/migrations';
import { DEFAULT_PREFERENCES } from '../domain/preferences';
import { DEFAULT_SERIES_DISPLAY } from '../domain/series';

export const PERSONAL_EXPORT_FORMAT = 'logbook.personal-data';
export const PERSONAL_EXPORT_VERSION = 1;
export const EXPORT_PAGE_SIZE = 256;
export const EXPORT_TABLES = [
  ['programs', 'id'], ['workout_templates', 'id'], ['exercise_catalog', 'id'],
  ['workout_exercises', 'id'], ['set_templates', 'id'], ['workout_sessions', 'id'],
  ['session_exercises', 'id'], ['session_sets', 'id'], ['performed_sets', 'id'],
  ['rest_intervals', 'id'], ['rest_pauses', 'id'], ['session_exercise_replacements', 'id'],
  ['session_exercise_choices', 'id'], ['app_preferences', 'key'],
  ['set_load_rules', 'set_template_id'],
] as const;
export class PersonalExportError extends Error {
  constructor(readonly code: 'cancelled' | 'incompatible' | 'integrity' | 'unavailable' | 'busy' | 'io' | 'cleanup', message: string) {
    super(message); this.name = 'PersonalExportError';
  }
}
export function checkExportCancellation(signal?: AbortSignal) {
  if (signal?.aborted) throw new PersonalExportError('cancelled', 'Export annulé. Vos données sont conservées.');
}
function json(value: unknown) {
  return JSON.stringify(value, (_key, item: unknown) => {
    if (typeof item === 'number' && !Number.isFinite(item)) throw new PersonalExportError('integrity', 'Une valeur numérique ne peut pas être exportée fidèlement.');
    return item;
  });
}

/** The caller MUST supply a dedicated connection, never the SQLiteProvider's.
 * A deferred read transaction pins one WAL snapshot across ALL tables and pages.
 * It does not reserve the write lock or join unrelated application writes. */
export async function writePersonalExport(db: Database, write: (text: string) => void | Promise<void>, options: {
  appVersion: string; createdAt?: string; signal?: AbortSignal; onProgress?(rows: number): void;
}) {
  checkExportCancellation(options.signal);
  await db.execAsync('PRAGMA query_only = ON; BEGIN DEFERRED TRANSACTION;');
  let committed = false, totalRows = 0;
  try {
    const tables = await db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT GLOB 'sqlite_*' ORDER BY name");
    const version = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
    if (version?.user_version !== DATABASE_VERSION || tables.length !== EXPORT_TABLES.length ||
      tables.some(table => !EXPORT_TABLES.some(([name]) => name === table.name))) {
      throw new PersonalExportError('incompatible', 'Cette version de la base ne peut pas être exportée par cette application. Mettez Logbook à jour.');
    }
    const integrity = await db.getAllAsync<{ quick_check: string }>('PRAGMA quick_check');
    if (integrity.length !== 1 || integrity[0]?.quick_check !== 'ok' || (await db.getAllAsync('PRAGMA foreign_key_check')).length) {
      throw new PersonalExportError('integrity', 'L’intégrité de la base ne permet pas un export fiable. Vos données restent conservées.');
    }
    checkExportCancellation(options.signal);
    const createdAt = options.createdAt ?? new Date().toISOString();
    if (!Number.isFinite(Date.parse(createdAt))) throw new PersonalExportError('integrity', 'La date de création de l’export est invalide.');
    const metadata = { format: PERSONAL_EXPORT_FORMAT, formatVersion: PERSONAL_EXPORT_VERSION,
      sqliteSchemaVersion: version.user_version, createdAt, application: { name: 'Logbook', version: options.appVersion },
      units: { weight: 'kg' }, preferenceDefaults: { ...DEFAULT_PREFERENCES, seriesDisplay: DEFAULT_SERIES_DISPLAY }, rowidField: '__rowid',
      conventions: { tonnage: 'recorded_kg_x_reps_including_warmups_no_doubling_no_bodyweight', duration: 'finished_at_minus_started_at_including_absences',
        restChronological: 'includes_pauses', restActive: 'excludes_pauses',
        plannedLoad: 'decimal_reference_target_x_percent_div_100_no_equipment_rounding_frozen_at_session_start' }, restorationAvailableInExporter: false };
    await write(json(metadata).slice(0, -1) + ',"tables":{');
    for (const [table, key] of EXPORT_TABLES) {
      checkExportCancellation(options.signal);
      const columns = (await db.getAllAsync<{ name: string }>(`PRAGMA table_info("${table}")`)).map(column => column.name);
      if (columns.includes('__rowid')) throw new PersonalExportError('incompatible', 'Cette structure de données nécessite une mise à jour de l’export.');
      const expected = (await db.getFirstAsync<{ count: number }>(`SELECT COUNT(*) AS count FROM "${table}"`))!.count;
      await write(`${table === EXPORT_TABLES[0][0] ? '' : ','}${json(table)}:{"columns":${json(columns)},"rows":[`);
      let cursor: number | null = null, count = 0;
      while (true) {
        checkExportCancellation(options.signal);
        const rows: Record<string, string | number | null>[] = cursor === null
          ? await db.getAllAsync(`SELECT rowid AS __rowid, * FROM "${table}" ORDER BY rowid LIMIT ?`, EXPORT_PAGE_SIZE)
          : await db.getAllAsync(`SELECT rowid AS __rowid, * FROM "${table}" WHERE rowid > ? ORDER BY rowid LIMIT ?`, cursor, EXPORT_PAGE_SIZE);
        if (!rows.length) break;
        const next = rows.at(-1)!.__rowid;
        if (typeof next !== 'number' || rows.some(row => !Number.isSafeInteger(row.__rowid) || typeof row[key] !== 'string')) {
          throw new PersonalExportError('integrity', 'Un identifiant ne peut pas être exporté fidèlement.');
        }
        await write(`${count ? ',' : ''}${json(rows).slice(1, -1)}`);
        count += rows.length; cursor = next; totalRows += rows.length;
        options.onProgress?.(totalRows);
        // Yield between bounded chunks for touch cancellation and native UI.
        await new Promise<void>(resolve => setTimeout(resolve, 0));
        if (rows.length < EXPORT_PAGE_SIZE) break;
      }
      if (count !== expected) throw new PersonalExportError('integrity', 'Le contenu de l’export est incomplet. Réessayez.');
      await write(`],"rowCount":${count}}`);
    }
    checkExportCancellation(options.signal);
    await write('}}');
    await db.execAsync('COMMIT;'); committed = true;
    return { totalRows, createdAt };
  } finally {
    if (!committed) await db.execAsync('ROLLBACK;');
  }
}
