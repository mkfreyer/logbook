import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, AppState, StyleSheet, Text, View } from 'react-native';
import { WebView } from 'react-native-webview';
import { Button, colors } from '../../ui';
import { commandScript, parseViewerEvent, type SurfaceHit, type ViewerCommand } from './bridge';
import { buildViewerDocument } from './document';
import { loadModelBase64 } from './loadModel';

export type ModelViewerHandle = { command(command: Exclude<ViewerCommand, 'dispose'>): void };
export function ModelViewer({ controller, onReadyChange, onSurfaceTouch }: {
  controller: React.RefObject<ModelViewerHandle | null>;
  onReadyChange(ready: boolean): void;
  onSurfaceTouch?: (hit: SurfaceHit) => void;
}) {
  // WebView 14 defaults its additional-props generic to undefined, making
  // WebViewProps & undefined resolve to never. No extra props are required.
  const web = useRef<WebView<unknown>>(null);
  const [focused, setFocused] = useState(false);
  const [active, setActive] = useState(AppState.currentState === 'active');
  const appActive = useRef(AppState.currentState === 'active');
  const [attempt, setAttempt] = useState(0);
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const generation = useRef(0);
  const source = useMemo(() => html ? { html } : undefined, [html]);
  const visible = focused && active;
  const dispose = useCallback(() => { web.current?.injectJavaScript(commandScript('dispose')); }, []);
  useFocusEffect(useCallback(() => {
    generation.current++; setFocused(true);
    return () => { generation.current++; dispose(); setFocused(false); };
  }, [dispose]));
  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      const next = state === 'active';
      if (appActive.current === next) return;
      appActive.current = next; generation.current++;
      if (!next) dispose();
      setActive(next);
    });
    return () => { subscription.remove(); dispose(); };
  }, [dispose]);
  useEffect(() => {
    let cancelled = false;
    setHtml(null); setError(null); setReady(false);
    const timeout = setTimeout(() => { if (!cancelled) { cancelled = true; setError('Le mannequin local n’a pas pu être chargé.'); } }, 25000);
    void loadModelBase64().then(value => {
      clearTimeout(timeout);
      if (!cancelled) setHtml(buildViewerDocument(value));
    }).catch(() => { clearTimeout(timeout); if (!cancelled) setError('Le mannequin local n’a pas pu être chargé.'); });
    return () => { cancelled = true; clearTimeout(timeout); };
  }, [attempt]);
  useEffect(() => {
    setReady(false);
  }, [visible, html, attempt]);
  // A ready event clears the loading timeout by changing this effect's lifetime.
  useEffect(() => {
    if (!visible || !html || ready || error) return;
    const timeout = setTimeout(() => setError('Le chargement 3D n’a pas abouti. Vous pouvez réessayer.'), 25000);
    return () => clearTimeout(timeout);
  }, [visible, html, ready, error]);
  useEffect(() => { onReadyChange(ready && visible && !error); }, [ready, visible, error, onReadyChange]);
  useEffect(() => {
    controller.current = { command: command => { if (ready && visible && !error) web.current?.injectJavaScript(commandScript(command)); } };
    return () => { controller.current = null; };
  }, [controller, ready, visible, error]);
  useEffect(() => { if (error) { dispose(); setReady(false); } }, [error, dispose]);
  // Every WebView mount owns its event closure; late messages from destroyed pages are ignored.
  const currentGeneration = visible && html && !error ? generation.current : -1;
  function fail(message: string) { if (currentGeneration === generation.current) { generation.current++; setError(message); } }
  function retry() { dispose(); generation.current++; setAttempt(value => value + 1); }
  return <View style={s.container} testID="model-viewer-container">
    {visible && html && !error ? <WebView<unknown> key={`${attempt}-${active}-${focused}`} ref={web}
      testID="model-webview" style={s.web} source={source} originWhitelist={['*']}
      javaScriptEnabled scrollEnabled={false} bounces={false} overScrollMode="never"
      contentInsetAdjustmentBehavior="never" automaticallyAdjustContentInsets={false}
      allowsLinkPreview={false} dataDetectorTypes="none" cacheEnabled={false} incognito
      javaScriptCanOpenWindowsAutomatically={false} setSupportMultipleWindows={false}
      onShouldStartLoadWithRequest={request => request.url === 'about:blank'}
      onMessage={event => {
        if (currentGeneration !== generation.current || !visible) return;
        const message = parseViewerEvent(event.nativeEvent.data);
        if (message?.type === 'ready') { setReady(true); setError(null); }
        else if (message?.type === 'error') fail('Le rendu 3D a été interrompu. Réessayez.');
        else if (message?.type === 'surface-hit' && ready) onSurfaceTouch?.(message.hit);
      }}
      onError={() => fail('Le visualiseur 3D n’a pas pu démarrer.')}
      onContentProcessDidTerminate={() => fail('Le rendu 3D a été interrompu. Réessayez.')}
      onRenderProcessGone={() => fail('Le rendu 3D a été interrompu. Réessayez.')} /> : null}
    {!ready && !error ? <View style={s.notice} pointerEvents="none" accessibilityLiveRegion="polite">
      <ActivityIndicator size="large" color={colors.cyan} accessibilityLabel="Chargement du mannequin" />
      <Text style={s.message}>Chargement du mannequin…</Text>
    </View> : null}
    {error ? <View style={s.notice} accessibilityLiveRegion="polite">
      <Text style={s.message}>{error}</Text>
      <Button label="Réessayer" icon="refresh-outline" onPress={retry} />
    </View> : null}
  </View>;
}
const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background }, web: { flex: 1, backgroundColor: colors.background },
  notice: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, justifyContent: 'center', alignItems: 'center', padding: 24, gap: 18, backgroundColor: colors.background },
  message: { color: colors.muted, fontSize: 15, lineHeight: 22, textAlign: 'center' },
});
