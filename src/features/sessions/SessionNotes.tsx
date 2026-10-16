import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import { Button, Field, Heading, Screen } from '../../ui';
import { FormError, LoadState } from '../programs/shared';
import { useScreenOperation } from '../training/shared';
import { Choice, sessionStyles as s, useSessionData } from './shared';

export function SessionNotes({ sessionId }: { sessionId?: string }) {
  const data = useSessionData(sessionId), operation = useScreenOperation();
  const [exerciseId, setExerciseId] = useState<string | null>(null), [body, setBody] = useState('');
  useEffect(() => { setBody(exerciseId === null ? data.session?.personalNote ?? '' : data.session?.exerciseNotes?.[exerciseId] ?? ''); }, [data.session, exerciseId]);
  const back = () => { if (operation.lock.current) return; Keyboard.dismiss(); if (router.canGoBack()) router.back(); else if (sessionId) router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); };
  return <Screen compact footer={data.session?.id === sessionId && !data.loading && !data.error ? <View style={{ gap: 8 }}>
    <FormError message={operation.error} /><Button label="Enregistrer la note" icon="checkmark" loading={operation.busy}
      onPress={() => { if (!data.session) return; Keyboard.dismiss(); void operation.run(() => data.repository.savePersonalNote(data.session!.id, body, exerciseId),
        () => { if (router.canGoBack()) router.back(); else router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: data.session!.id } }); }, true); }} />
  </View> : undefined}>
    <Heading title="Notes personnelles" back backDisabled={operation.busy} onBack={back} />
    {data.loading || data.error || !data.session ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : <View style={s.sections}>
      <Text style={s.help}>Notes de cet entraînement uniquement. Les consignes du programme, performances et repos restent conservés.</Text>
      <View style={{ gap: 8 }} accessibilityRole="radiogroup" accessibilityLabel="Objet de la note">
        <Choice label="Cet entraînement" selected={exerciseId === null} disabled={operation.busy} onPress={() => setExerciseId(null)} />
        {data.session.exercises.map((exercise, index) => <Choice key={exercise.id} label={`${index + 1}. ${exercise.name}`} selected={exerciseId === exercise.id} disabled={operation.busy} onPress={() => setExerciseId(exercise.id)} />)}
      </View>
      <Field label="Note personnelle" value={body} onChangeText={setBody} multiline maxLength={4000} placeholder="Votre ressenti, un rappel…" />
      <Button label="Annuler" variant="ghost" disabled={operation.busy} onPress={back} />
    </View>}
  </Screen>;
}
