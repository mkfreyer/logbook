import { DatabaseSync } from 'node:sqlite';
import type { Database } from '../../src/db/types';

export class SqliteDatabase implements Database {
  readonly raw: DatabaseSync;
  constructor(path = ':memory:') { this.raw = new DatabaseSync(path); }
  async execAsync(sql: string) { this.raw.exec(sql); }
  async runAsync(sql: string, ...args: (string | number | null)[]) {
    return { changes: Number(this.raw.prepare(sql).run(...args).changes) };
  }
  async getFirstAsync<T>(sql: string, ...args: (string | number | null)[]): Promise<T | null> {
    const row = this.raw.prepare(sql).get(...args); return row ? { ...row } as T : null;
  }
  async getAllAsync<T>(sql: string, ...args: (string | number | null)[]): Promise<T[]> {
    return this.raw.prepare(sql).all(...args).map(row => ({ ...row }) as T);
  }
  async withTransactionAsync(task: () => Promise<void>) {
    this.raw.exec('BEGIN IMMEDIATE');
    try { await task(); this.raw.exec('COMMIT'); } catch (error) { this.raw.exec('ROLLBACK'); throw error; }
  }
  close() { this.raw.close(); }
}
