import type { Database } from './types';
import { DEFAULT_PREFERENCES, REST_SOUND_KEY, type Preferences } from '../domain/preferences';
import { DEFAULT_SERIES_DISPLAY, type SeriesDisplay } from '../domain/series';

export const SERIES_DISPLAY_KEY = 'series_display';

export class PreferencesRepository {
  private pending: Promise<void> = Promise.resolve();
  constructor(private readonly db: Database, private readonly now = () => new Date().toISOString()) {}
  async getPreferences(): Promise<Preferences> {
    await this.pending;
    const row = await this.db.getFirstAsync<{ value: string }>('SELECT value_json AS value FROM app_preferences WHERE key = ?', REST_SOUND_KEY);
    if (!row) return { ...DEFAULT_PREFERENCES };
    const value: unknown = JSON.parse(row.value);
    if (typeof value !== 'boolean') throw new Error('La préférence sonore ne peut pas être lue. Réessayez.');
    return { restSoundEnabled: value };
  }
  setRestSoundEnabled(enabled: boolean): Promise<Preferences> {
    if (typeof enabled !== 'boolean') return Promise.reject(new Error('Réglage sonore invalide.'));
    const result = this.pending.then(async () => {
      await this.db.runAsync(`INSERT INTO app_preferences (key, value_json, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at`,
      REST_SOUND_KEY, JSON.stringify(enabled), this.now());
      return { restSoundEnabled: enabled };
    });
    this.pending = result.then(() => undefined, () => undefined);
    return result;
  }

  async getSeriesDisplay(): Promise<SeriesDisplay> {
    await this.pending;
    const row = await this.db.getFirstAsync<{ value: string }>('SELECT value_json AS value FROM app_preferences WHERE key = ?', SERIES_DISPLAY_KEY);
    if (!row) return DEFAULT_SERIES_DISPLAY;
    const value: unknown = JSON.parse(row.value);
    if (value !== 'number' && value !== 'name' && value !== 'both') throw new Error('Le réglage des noms de séries ne peut pas être lu.');
    return value;
  }
  setSeriesDisplay(mode: SeriesDisplay): Promise<SeriesDisplay> {
    if (!['number', 'name', 'both'].includes(mode)) return Promise.reject(new Error('Affichage des séries invalide.'));
    const result = this.pending.then(async () => {
      await this.db.runAsync(`INSERT INTO app_preferences (key, value_json, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at`,
      SERIES_DISPLAY_KEY, JSON.stringify(mode), this.now());
      return mode;
    });
    this.pending = result.then(() => undefined, () => undefined);
    return result;
  }
}
