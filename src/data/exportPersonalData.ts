import { randomUUID } from 'expo-crypto';
import { Directory, File, Paths } from 'expo-file-system';
import { isAvailableAsync, shareAsync } from 'expo-sharing';
import { openDatabaseAsync, type SQLiteDatabase } from 'expo-sqlite';
import appConfig from '../../app.json';
import { checkExportCancellation, PersonalExportError, writePersonalExport } from './personalExport';

let exporting = false;
const exportDirectory = () => new Directory(Paths.cache, 'logbook-personal-exports');

/** Only our own temporary directory, never SQLite or the user's saved copies. */
export function cleanupPersonalExportCache() {
  if (exporting) return;
  const directory = exportDirectory();
  if (directory.exists) directory.delete();
}

/** Sharing only occurs after an explicit user action; no URL/network destination.
 * The native sheet doesn't report whether the user saved or cancelled. */
export async function exportPersonalData(options: {
  signal?: AbortSignal; onProgress?(rows: number): void; onPhase?(phase: 'preparing' | 'sharing'): void;
} = {}) {
  if (exporting) throw new PersonalExportError('busy', 'Un export est déjà en cours. Attendez sa fermeture.');
  exporting = true;
  let db: SQLiteDatabase | undefined, draft: File | undefined, ready: File | undefined, failure: unknown;
  try {
    checkExportCancellation(options.signal);
    if (!await isAvailableAsync()) throw new PersonalExportError('unavailable', 'L’enregistrement par la feuille de partage n’est pas disponible sur cet appareil.');
    const directory = exportDirectory();
    if (directory.exists) directory.delete();
    directory.create({ intermediates: true });
    const name = `logbook-personnel-${new Date().toISOString().replace(/[:.]/g, '-')}-${randomUUID()}`;
    draft = new File(directory, `${name}.json.part`); ready = new File(directory, `${name}.json`);
    draft.create();
    options.onPhase?.('preparing');
    db = await openDatabaseAsync('logbook.db', { useNewConnection: true });
    const file = draft;
    await writePersonalExport(db, text => file.write(text, { append: true }), {
      appVersion: appConfig.expo.version, signal: options.signal, onProgress: options.onProgress,
    });
    await db.closeAsync(); db = undefined;
    checkExportCancellation(options.signal);
    await draft.move(ready);
    checkExportCancellation(options.signal);
    options.onPhase?.('sharing');
    await shareAsync(ready.uri, { mimeType: 'application/json', UTI: 'public.json', dialogTitle: 'Enregistrer mon export Logbook' });
  } catch (error) {
    failure = error instanceof PersonalExportError ? error : new PersonalExportError('io', 'Impossible de préparer ou d’enregistrer l’export. Vos données n’ont pas été modifiées. Réessayez.');
  } finally {
    try { await db?.closeAsync(); } catch { failure ??= new PersonalExportError('cleanup', 'La connexion d’export n’a pas pu être fermée correctement. Fermez puis rouvrez Logbook.'); }
    try {
      if (draft?.exists) draft.delete();
      if (ready?.exists) ready.delete();
    } catch { failure = new PersonalExportError('cleanup', 'Le fichier temporaire n’a pas pu être nettoyé. Rouvrez les paramètres pour réessayer le nettoyage.'); }
    exporting = false;
  }
  if (failure) throw failure;
}
