import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Switch, Text, View } from 'react-native';
import appConfig from '../../../app.json';
import { cleanupPersonalExportCache, exportPersonalData } from '../../data/exportPersonalData';
import { PersonalExportError } from '../../data/personalExport';
import { usePreferences } from '../../store/PreferencesProvider';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { FormError, messageFor } from '../programs/shared';
import { sessionStyles as s } from '../sessions/shared';
import { SeriesDisplaySettings } from './SeriesDisplaySettings';

export function SettingsScreen() {
  const preferences = usePreferences();
  const [phase, setPhase] = useState<'idle' | 'preparing' | 'sharing'>('idle');
  const [error, setError] = useState<string | null>(null), [notice, setNotice] = useState<string | null>(null);
  const lock = useRef(false), controller = useRef<AbortController | null>(null), focused = useRef(false);
  const phaseRef = useRef(phase);
  useFocusEffect(useCallback(() => {
    focused.current = true;
    setPhase(phaseRef.current);
    try { cleanupPersonalExportCache(); } catch { setError('Le nettoyage des fichiers temporaires a échoué. Réessayez l’export pour le relancer.'); }
    return () => { focused.current = false; if (phaseRef.current === 'preparing') controller.current?.abort(); };
  }, []));
  useEffect(() => () => { if (phaseRef.current === 'preparing') controller.current?.abort(); }, []);
  const exportData = async () => {
    if (lock.current || !focused.current) return;
    lock.current = true; setError(null); setNotice(null);
    controller.current = new AbortController(); phaseRef.current = 'preparing'; setPhase('preparing');
    try {
      await exportPersonalData({ signal: controller.current.signal, onPhase: value => {
        phaseRef.current = value; if (focused.current) setPhase(value);
      } });
      if (focused.current) setNotice('Feuille de partage fermée. Vérifiez votre fichier dans Fichiers ; une annulation n’enregistre rien.');
    } catch (failure) {
      if (focused.current) {
        if (failure instanceof PersonalExportError && failure.code === 'cancelled') setNotice(failure.message);
        else setError(messageFor(failure));
      }
    } finally {
      lock.current = false; controller.current = null; phaseRef.current = 'idle';
      if (focused.current) setPhase('idle');
    }
  };
  return <Screen compact><Heading title="Paramètres" subtitle="Votre Logbook, sur cet iPhone" back backDisabled={phase !== 'idle'}
    onBack={() => { if (!lock.current) router.canGoBack() ? router.back() : router.replace({ pathname: '/', params: { universe: 'musculation' } }); }} />
    <Text style={s.eyebrow}>CHRONOMÈTRE ET ALERTES</Text>
    <Card style={{ gap: 10 }}><View style={s.row}><View style={{ flex: 1 }}><Text style={s.subtitle}>Son de fin de repos</Text>
      <Text style={s.help}>{preferences.loading ? 'Lecture du réglage…' : 'Alerte au premier plan, selon le volume et le mode silencieux iOS.'}</Text></View>
      <Switch accessibilityLabel="Son de fin de repos" value={preferences.data?.restSoundEnabled ?? false}
        disabled={preferences.loading || !!preferences.error} trackColor={{ false: colors.border, true: colors.blue }} ios_backgroundColor={colors.border}
        onValueChange={value => { void preferences.setRestSoundEnabled(value); }} /></View>
      <Text style={s.help}>Le minuteur et le passage manuel aux séries restent identiques. Aucune alerte écran verrouillé n’est garantie dans Expo Go.</Text>
      {preferences.error && <><FormError message="Le réglage n’a pas pu être lu ou enregistré. Le son reste coupé jusqu’à une lecture réussie." />
        <Button label="Réessayer le réglage sonore" variant="secondary" disabled={preferences.saving} onPress={preferences.retry} /></>}
    </Card>
    <Text style={s.eyebrow}>UNITÉS ET AFFICHAGE</Text>
    <Card style={{ gap: 8 }}><Text style={s.subtitle}>Kilogrammes · kg</Text>
      <Text style={s.body}>Les charges et les performances sont enregistrées en kilogrammes. Les modes charge totale, par haltère et charge ajoutée restent distincts.</Text>
      <Text style={s.help}>Thème sombre. Les charges restent en kilogrammes ; aucune conversion partielle en livres.</Text></Card>
    <SeriesDisplaySettings />
    <Text style={s.eyebrow}>MES DONNÉES</Text>
    <Card style={{ gap: 12 }}><Text style={s.subtitle}>Un carnet personnel local</Text>
      <Text style={s.body}>Programmes, entraînements, historiques et préférences restent sur cet appareil. Supprimer Logbook, Expo Go ou son stockage peut effacer ces données.</Text>
      <Text style={s.help}>L’export JSON contient vos données personnelles, sans chiffrement. Enregistrez-le dans un emplacement de confiance. Aucun envoi automatique à un serveur ou à un coach.</Text>
      <Button label="Exporter mes données" icon="download-outline" loading={phase !== 'idle'} onPress={() => { void exportData(); }} />
      {phase === 'preparing' && <><Text accessibilityLiveRegion="polite" style={s.help}>Préparation de votre export personnel…</Text>
        <Button label="Annuler l’export" variant="secondary" onPress={() => controller.current?.abort()} /></>}
      {phase === 'sharing' && <Text style={s.help}>Choisissez Enregistrer dans Fichiers dans la feuille native, ou annulez.</Text>}
      <FormError message={error} />{notice && <Text accessibilityLiveRegion="polite" style={s.body}>{notice}</Text>}
      <Text style={s.help}>La restauration n’est pas encore disponible dans Logbook. Ce fichier conserve les données pour une restauration future ; ne supprimez pas vos données actuelles en pensant pouvoir déjà le réimporter.</Text>
    </Card>
    <Text style={s.eyebrow}>À PROPOS</Text>
    <Card style={{ gap: 8 }}><Text style={s.subtitle}>Logbook</Text><Text style={s.body}>Version {appConfig.expo.version}</Text>
      <Text style={s.help}>Musculation personnelle · hors ligne · sans compte obligatoire.</Text></Card>
  </Screen>;
}
