import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert } from 'react-native';
import type { SessionRepository } from '../../db/sessionRepository';
import type { SessionSet, WorkoutSession } from '../../domain/session';
import type { useScreenOperation } from '../training/shared';

/** A decision captures the exact set/revision and shares the save lock. Cancel,
 * blur and repeated native callbacks invalidate it before any write can happen. */
export function useSkipSet({ operation, repository, sessionId, onSkipped, leavesScreen = false }: {
  operation: ReturnType<typeof useScreenOperation>; repository: SessionRepository; sessionId?: string;
  onSkipped(session: WorkoutSession): void; leavesScreen?: boolean;
}) {
  const [confirming, setConfirming] = useState(false);
  const mounted = useRef(true), focused = useRef(false), ticket = useRef(0), pending = useRef(false);
  const release = () => {
    if (!pending.current) return;
    pending.current = false; ticket.current++; operation.lock.current = false;
    if (mounted.current) setConfirming(false);
  };
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; release(); }; }, []);
  useEffect(() => { release(); }, [sessionId]);
  useFocusEffect(useCallback(() => {
    focused.current = true;
    return () => { focused.current = false; release(); };
  }, [operation.lock]));
  const confirm = (series: SessionSet) => {
    if (!sessionId || series.skippedAt || operation.lock.current || !mounted.current || !focused.current) return;
    operation.lock.current = true; pending.current = true; setConfirming(true);
    const capturedSession = sessionId, id = series.id, revision = series.passageRevision ?? 0, current = ++ticket.current;
    Alert.alert('Passer cette série', "Passer cette série pour aujourd'hui ? Elle restera dans votre programme.", [
      { text: 'Annuler', style: 'cancel', onPress: () => { if (ticket.current === current) release(); } },
      { text: 'Passer cette série', onPress: () => {
        if (!pending.current || ticket.current !== current || !mounted.current || !focused.current) return;
        release();
        let saved!: WorkoutSession;
        void operation.run(async () => { saved = await repository.skipSet(capturedSession, id, revision); }, () => onSkipped(saved), leavesScreen);
      } },
    ], { cancelable: true, onDismiss: () => { if (ticket.current === current) release(); } });
  };
  return { confirm, confirming };
}
