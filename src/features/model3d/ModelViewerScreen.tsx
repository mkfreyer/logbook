import { useCallback, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button, colors, Heading } from '../../ui';
import { ModelViewer, type ModelViewerHandle } from './ModelViewer';
export function ModelViewerScreen() {
  const controller = useRef<ModelViewerHandle | null>(null);
  const [ready, setReady] = useState(false);
  const readyChanged = useCallback((value: boolean) => setReady(value), []);
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <View style={s.header}><Heading title="Mannequin 3D" back /></View>
    <ModelViewer controller={controller} onReadyChange={readyChanged} />
    <View style={s.footer}>
      <Text style={s.hint}>Un doigt pour tourner · Deux doigts pour zoomer</Text>
      <Text style={s.subHint}>À deux doigts, glissez aussi vers le haut ou le bas pour explorer le corps.</Text>
      <View style={s.actions}>
        <View style={s.action}><Button label="Vue générale" icon="scan-outline" variant="secondary" disabled={!ready} onPress={() => controller.current?.command('overview')} /></View>
        <View style={s.action}><Button label="Face" icon="person-outline" variant="secondary" disabled={!ready} onPress={() => controller.current?.command('front')} /></View>
      </View>
      <Text style={s.credit}>Modèle créé avec Meshy · CC BY 4.0 · Adaptation Logbook</Text>
    </View>
  </SafeAreaView>;
}
const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background }, header: { paddingHorizontal: 24, paddingBottom: 8 },
  footer: { paddingHorizontal: 18, paddingBottom: 8, paddingTop: 10, gap: 9, borderTopWidth: 1, borderTopColor: colors.border },
  hint: { color: colors.text, fontSize: 13, textAlign: 'center' }, subHint: { color: colors.muted, fontSize: 12, lineHeight: 17, textAlign: 'center' },
  actions: { flexDirection: 'row', gap: 10 }, action: { flex: 1 }, credit: { color: colors.muted, fontSize: 10, textAlign: 'center' },
});
