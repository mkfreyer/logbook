import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert } from 'react-native';

/** Share the editor's synchronous lock with saving, so neither operation can
 * start while the other is awaiting confirmation or storage. */
export function useConfirmedDelete({ title, message, remove, onDeleted, failureMessage, operationLock }: {
  title: string;
  message: string;
  remove(): Promise<void>;
  onDeleted(): void;
  failureMessage: string;
  operationLock?: { current: boolean };
}) {
  const ownLock = useRef(false);
  const lock = operationLock ?? ownLock;
  const phase = useRef<'idle' | 'confirming' | 'deleting' | 'done'>('idle');
  const mounted = useRef(true);
  const focused = useRef(false);
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useFocusEffect(useCallback(() => {
    focused.current = true;
    if (phase.current === 'idle') setBusy(false);
    return () => {
      focused.current = false;
      // A confirmation left behind by a route change must no longer delete.
      if (phase.current === 'confirming') { phase.current = 'idle'; lock.current = false; }
    };
  }, [lock]));

  const cancel = () => {
    if (phase.current !== 'confirming') return;
    phase.current = 'idle';
    lock.current = false;
    if (mounted.current) setBusy(false);
  };
  const execute = async () => {
    if (phase.current !== 'confirming' || !focused.current || !mounted.current) return;
    phase.current = 'deleting';
    setDeleting(true);
    try {
      await remove();
      if (mounted.current && focused.current) {
        onDeleted();
        phase.current = 'done';
      }
    } catch {
      if (mounted.current && focused.current) setError(failureMessage);
    } finally {
      // Keep the success lock until this removed screen leaves the stack.
      if (phase.current !== 'done') { phase.current = 'idle'; lock.current = false; }
      if (mounted.current) { setBusy(false); setDeleting(false); }
    }
  };

  const confirm = () => {
    if (lock.current || !mounted.current || !focused.current) return;
    lock.current = true;
    phase.current = 'confirming';
    setBusy(true);
    setError(null);
    Alert.alert(title, message, [
      { text: 'Annuler', style: 'cancel', onPress: cancel },
      { text: 'Supprimer', style: 'destructive', onPress: () => { void execute(); } },
    ], { cancelable: true, onDismiss: cancel });
  };

  return { confirm, busy, deleting, error };
}
