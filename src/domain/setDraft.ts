import type { SetKind, SetTemplateInput } from './training';

export interface SetDraft {
  label: string; kind: SetKind; repetitionMode: 'exact' | 'range';
  repsMin: string; repsMax: string; weight: string; rir: string; rest: string; notes: string;
}

function numberField(raw: string, label: string, integer: boolean, optional = false): number | null {
  const text = raw.trim();
  if (!text && optional) return null;
  if (!(integer ? /^\d+$/ : /^\d+(?:[.,]\d+)?$/).test(text)) {
    throw new Error(`${label} : indiquez un nombre ${integer ? 'entier ' : ''}positif ou nul${optional ? ', ou laissez le champ vide' : ''}.`);
  }
  const value = Number(text.replace(',', '.'));
  if (!Number.isFinite(value) || (integer && !Number.isSafeInteger(value))) throw new Error(`${label} : cette valeur est trop grande.`);
  return value;
}

/** Parse French decimals strictly. Blank optional targets remain null, never zero. */
export function parseSetDraft(draft: SetDraft): SetTemplateInput {
  const repsMin = numberField(draft.repsMin, 'Répétitions', true)!;
  const repsMax = draft.repetitionMode === 'exact' ? repsMin : numberField(draft.repsMax, 'Répétitions maximum', true)!;
  if (repsMax < repsMin) throw new Error('Le maximum de répétitions doit être supérieur ou égal au minimum.');
  const targetWeightKg = numberField(draft.weight, 'Charge', false, true);
  const targetRir = numberField(draft.rir, 'RIR', true, true);
  if (targetRir !== null && targetRir > 10) throw new Error('Le RIR cible doit être compris entre 0 et 10.');
  const restAfterSec = numberField(draft.rest, 'Repos', true)!;
  if (restAfterSec > 86400) throw new Error('Le repos doit être compris entre 0 et 86 400 secondes.');
  if (draft.label.trim().length > 80 || draft.notes.trim().length > 1000) throw new Error('L’étiquette est limitée à 80 caractères et les notes à 1 000 caractères.');
  return { label: draft.label.trim(), kind: draft.kind, repsMin, repsMax, targetWeightKg, targetRir, restAfterSec, notes: draft.notes.trim() };
}
