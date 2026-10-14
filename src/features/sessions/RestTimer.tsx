import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { calculateRestTiming, formatDuration } from '../../domain/restTimer';
import type { RestInterval } from '../../domain/session';
import { Button, Card, colors } from '../../ui';
import { sessionStyles } from './shared';

/** The tick only repaints. Every displayed duration is reconstructed from SQLite timestamps. */
export function RestTimer({ rest, busy, onPause, onResume, onComplete, showAction = true }: {
  rest: RestInterval; busy: boolean; onPause(): void; onResume(): void; onComplete(): void; showAction?: boolean;
}) {
  const [now, setNow] = useState(Date.now);
  const [foreground, setForeground] = useState(AppState.currentState === 'active');
  const [focused, setFocused] = useState(false);
  useFocusEffect(useCallback(() => { setFocused(true); setNow(Date.now()); return () => setFocused(false); }, []));
  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      setForeground(state === 'active'); setNow(Date.now());
    });
    return () => subscription.remove();
  }, []);
  useEffect(() => {
    if (!foreground || !focused) return;
    const repaint = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(repaint);
  }, [foreground, focused]);
  const timing = calculateRestTiming(rest, now);
  const size = Math.min(useWindowDimensions().width - 48, 320);
  const radius = size / 2 - 14, circumference = 2 * Math.PI * radius;
  const accent = timing.expired ? '#ff785c' : '#49ebc4';
  const remaining = formatDuration(Math.ceil(timing.remainingMs / 1000) * 1000);
  return <View style={sessionStyles.sections}>
    <View style={styles.timerWrap}>
      <View style={{ width: size, height: size }} accessible={false}>
        <Svg width={size} height={size} pointerEvents="none" accessibilityElementsHidden>
          <Circle cx={size / 2} cy={size / 2} r={radius} stroke={timing.expired ? '#442525' : '#153d43'} strokeWidth={13} fill="transparent" />
          <Circle cx={size / 2} cy={size / 2} r={radius} stroke={accent} strokeWidth={13} fill="transparent"
            strokeLinecap="round" strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={timing.expired ? 0 : circumference * timing.progress}
            rotation={-90} origin={`${size / 2}, ${size / 2}`} />
        </Svg>
        <View style={styles.center}>
          <Text style={[styles.clock, { color: timing.expired ? accent : colors.text }]} accessibilityLabel={timing.expired ? 'Temps de dépassement' : 'Temps restant'}>
            {timing.expired ? `+${formatDuration(timing.overtimeMs)}` : remaining}
          </Text>
          <Text style={[styles.state, { color: timing.expired ? accent : colors.muted }]}>{timing.isPaused ? 'MINUTEUR EN PAUSE' : timing.expired ? 'REPOS DÉPASSÉ' : 'TEMPS RESTANT'}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel={timing.isPaused ? 'Reprendre le minuteur' : 'Mettre le minuteur en pause'}
            accessibilityState={{ disabled: busy }} disabled={busy} onPress={timing.isPaused ? onResume : onPause}
            style={({ pressed }) => [styles.pause, timing.expired && styles.pauseOvertime, (pressed || busy) && styles.dimmed]}>
            <Ionicons name={timing.isPaused ? 'play' : 'pause'} size={30} color={colors.text} />
          </Pressable>
        </View>
      </View>
    </View>
    <View style={sessionStyles.row}>
      <Card style={[styles.metric, timing.expired && styles.metricOvertime]}><Text style={sessionStyles.body}>Repos prévu</Text><Text style={styles.metricValue}>{formatDuration(rest.plannedSeconds * 1000)}</Text></Card>
      <Card style={[styles.metric, timing.expired && styles.metricOvertime]}><Text style={sessionStyles.body}>Repos réel</Text><Text style={styles.metricValue} accessibilityLabel="Repos réel écoulé">{formatDuration(timing.chronologicalMs)}</Text></Card>
    </View>
    {timing.isPaused && <Text style={sessionStyles.help}>Le compte à rebours est en pause. Votre repos réel continue de mesurer le temps écoulé.</Text>}
    {showAction && <Button label={timing.expired ? 'Repos terminé' : 'Passer à la série suivante'} icon="arrow-forward" disabled={busy} onPress={onComplete} />}
    <Text style={[sessionStyles.help, sessionStyles.center]}>Vous décidez quand continuer.</Text>
  </View>;
}

const styles = StyleSheet.create({
  timerWrap: { alignItems: 'center' },
  center: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, alignItems: 'center', justifyContent: 'center', gap: 8 },
  clock: { fontSize: 46, fontWeight: '700', fontVariant: ['tabular-nums'], letterSpacing: -1 },
  state: { fontSize: 10, letterSpacing: 1.2, fontWeight: '600', marginBottom: 10 },
  pause: { width: 66, height: 66, borderRadius: 33, borderWidth: 1, borderColor: '#70bdff', backgroundColor: colors.blue, alignItems: 'center', justifyContent: 'center' },
  pauseOvertime: { backgroundColor: '#c34e3e', borderColor: '#ff987e' }, dimmed: { opacity: 0.55 },
  metric: { flex: 1, minWidth: 0, gap: 4, padding: 16, backgroundColor: '#0c222b', borderColor: '#24515a' },
  metricOvertime: { backgroundColor: '#251b20', borderColor: '#69372f' },
  metricValue: { fontSize: 29, fontWeight: '600', color: colors.text, fontVariant: ['tabular-nums'] },
});
