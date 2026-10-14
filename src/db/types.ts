/** The subset of Expo SQLite also implemented by our real SQLite test adapter. */
export interface Database {
  execAsync(source: string): Promise<void>;
  runAsync(
    source: string,
    ...params: (string | number | null)[]
  ): Promise<{ changes: number }>;
  getFirstAsync<T>(
    source: string,
    ...params: (string | number | null)[]
  ): Promise<T | null>;
  getAllAsync<T>(
    source: string,
    ...params: (string | number | null)[]
  ): Promise<T[]>;
  withTransactionAsync(task: () => Promise<void>): Promise<void>;
}
