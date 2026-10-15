import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';

import { useLogbook } from '../../store/LogbookProvider';
import { Button, Card, Field, Heading, Screen } from '../../ui';
import { featureStyles, FormError, LoadState, RefreshNotice, LocalNotice, messageFor, useFocusedData } from './shared';

export function ProgramEditor({ mode, id }: { mode: 'create' | 'edit'; id?: string }) {
  const editing = mode === 'edit';
  const { getProgram, createProgram, updateProgram } = useLogbook();
  const load = useCallback(() => editing && id ? getProgram(id) : Promise.resolve(null), [editing, getProgram, id]);
  const { data: program, loading, error, refreshError, refreshing, retry } = useFocusedData(load);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const mounted = useRef(true);
  const focused = useRef(false);

  useFocusEffect(useCallback(() => {
    focused.current = true;
    return () => { focused.current = false; };
  }, []));

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    if (program) { setName(program.name); setDescription(program.description ?? ''); }
  }, [program]);

  const save = async () => {
    if (savingRef.current) return;
    if (!name.trim()) { setFormError('Donnez un nom à votre programme.'); return; }
    if (name.trim().length > 80 || description.trim().length > 1000) {
      setFormError('Le nom est limité à 80 caractères et la description à 1 000 caractères.'); return;
    }
    if (editing && !id) return;
    savingRef.current = true;
    setSaving(true);
    setFormError(null);
    try {
      const input = { name: name.trim(), description: description.trim() };
      const saved = editing && id ? await updateProgram(id, input) : await createProgram(input);
      if (mounted.current && focused.current) {
        if (editing && router.canGoBack()) router.back();
        else router.replace({ pathname: '/programs/[id]', params: { id: saved.id } });
      }
    } catch (failure: unknown) {
      if (mounted.current && focused.current) setFormError(messageFor(failure));
    } finally {
      savingRef.current = false;
      if (mounted.current) setSaving(false);
    }
  };

  const cancel = () => {
    if (router.canGoBack()) router.back();
    else if (editing && id) router.replace({ pathname: '/programs/[id]', params: { id } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };

  return <Screen>
    <Heading title={editing ? 'Modifier le programme' : 'Créer un programme'} back backDisabled={saving} />
    <RefreshNotice refreshError={refreshError} refreshing={refreshing} retry={retry} />
    {loading || error || (editing && !program) ? <LoadState loading={loading} error={error} retry={retry}
      missing="Ce programme n’est pas disponible." /> : <View style={featureStyles.sections}>
      <Text style={featureStyles.body}>{editing
        ? 'Adaptez le nom et la description de votre programme.'
        : 'Un nom, un objectif, puis vos premières séances. Vous pourrez tout modifier ensuite.'}</Text>
      <Card>
        <View style={featureStyles.sections}>
          <Field label="Nom du programme" value={name} onChangeText={(value) => { setName(value); setFormError(null); }}
            placeholder="Ex. Mon programme" maxLength={80} />
          <Field label="Description (facultative)" value={description} onChangeText={setDescription}
            placeholder="Votre objectif ou votre organisation" multiline maxLength={1000} />
        </View>
      </Card>
      <FormError message={formError} />
      <Button label={editing ? 'Enregistrer les modifications' : 'Créer le programme'} onPress={() => { void save(); }}
        icon="checkmark" loading={saving} disabled={saving} />
      <Button label="Annuler" variant="ghost" onPress={cancel} disabled={saving} />
      <LocalNotice />
    </View>}
  </Screen>;
}
