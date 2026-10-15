import { beforeEach, expect, jest, test } from '@jest/globals';
import type { writePersonalExport } from '../src/data/personalExport';
import { checkExportCancellation, PersonalExportError } from '../src/data/personalExport';
import { cleanupPersonalExportCache, exportPersonalData } from '../src/data/exportPersonalData';

const mockFiles = new Map<string, string>(), mockDirectories = new Set<string>();
let mockDeleteFailure = false;
const mockWrite = jest.fn<typeof writePersonalExport>();
const mockClose = jest.fn<() => Promise<void>>(), mockOpen = jest.fn<(...args: unknown[]) => Promise<{ closeAsync: typeof mockClose }>>();
const mockAvailable = jest.fn<() => Promise<boolean>>(), mockShare = jest.fn<(...args: unknown[]) => Promise<void>>();
jest.mock('expo-crypto', () => ({ randomUUID: () => 'export-id' }));
jest.mock('expo-sqlite', () => ({ openDatabaseAsync: (...args: unknown[]) => mockOpen(...args) }));
jest.mock('expo-sharing', () => ({ isAvailableAsync: () => mockAvailable(), shareAsync: (...args: unknown[]) => mockShare(...args) }));
jest.mock('../src/data/personalExport', () => {
  const actual = jest.requireActual<typeof import('../src/data/personalExport')>('../src/data/personalExport');
  return { ...actual, writePersonalExport: (...args: Parameters<typeof writePersonalExport>) => mockWrite(...args) };
});
jest.mock('expo-file-system', () => {
  const path = (...parts: (string | { uri: string })[]) => parts.map(part => typeof part === 'string' ? part.replace(/\/$/, '') : part.uri).join('/');
  return { Paths: { cache: 'file:///cache' }, Directory: class {
    uri: string; constructor(...parts: (string | { uri: string })[]) { this.uri = path(...parts); }
    get exists() { return mockDirectories.has(this.uri); }
    create() { mockDirectories.add(this.uri); }
    delete() { for (const file of mockFiles.keys()) if (file.startsWith(this.uri + '/')) mockFiles.delete(file); mockDirectories.delete(this.uri); }
  }, File: class {
    uri: string; constructor(...parts: (string | { uri: string })[]) { this.uri = path(...parts); }
    get exists() { return mockFiles.has(this.uri); }
    create() { if (this.exists) throw new Error('exists'); mockFiles.set(this.uri, ''); }
    write(text: string, options: { append: boolean }) { mockFiles.set(this.uri, (options.append ? mockFiles.get(this.uri) ?? '' : '') + text); }
    async move(target: { uri: string }) { const text = mockFiles.get(this.uri)!; mockFiles.delete(this.uri); this.uri = target.uri; mockFiles.set(this.uri, text); }
    delete() { if (mockDeleteFailure) throw new Error('locked'); mockFiles.delete(this.uri); }
  } };
});
function deferred() { let resolve!: () => void; const promise = new Promise<void>(done => { resolve = done; }); return { promise, resolve }; }
beforeEach(() => {
  jest.clearAllMocks(); mockFiles.clear(); mockDirectories.clear(); mockDeleteFailure = false;
  mockClose.mockResolvedValue(undefined); mockOpen.mockResolvedValue({ closeAsync: mockClose }); mockAvailable.mockResolvedValue(true); mockShare.mockResolvedValue(undefined);
  mockWrite.mockImplementation(async (_db, write, options) => {
    await write('{"format":"logbook.personal-data","tables":{}}'); checkExportCancellation(options.signal);
    return { totalRows: 0, createdAt: '2026-10-15T12:00:00.000Z' };
  });
});

test('explicit export writes a temporary JSON, closes its dedicated reader before sharing, and cleans only its own files', async () => {
  const original = 'file:///Documents/mon-fichier.json'; mockFiles.set(original, 'original');
  mockShare.mockImplementation(async (uri, options) => {
    expect(String(uri)).toMatch(/logbook-personnel-.*\.json$/); expect(mockFiles.has(String(uri))).toBe(true);
    expect(options).toEqual(expect.objectContaining({ mimeType: 'application/json', UTI: 'public.json' }));
    expect(mockClose).toHaveBeenCalledTimes(1);
  });
  await exportPersonalData(); expect(mockOpen).toHaveBeenCalledWith('logbook.db', { useNewConnection: true });
  expect(mockWrite).toHaveBeenCalledTimes(1); expect(mockShare).toHaveBeenCalledTimes(1);
  expect([...mockFiles]).toEqual([[original, 'original']]);
});
test('no file is removed while the native share sheet is open; concurrent exports and cache cleanup cannot interfere', async () => {
  const pending = deferred(); mockShare.mockReturnValue(pending.promise);
  const job = exportPersonalData();
  // Let the asynchronous preparation reach the sheet.
  for (let i = 0; i < 12; i++) await Promise.resolve();
  expect(mockShare).toHaveBeenCalledTimes(1); expect(mockFiles.size).toBe(1);
  cleanupPersonalExportCache(); expect(mockFiles.size).toBe(1);
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'busy' });
  pending.resolve(); await job; expect(mockFiles.size).toBe(0);
});
test('unsupported sharing creates no file and performs no database read', async () => {
  mockAvailable.mockResolvedValue(false);
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'unavailable' });
  expect(mockOpen).not.toHaveBeenCalled(); expect(mockFiles.size).toBe(0); expect(mockShare).not.toHaveBeenCalled();
});
test('cancel before or during preparation never opens the share sheet and releases files/connections', async () => {
  const controller = new AbortController(); controller.abort();
  await expect(exportPersonalData({ signal: controller.signal })).rejects.toMatchObject({ code: 'cancelled' });
  expect(mockOpen).not.toHaveBeenCalled();
  const second = new AbortController(); mockWrite.mockImplementation(async () => { second.abort(); checkExportCancellation(second.signal); throw new Error('unreachable'); });
  await expect(exportPersonalData({ signal: second.signal })).rejects.toMatchObject({ code: 'cancelled' });
  expect(mockShare).not.toHaveBeenCalled(); expect(mockClose).toHaveBeenCalledTimes(1); expect(mockFiles.size).toBe(0);
});
test('failed reading/writing never exposes a partial file or alters source data', async () => {
  mockWrite.mockRejectedValueOnce(new Error('disk full / private/path'));
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'io', message: expect.not.stringContaining('private/path') });
  expect(mockClose).toHaveBeenCalledTimes(1); expect(mockFiles.size).toBe(0); expect(mockShare).not.toHaveBeenCalled();
});
test('share failure cleans the prepared file and a cancelled native sheet resolves without claiming a saved copy', async () => {
  mockShare.mockRejectedValueOnce(new Error('extension failed'));
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'io' }); expect(mockFiles.size).toBe(0);
  mockShare.mockResolvedValue(undefined); expect(await exportPersonalData()).toBeUndefined(); expect(mockFiles.size).toBe(0);
});
test('integrity errors remain meaningful and temporary cleanup failures are reported, then recoverable', async () => {
  mockWrite.mockRejectedValueOnce(new PersonalExportError('integrity', 'Intégrité invalide.'));
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'integrity', message: 'Intégrité invalide.' });
  mockDeleteFailure = true;
  await expect(exportPersonalData()).rejects.toMatchObject({ code: 'cleanup' }); expect(mockFiles.size).toBe(1);
  mockDeleteFailure = false; cleanupPersonalExportCache(); expect(mockFiles.size).toBe(0);
});
