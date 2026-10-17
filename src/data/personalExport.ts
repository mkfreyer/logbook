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
  ['set_load_rules', 'set_template_id'], ['set_actual_load_rules', 'set_template_id'],
  ['session_set_load_rules', 'session_set_id'], ['session_set_adjustments', 'id'], ['session_personal_notes', 'id'], ['session_set_passages', 'id'],
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
    // Provenance IDs of deleted templates remain valid history, not foreign keys.
    // Check the new live-rule semantics without requiring those deleted models.
    const invalidRule = await db.getFirstAsync(`SELECT r.session_set_id FROM session_set_load_rules r
      JOIN session_sets s ON s.id = r.session_set_id JOIN session_sets ref ON ref.id = r.reference_set_id
      JOIN session_exercises e ON e.id = s.session_exercise_id
      WHERE r.suspended = 0 AND s.removed_at IS NULL
      AND NOT EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = s.id)
      AND (s.session_id != r.session_id OR ref.session_id != r.session_id OR s.session_exercise_id != ref.session_exercise_id
        OR e.weight_mode != r.weight_mode OR ref.removed_at IS NOT NULL) LIMIT 1`);
    const duplicateRule = await db.getFirstAsync('SELECT p.set_template_id FROM set_load_rules p JOIN set_actual_load_rules a USING(set_template_id) LIMIT 1');
    const invalidAddition = await db.getFirstAsync(`SELECT id FROM session_sets WHERE addition_key IS NOT NULL
      AND (added_at IS NULL OR addition_scope IS NULL OR initial_metadata IS NULL OR (addition_scope = 'program' AND source_set_template_id IS NULL)) LIMIT 1`);
    if (invalidRule || duplicateRule || invalidAddition) throw new PersonalExportError('integrity', 'Une relation de série est incohérente. Export interrompu ; les données sont conservées.');
    const invalidPassage = await db.getFirstAsync(`WITH ordered AS (
      SELECT *, ROW_NUMBER() OVER(PARTITION BY session_set_id ORDER BY revision) AS expected_revision,
        LAG(action) OVER(PARTITION BY session_set_id ORDER BY revision) AS previous_action,
        LAG(changed_at) OVER(PARTITION BY session_set_id ORDER BY revision) AS previous_at
      FROM session_set_passages)
      SELECT id FROM ordered WHERE revision != expected_revision
        OR (previous_action IS NULL AND action != 'skip') OR previous_action = action OR changed_at < previous_at LIMIT 1`);
    const invalidSkipped = await db.getFirstAsync(`SELECT p.id FROM session_set_passages p JOIN session_sets s ON s.id = p.session_set_id
      WHERE p.action = 'skip' AND p.revision = (SELECT MAX(revision) FROM session_set_passages WHERE session_set_id = p.session_set_id)
      AND (s.removed_at IS NOT NULL OR EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = p.session_set_id)) LIMIT 1`);
    if (invalidPassage || invalidSkipped) throw new PersonalExportError('integrity', 'Le statut d’une série est incohérent. Export interrompu ; les données sont conservées.');
    checkExportCancellation(options.signal);
    const createdAt = options.createdAt ?? new Date().toISOString();
    if (!Number.isFinite(Date.parse(createdAt))) throw new PersonalExportError('integrity', 'La date de création de l’export est invalide.');
    const metadata = { format: PERSONAL_EXPORT_FORMAT, formatVersion: PERSONAL_EXPORT_VERSION,
      sqliteSchemaVersion: version.user_version, createdAt, application: { name: 'Logbook', version: options.appVersion },
      units: { weight: 'kg' }, preferenceDefaults: { ...DEFAULT_PREFERENCES, seriesDisplay: DEFAULT_SERIES_DISPLAY }, rowidField: '__rowid',
      conventions: { tonnage: 'recorded_kg_x_reps_including_warmups_no_doubling_no_bodyweight', duration: 'finished_at_minus_started_at_including_absences',
        restChronological: 'includes_pauses', restActive: 'excludes_pauses',
        plannedLoad: 'decimal_reference_target_x_percent_div_100_no_equipment_rounding_frozen_at_session_start',
        performedLoad: 'validated_reference_weight_x_percent_div_100_proposed_target_only',
        sessionAdjustments: 'append_only_original_snapshots_preserved', removedSeries: 'soft_deleted_unperformed_additions_only', skippedSeries: 'latest_passage_revision_is_not_a_performance' }, restorationAvailableInExporter: false };
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
