import { setAudioModeAsync, useAudioPlayer } from 'expo-audio';
import { useEffect, useRef, useState } from 'react';
import { AppState } from 'react-native';
import { calculateRestTiming } from '../../domain/restTimer';
import type { RestInterval } from '../../domain/session';

/** A foreground-only cue. It never advances the workout or changes its saved clock.
 * An expiry missed while backgrounded/closed is displayed on return, without a late alarm. */
export function useRestAlert(rest: RestInterval | null, enabled: boolean): boolean {
  const player = useAudioPlayer(require('../../../assets/rest-complete.wav'));
  const [soundUnavailable, setSoundUnavailable] = useState(false);
  const [appActive, setAppActive] = useState(AppState.currentState === 'active');
  const sounded = useRef<string | null>(null);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => setAppActive(state === 'active'));
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (!rest || rest.endedAt || !enabled || !appActive) return;
    let alive = true;
    // An already elapsed rest may have expired while the app was closed.
    let wasExpired = calculateRestTiming(rest).expired;
    const tick = () => {
      const timing = calculateRestTiming(rest);
      if (!wasExpired && timing.expired && sounded.current !== rest.id && AppState.currentState === 'active') {
        sounded.current = rest.id;
        void (async () => {
          try {
            await setAudioModeAsync({ playsInSilentMode: false, shouldPlayInBackground: false,
              allowsRecording: false, interruptionMode: 'mixWithOthers' });
            if (!alive || AppState.currentState !== 'active') return;
            await player.seekTo(0);
            if (alive && AppState.currentState === 'active') player.play();
          } catch {
            if (alive) setSoundUnavailable(true);
          }
        })();
      }
      wasExpired = timing.expired;
    };
    const interval = setInterval(tick, 200);
    return () => { alive = false; clearInterval(interval); };
  }, [rest, enabled, appActive, player]);
  return soundUnavailable;
}
