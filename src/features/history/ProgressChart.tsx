import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import Svg, { Circle, Line, Text as SvgText } from 'react-native-svg';
import { Card, colors } from '../../ui';
import { sessionStyles as s } from '../sessions/shared';
import { historyDate, historyNumber } from './shared';

export interface ChartPoint { id: string; date: string; value: number | null; label: string }
/** Discrete observations positioned on real timestamps; no invented in-between
 * points or smoothing. Native SVG is already part of the validated Expo SDK. */
export function ProgressChart({ title, unit, points, caption }: { title: string; unit: string; points: ChartPoint[]; caption?: string }) {
  const [selectedId, setSelectedId] = useState<string | null>(null), [width, setWidth] = useState(320);
  const valid = points.filter(point => point.value !== null && Number.isFinite(point.value));
  const current = valid.findIndex(point => point.id === selectedId), index = current < 0 ? valid.length - 1 : current;
  const selected = valid[index];
  const start = Date.parse(valid[0]?.date ?? ''), end = Date.parse(valid.at(-1)?.date ?? '');
  const max = Math.max(1, ...valid.map(point => point.value!));
  const x = (point: ChartPoint) => end === start ? 166 : 35 + (Date.parse(point.date) - start) / (end - start) * 262;
  const y = (point: ChartPoint) => 132 - point.value! / max * 112;
  const choose = (position: number) => {
    if (!valid.length) return;
    const viewX = position / width * 320;
    setSelectedId([...valid].sort((a, b) => Math.abs(x(a) - viewX) - Math.abs(x(b) - viewX))[0]!.id);
  };
  return <Card style={{ padding: 16, gap: 12 }}>
    <Text style={s.subtitle}>{title}</Text>
    {valid.length < 2 ? <Text style={s.body}>Deux relevés renseignés sont nécessaires pour comparer une évolution.{selected ? ` Un relevé : ${historyNumber(selected.value!)} ${unit}, le ${historyDate(selected.date)}.` : ' Aucun relevé disponible.'}</Text> : <>
      <View testID="history-chart" onLayout={event => setWidth(Math.max(1, event.nativeEvent.layout.width))}
        onTouchEnd={event => choose(event.nativeEvent.locationX)} accessible={false}>
        <Svg width="100%" height={155} viewBox="0 0 320 155" accessible={false} pointerEvents="none">
          {[20, 76, 132].map((line, i) => <Line key={i} x1={35} x2={300} y1={line} y2={line} stroke={colors.border} strokeWidth={1} />)}
          <SvgText x={2} y={24} fill={colors.muted} fontSize={10}>{historyNumber(max)}</SvgText>
          <SvgText x={14} y={136} fill={colors.muted} fontSize={10}>0</SvgText>
          {valid.map(point => <Line key={`stem-${point.id}`} x1={x(point)} x2={x(point)} y1={132} y2={y(point)} stroke={point.id === selected?.id ? '#49ebc4' : colors.blue} strokeWidth={3} />)}
          {valid.map(point => <Circle key={point.id} cx={x(point)} cy={y(point)} r={point.id === selected?.id ? 5 : 3} fill={point.id === selected?.id ? '#49ebc4' : colors.cyan} />)}
        </Svg>
      </View>
      <View style={[s.row, { justifyContent: 'space-between' }]}><Text style={s.help}>{new Date(valid[0]!.date).toLocaleDateString('fr-FR')}</Text><Text style={s.help}>{new Date(valid.at(-1)!.date).toLocaleDateString('fr-FR')}</Text></View>
      <Text accessibilityLiveRegion="polite" style={s.body}>{historyDate(selected!.date)} · {historyNumber(selected!.value!)} {unit}{selected!.label ? ` · ${selected!.label}` : ''}</Text>
      <View style={[s.row, { justifyContent: 'space-between' }]}>
        <Pressable accessibilityRole="button" accessibilityLabel={`Relevé précédent : ${title}`} accessibilityState={{ disabled: index <= 0 }} disabled={index <= 0}
          onPress={() => setSelectedId(valid[index - 1]!.id)} style={{ minHeight: 44, justifyContent: 'center' }}><Text style={{ color: index <= 0 ? colors.muted : colors.cyan }}>‹ Précédent</Text></Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={`Relevé suivant : ${title}`} accessibilityState={{ disabled: index >= valid.length - 1 }} disabled={index >= valid.length - 1}
          onPress={() => setSelectedId(valid[index + 1]!.id)} style={{ minHeight: 44, justifyContent: 'center' }}><Text style={{ color: index >= valid.length - 1 ? colors.muted : colors.cyan }}>Suivant ›</Text></Pressable>
      </View>
    </>}
    <Text style={s.help}>{caption ?? 'Chaque point représente une séance réelle. Touchez le graphique ou utilisez les boutons pour consulter les relevés.'}</Text>
    {points.some(point => point.value === null) && <Text style={s.help}>Les valeurs absentes ne sont pas représentées comme des zéros.</Text>}
  </Card>;
}
