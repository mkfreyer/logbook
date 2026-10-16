import { setKindLabel, type SetKind } from './training';

export type SeriesDisplay = 'number' | 'name' | 'both';
export const DEFAULT_SERIES_DISPLAY: SeriesDisplay = 'name';
export function parseLoadPercentage(text: string): number {
  if (!/^\d+(?:[.,]\d+)?$/.test(text.trim())) throw new Error('Indiquez un pourcentage numérique, par exemple 50 ou 75,5.');
  const value = Number(text.trim().replace(',', '.'));
  percentageWeight(null, value);
  return value;
}
export function formatSeriesTitle(series: { label: string; kind: SetKind }, index: number, mode: SeriesDisplay = DEFAULT_SERIES_DISPLAY): string {
  const number = `Série ${index + 1}`;
  const name = series.label.trim() || (series.kind === 'work' ? '' : setKindLabel[series.kind]);
  return mode === 'number' ? number : mode === 'name' ? name || number : name ? `${number} · ${name}` : number;
}

/** Multiply the decimal values exactly as represented by JS, then convert once
 * to SQLite REAL. No rounding to plates, dumbbells, or a chosen kg increment. */
export function percentageWeight(reference: number | null, percent: number): number | null {
  if (!Number.isFinite(percent) || percent <= 0 || percent > 100) throw new Error('Le pourcentage doit être supérieur à 0 et inférieur ou égal à 100.');
  if (reference === null) return null;
  if (!Number.isFinite(reference) || reference < 0) throw new Error('La charge de référence est invalide.');
  const decimal = (value: number) => {
    const [mantissa, exponent = '0'] = String(value).toLowerCase().split('e');
    const [whole, fraction = ''] = mantissa!.split('.');
    return { integer: BigInt(whole! + fraction), scale: fraction.length - Number(exponent) };
  };
  const a = decimal(reference), b = decimal(percent);
  const result = Number(`${a.integer * b.integer}e${-(a.scale + b.scale + 2)}`);
  if (!Number.isFinite(result) || (reference > 0 && result === 0)) throw new Error('Cette charge calculée ne peut pas être représentée fidèlement. Saisissez une charge manuelle.');
  return result;
}
