import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert } from 'react-native';

/** A native decision never mutates data until confirmed, and ignores late
 * confirmations after leaving the route. The ref closes the double-tap window. */
export function useSessionConfirmation() {
  const gate = useRef(false), ticket = useRef(0), mounted = useRef(true), focused = useRef(false);
  const [confirming, setConfirming] = useState(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useFocusEffect(useCallback(() => { focused.current = true; setConfirming(false); return () => { focused.current = false; ticket.current++; gate.current = false; }; }, []));
  const release = () => { gate.current = false; if (mounted.current) setConfirming(false); };
  const confirm = (title: string, message: string, label: string, apply: () => void) => {
    if (gate.current || !mounted.current || !focused.current) return;
    const decision = ++ticket.current;
    gate.current = true; setConfirming(true);
    const consume = () => { if (decision !== ticket.current || !gate.current) return false; ticket.current++; release(); return true; };
    Alert.alert(title, message, [
      { text: 'Annuler', style: 'cancel', onPress: consume },
      { text: label, onPress: () => { if (consume() && mounted.current && focused.current) apply(); } },
    ], { cancelable: true, onDismiss: consume });
  };
  return { confirm, confirming };
}
