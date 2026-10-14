import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import type { ComponentProps, ReactNode } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, type StyleProp, type ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const colors = {
  background: '#050d16', surface: '#0d1c2c', surfaceRaised: '#11253a',
  border: '#22415d', blue: '#168bff', cyan: '#65caff', text: '#f4f8ff',
  muted: '#a3b4c9', danger: '#ff8f9c',
};
export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
type IconName = ComponentProps<typeof Ionicons>['name'];

export function Screen({ children }: { children: ReactNode }) {
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <KeyboardAvoidingView style={s.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled" keyboardDismissMode="interactive">{children}</ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}

export function Heading({ title, subtitle, back = false, backDisabled = false, onBack, action }: { title: string; subtitle?: string; back?: boolean; backDisabled?: boolean; onBack?: () => void; action?: ReactNode }) {
  return <View style={s.heading}>
    {back && <Pressable disabled={backDisabled} onPress={onBack ?? (() => router.canGoBack() ? router.back() : router.replace({ pathname: '/', params: { universe: 'musculation' } }))} accessibilityRole="button" accessibilityLabel="Retour" accessibilityState={{ disabled: backDisabled }} style={({ pressed }) => [s.back, pressed && s.pressed, backDisabled && s.disabled]}>
      <Ionicons name="chevron-back" size={24} color={colors.text} />
    </Pressable>}
    <View style={s.flex}><Text style={s.title} accessibilityRole="header">{title}</Text>{subtitle && <Text style={s.subtitle}>{subtitle}</Text>}</View>
    {action}
  </View>;
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[s.card, style]}>{children}</View>;
}

export function Button({ label, onPress, variant = 'primary', disabled = false, loading = false, icon }: {
  label: string; onPress: () => void; variant?: 'primary' | 'secondary' | 'ghost'; disabled?: boolean; loading?: boolean; icon?: IconName;
}) {
  return <Pressable onPress={onPress} disabled={disabled || loading} accessibilityRole="button" accessibilityState={{ disabled: disabled || loading, busy: loading }}
    style={({ pressed }) => [s.button, variant === 'secondary' && s.secondary, variant === 'ghost' && s.ghost, pressed && s.pressed, (disabled || loading) && s.disabled]}>
    {loading ? <ActivityIndicator color={colors.text} /> : icon && <Ionicons name={icon} color={variant === 'ghost' ? colors.cyan : colors.text} size={20} />}
    <Text style={[s.buttonText, variant === 'ghost' && { color: colors.cyan }]}>{label}</Text>
  </Pressable>;
}

export function EmptyState({ icon, title, description }: { icon: IconName; title: string; description: string }) {
  return <View style={s.empty}>
    <View style={s.iconCircle}><Ionicons name={icon} size={32} color={colors.cyan} /></View>
    <Text style={s.emptyTitle}>{title}</Text><Text style={s.emptyDescription}>{description}</Text>
  </View>;
}

export function Field({ label, value, onChangeText, placeholder, multiline = false, maxLength }: {
  label: string; value: string; onChangeText: (text: string) => void; placeholder?: string; multiline?: boolean; maxLength?: number;
}) {
  return <View style={s.field}>
    <Text style={s.label}>{label}</Text>
    <TextInput accessibilityLabel={label} value={value} onChangeText={onChangeText} placeholder={placeholder} placeholderTextColor={colors.muted}
      maxLength={maxLength} multiline={multiline} textAlignVertical={multiline ? 'top' : 'center'} autoCapitalize="sentences"
      selectionColor={colors.cyan} style={[s.input, multiline && s.multiline]} returnKeyType={multiline ? 'default' : 'done'} />
  </View>;
}

const s = StyleSheet.create({
  flex: { flex: 1 }, screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, gap: 24, flexGrow: 1, paddingBottom: 32, width: '100%', maxWidth: 640, alignSelf: 'center' },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingTop: 8 },
  back: { minWidth: 44, minHeight: 44, justifyContent: 'center', alignItems: 'center', marginLeft: -12 },
  title: { color: colors.text, fontSize: 26, fontWeight: '700', letterSpacing: -0.6 },
  subtitle: { color: colors.muted, fontSize: 14, lineHeight: 21, marginTop: 6 },
  card: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 20, padding: 20, gap: 16 },
  button: { backgroundColor: colors.blue, borderWidth: 1, borderColor: '#42a6ff', borderRadius: 15, minHeight: 52, paddingHorizontal: 16, paddingVertical: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  secondary: { backgroundColor: colors.surfaceRaised, borderColor: colors.border },
  ghost: { backgroundColor: 'transparent', borderColor: 'transparent' },
  buttonText: { fontWeight: '600', fontSize: 16, color: colors.text, textAlign: 'center', flexShrink: 1 },
  pressed: { opacity: 0.75 }, disabled: { opacity: 0.55 },
  empty: { paddingVertical: 24, alignItems: 'center', gap: 14 },
  iconCircle: { width: 72, height: 72, borderRadius: 24, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceRaised, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { color: colors.text, fontSize: 20, fontWeight: '600', textAlign: 'center' },
  emptyDescription: { color: colors.muted, fontSize: 15, lineHeight: 23, textAlign: 'center', maxWidth: 310 },
  field: { gap: 10 }, label: { color: colors.text, fontSize: 15, fontWeight: '500' },
  input: { borderWidth: 1, borderColor: colors.border, borderRadius: 14, paddingHorizontal: 16, paddingVertical: 15, color: colors.text, backgroundColor: colors.surface, fontSize: 17, minHeight: 54 },
  multiline: { minHeight: 124 },
});
