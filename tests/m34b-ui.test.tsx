import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { router } from 'expo-router';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { SessionSet, WorkoutSession } from '../src/domain/session';
import { useSessions } from '../src/store/SessionProvider';
import { SessionSetEditor } from '../src/features/sessions/SessionSetEditor';
import { RestTimer } from '../src/features/sessions/RestTimer';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionNotes } from '../src/features/sessions/SessionNotes';
import { SessionSummaryView } from '../src/features/sessions/SessionSummaryView';

jest.mock('expo-router',()=>{const React=require('react'); return { router:{push:jest.fn(),dismissTo:jest.fn(),back:jest.fn(),canGoBack:jest.fn()}, useFocusEffect:(effect:()=>any)=>React.useEffect(effect,[effect]) };});
jest.mock('expo-crypto',()=>({randomUUID:()=> 'addition-intent'}));
jest.mock('../src/store/SessionProvider',()=>({useSessions:jest.fn()}));
jest.mock('../src/features/sessions/PreviousPerformanceCard',()=>({PreviousPerformanceCard:()=>null}));
jest.mock('../src/features/sessions/RestTimer',()=>({RestTimer:jest.fn(()=>null)}));
jest.mock('@expo/vector-icons',()=>({Ionicons:()=>null}));
jest.mock('react-native-safe-area-context',()=>jest.requireActual<{default:unknown}>('react-native-safe-area-context/jest/mock').default);
const targets={repsMin:8,repsMax:10,targetWeightKg:100,targetRir:2,restAfterSec:60};
const top:SessionSet={id:'top',sessionId:'session',sessionExerciseId:'exercise',sourceSetTemplateId:'source-top',sortOrder:0,seriesIndex:0,label:'Top',kind:'top_set',notes:'',targets,originalTargets:targets};
const back:SessionSet={...top,id:'back',sourceSetTemplateId:'source-back',sortOrder:1,seriesIndex:1,label:'Back',kind:'back_off',targets:{...targets,targetWeightKg:null},loadRule:{basis:'performed_weight',referenceSetId:'top',percent:90,weightMode:'total',suspended:false}};
const initial:WorkoutSession={id:'session',sourceProgramId:'program',sourceWorkoutTemplateId:'workout',workoutName:'Ma séance',programName:'Mon programme',status:'active',startedAt:'2026-10-16T12:00:00Z',finishedAt:null,
  exercises:[{id:'exercise',sessionId:'session',sourceWorkoutExerciseId:'source-exercise',sourceCatalogExerciseId:'catalog',sortOrder:0,plannedOrder:0,name:'Barre',muscleGroup:'Dos',equipment:'Barre',instructions:'',notes:'Consigne',weightMode:'total'},
    {id:'other',sessionId:'session',sourceWorkoutExerciseId:'source-other',sourceCatalogExerciseId:'other-catalog',sortOrder:1,plannedOrder:1,name:'Haltères',muscleGroup:'Dos',equipment:'Haltères',instructions:'',notes:'',weightMode:'per_hand'}],
  sets:[top,back,{...top,id:'other-set',sessionExerciseId:'other',sortOrder:2,label:'Autre'}],performances:[],rests:[]};
const repo={getSession:jest.fn<SessionRepository['getSession']>(),getActiveSession:jest.fn<SessionRepository['getActiveSession']>(),
  canUpdateProgram:jest.fn<SessionRepository['canUpdateProgram']>(),addSet:jest.fn<SessionRepository['addSet']>(),updateSet:jest.fn<SessionRepository['updateSet']>(),
  skipSet:jest.fn<SessionRepository['skipSet']>(),reintegrateSet:jest.fn<SessionRepository['reintegrateSet']>(),completeRest:jest.fn<SessionRepository['completeRest']>(),finishSession:jest.fn<SessionRepository['finishSession']>(),validateSet:jest.fn<SessionRepository['validateSet']>(),
  deleteAddedSet:jest.fn<SessionRepository['deleteAddedSet']>(),savePersonalNote:jest.fn<SessionRepository['savePersonalNote']>()};
beforeEach(()=>{jest.resetAllMocks(); repo.getSession.mockResolvedValue(initial);repo.canUpdateProgram.mockResolvedValue(true);repo.addSet.mockResolvedValue(initial);repo.updateSet.mockResolvedValue(initial);repo.savePersonalNote.mockResolvedValue(initial);repo.deleteAddedSet.mockResolvedValue(initial);
  repo.skipSet.mockResolvedValue(skipped(initial,['top']));repo.reintegrateSet.mockResolvedValue(initial);jest.mocked(RestTimer).mockImplementation(()=> <></>);
  jest.mocked(useSessions).mockReturnValue(repo as unknown as SessionRepository);});
afterEach(()=>{cleanup();jest.restoreAllMocks();});
function deferred<T>(){let resolve!:(value:T)=>void; const promise=new Promise<T>(done=>{resolve=done;});return {promise,resolve};}

test.each(['set','rest','ready'] as const)('secondary addition and notes remain available in phase %s',async phase=>{
  if(phase==='ready')repo.getSession.mockResolvedValue({...initial,performances:initial.sets.map((s,i)=>({id:`p${i}`,sessionId:initial.id,sessionSetId:s.id,sortOrder:i,weightKg:95,reps:8,rir:null,performedAt:initial.startedAt,advancedAt:initial.startedAt}))});
  if(phase==='rest')repo.getSession.mockResolvedValue({...initial,performances:[{id:'p',sessionId:initial.id,sessionSetId:top.id,sortOrder:0,weightKg:95,reps:8,rir:null,performedAt:initial.startedAt,advancedAt:null}],rests:[{id:'rest',sessionId:initial.id,performedSetId:'p',plannedSeconds:60,startedAt:initial.startedAt,endedAt:null,chronologicalMs:null,activeMs:null,pauses:[]}]});
  const view=render(<SessionScreen sessionId="session"/>);fireEvent.press(await view.findByRole('button',{name:'Actions de séance'}));
  expect(view.getByRole('button',{name:'Notes personnelles'})).toBeTruthy();
  fireEvent.press(view.getByRole('button',{name:'Ajouter une série'})); await waitFor(()=>expect(router.push).toHaveBeenCalledWith({pathname:'/sessions/[sessionId]/add',params:{sessionId:'session'}}));
});
test('addition chooses another exercise, carries all optional goals and defaults to this session without double taps',async()=>{
  const pending=deferred<WorkoutSession>();repo.addSet.mockReturnValue(pending.promise);
  const view=render(<SessionSetEditor sessionId="session" adding/>);await view.findByRole('radio',{name:'Haltères'});
  fireEvent.press(view.getByRole('radio',{name:'Haltères'}));fireEvent.press(view.getByRole('radio',{name:'Personnalisée'}));
  fireEvent.changeText(view.getByLabelText('Nom de la série (facultatif)'),'Bonus');
  fireEvent.press(view.getByRole('radio',{name:'Plage min / max'}));fireEvent.changeText(view.getByLabelText('Répétitions minimum'),'12');fireEvent.changeText(view.getByLabelText('Répétitions maximum'),'15');
  fireEvent.changeText(view.getByLabelText('Notes de la série (facultatives)'),'Imprévu');
  const save=view.getByRole('button',{name:'Ajouter la série'});fireEvent.press(save);fireEvent.press(save);
  expect(repo.addSet).toHaveBeenCalledTimes(1);expect(repo.addSet).toHaveBeenCalledWith('session','other',expect.objectContaining({kind:'custom',label:'Bonus',repsMin:12,repsMax:15,targetWeightKg:null,notes:'Imprévu'}),'session','addition-intent');
  await act(async()=>{pending.resolve(initial);await pending.promise;});expect(router.dismissTo).toHaveBeenCalledTimes(1);
});
test('Program is explicit and unavailable source models cannot be selected',async()=>{
  repo.canUpdateProgram.mockResolvedValue(false);const view=render(<SessionSetEditor sessionId="session" adding/>);
  await view.findByRole('radio',{name:'Barre'});await waitFor(()=>expect(repo.canUpdateProgram).toHaveBeenCalled());
  expect(view.getByRole('radio',{name:'Programme'}).props.accessibilityState.disabled).toBe(true);
  fireEvent.press(view.getByRole('button',{name:'Annuler'}));expect(repo.addSet).not.toHaveBeenCalled();
});
test('a Program addition passes its scope only after an explicit choice',async()=>{
  const view=render(<SessionSetEditor sessionId="session" adding/>);
  await waitFor(()=>expect(view.getByRole('radio',{name:'Programme'}).props.accessibilityState.disabled).toBe(false));
  fireEvent.press(view.getByRole('radio',{name:'Programme'}));fireEvent.press(view.getByRole('button',{name:'Ajouter la série'}));
  await waitFor(()=>expect(repo.addSet).toHaveBeenCalledWith('session','exercise',expect.anything(),'program','addition-intent'));
});
test('a different unperformed series is editable, real reference is pending and remains an explicit rule',async()=>{
  const view=render(<SessionSetEditor sessionId="session" setId="top"/>);
  fireEvent.press(await view.findByRole('button',{name:'Choisir une autre série restante'}));
  fireEvent.press(view.getByRole('radio',{name:'Barre · Back'}));
  await view.findByText('En attente de la série de référence');
  expect(view.getByLabelText('Charge cible (kg)').props.value).toBe('');
  expect(view.queryByLabelText('Charge réelle (kg)')).toBeNull();
  fireEvent.press(view.getByRole('button',{name:'Enregistrer les objectifs'}));
  await waitFor(()=>expect(repo.updateSet).toHaveBeenCalledWith('session','back',expect.objectContaining({loadRule:{basis:'performed_weight',referenceSetId:'top',percent:90}}),'session'));
});
test('95 performed previews 85.5 while the manual override removes the rule',async()=>{
  repo.getSession.mockResolvedValue({...initial,performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:2,performedAt:initial.startedAt,advancedAt:initial.startedAt}]});
  const view=render(<SessionSetEditor sessionId="session" setId="back"/>);await view.findByText('85,5 kg');
  fireEvent.press(view.getByRole('button',{name:'Remplacer par une charge manuelle'}));
  expect(view.getByLabelText('Charge cible (kg)').props.value).toBe('85.5');fireEvent.changeText(view.getByLabelText('Charge cible (kg)'),'82,5');
  fireEvent.press(view.getByRole('button',{name:'Enregistrer les objectifs'}));
  await waitFor(()=>expect(repo.updateSet).toHaveBeenCalledWith('session','back',expect.objectContaining({loadRule:null,targetWeightKg:82.5}),'session'));
});
test('an addition write failure preserves the draft and retry reuses the same intent key',async()=>{
  repo.addSet.mockRejectedValueOnce(new Error('Stockage indisponible'));const view=render(<SessionSetEditor sessionId="session" adding/>);
  await view.findByRole('radio',{name:'Barre'});fireEvent.changeText(view.getByLabelText('Nom de la série (facultatif)'),'À garder');
  fireEvent.press(view.getByRole('button',{name:'Ajouter la série'}));await view.findByText('Stockage indisponible');expect(router.dismissTo).not.toHaveBeenCalled();
  expect(view.getByLabelText('Nom de la série (facultatif)').props.value).toBe('À garder');fireEvent.press(view.getByRole('button',{name:'Ajouter la série'}));
  await waitFor(()=>expect(repo.addSet).toHaveBeenCalledTimes(2));expect(repo.addSet.mock.calls.map(call=>call[4])).toEqual(['addition-intent','addition-intent']);
});
test('removing an added series requires confirmation; cancellation does not touch data',async()=>{
  repo.getSession.mockResolvedValue({...initial,sets:[{...top,addition:{key:'extra',scope:'session',addedAt:initial.startedAt}},back]});
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{});const view=render(<SessionSetEditor sessionId="session" setId="top"/>);
  fireEvent.press(await view.findByRole('button',{name:'Retirer la série ajoutée'}));
  act(()=>{alert.mock.calls[0]![2]!.find(b=>b.text==='Annuler')!.onPress!();});expect(repo.deleteAddedSet).not.toHaveBeenCalled();
  fireEvent.press(view.getByRole('button',{name:'Retirer la série ajoutée'}));act(()=>{alert.mock.calls[1]![2]!.find(b=>b.style==='destructive')!.onPress!();});
  await waitFor(()=>expect(repo.deleteAddedSet).toHaveBeenCalledTimes(1));
});
test('a validated series exposes no save or remove action',async()=>{
  repo.getSession.mockResolvedValue({...initial,sets:[{...top,addition:{key:'extra',scope:'session',addedAt:initial.startedAt}},back],performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:null,performedAt:initial.startedAt,advancedAt:initial.startedAt}]});
  const view=render(<SessionSetEditor sessionId="session" setId="top"/>);await view.findByText(/Cette série n’est pas modifiable/);
  expect(view.queryByRole('button',{name:'Enregistrer les objectifs'})).toBeNull();expect(view.queryByRole('button',{name:'Retirer la série ajoutée'})).toBeNull();
});
test('personal exercise notes save independently and a failed save keeps the editor open',async()=>{
  repo.savePersonalNote.mockRejectedValueOnce(new Error('Erreur de note'));const view=render(<SessionNotes sessionId="session"/>);
  fireEvent.press(await view.findByRole('radio',{name:'1. Barre'}));fireEvent.changeText(view.getByLabelText('Note personnelle'),'Réduire la charge');
  fireEvent.press(view.getByRole('button',{name:'Enregistrer la note'}));await view.findByText('Erreur de note');expect(router.dismissTo).not.toHaveBeenCalled();
  fireEvent.press(view.getByRole('button',{name:'Enregistrer la note'}));await waitFor(()=>expect(repo.savePersonalNote).toHaveBeenLastCalledWith('session','Réduire la charge','exercise'));
});
test('the summary displays personal notes with the real exercise identity and no fictional performance',async()=>{
  const view=render(<SessionSummaryView session={{...initial,status:'completed',finishedAt:'2026-10-16T12:30:00Z',personalNote:'Bonne énergie',exerciseNotes:{exercise:'Repère personnel'},performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:0,performedAt:initial.startedAt,advancedAt:initial.startedAt}]}} onExit={()=>{}} onRetry={()=>{}}/>);
  expect(view.getByText('Bonne énergie')).toBeTruthy();expect(view.getByText('Repère personnel')).toBeTruthy();expect(view.getByText('95 kg · 8 reps · RIR 0')).toBeTruthy();
  expect(view.queryByText('100 kg · 8 reps')).toBeNull();
});

test('the active position counter uses the retained list after an extra set is removed, preserving stable series numbers',async()=>{
  const extra={...top,id:'extra',seriesIndex:3,sortOrder:3,label:'Bonus',addition:{key:'bonus',scope:'session' as const,addedAt:initial.startedAt}};
  repo.getSession.mockResolvedValue({...initial,sets:[top,extra],performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:null,performedAt:initial.startedAt,advancedAt:initial.startedAt}]});
  const view=render(<SessionScreen sessionId="session"/>);await view.findByText('Bonus · 2 / 2');
  expect(view.queryByText('Bonus · 4 / 2')).toBeNull();expect(view.getByText('1 / 2 séries validées')).toBeTruthy();
});


function skipped(session: WorkoutSession, ids: string[]): WorkoutSession {
  return { ...session, sets: session.sets.map(series => ids.includes(series.id) ? { ...series, skippedAt: session.startedAt, passageRevision: 1 } : series) };
}
function confirmPassage(alert: ReturnType<typeof jest.spyOn>) {
  const call = alert.mock.calls.at(-1) as unknown as Parameters<typeof Alert.alert>;
  const apply = call[2]!.find(button => button.text === 'Passer cette série')!.onPress!;
  act(() => apply());
  return apply;
}

test('Passer cette série is secondary, native cancellation is inert and a late cancelled confirmation cannot write',async()=>{
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{}),view=render(<SessionScreen sessionId="session"/>);
  await view.findByRole('button',{name:'Valider la série'});
  fireEvent.press(view.getByRole('button',{name:'Passer cette série'}));
  expect(alert).toHaveBeenCalledWith('Passer cette série',"Passer cette série pour aujourd'hui ? Elle restera dans votre programme.",expect.any(Array),expect.anything());
  const old=alert.mock.calls[0]![2]!;act(()=>{old.find(b=>b.text==='Annuler')!.onPress!();});act(()=>{old.find(b=>b.text==='Passer cette série')!.onPress!();});
  expect(repo.skipSet).not.toHaveBeenCalled();expect(repo.validateSet).not.toHaveBeenCalled();
  expect(view.getByRole('button',{name:'Valider la série'}).props.accessibilityState.disabled).toBe(false);
});
test('confirmed skip captures one exact series, ignores duplicate callbacks and displays passed / remaining honestly',async()=>{
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{}),pending=deferred<WorkoutSession>();repo.skipSet.mockReturnValue(pending.promise);
  const view=render(<SessionScreen sessionId="session"/>);await view.findByLabelText('Répétitions réelles');
  fireEvent.changeText(view.getByLabelText('Charge réelle (kg)'),'95');fireEvent.changeText(view.getByLabelText('Répétitions réelles'),'10');
  fireEvent.press(view.getByRole('button',{name:'Passer cette série'}));const apply=confirmPassage(alert);act(()=>apply());
  expect(repo.skipSet).toHaveBeenCalledTimes(1);expect(repo.skipSet).toHaveBeenCalledWith('session','top',0);expect(repo.validateSet).not.toHaveBeenCalled();
  await act(async()=>{pending.resolve(skipped(initial,['top']));await pending.promise;});
  await view.findByText('0 série réalisée · 1 passée · 2 restantes');expect(view.getByText('Top · Passée')).toBeTruthy();
  expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('');
  expect(view.getByText('La série de référence est passée. Utilisez « Réintégrer la série » ou choisissez une charge manuelle.')).toBeTruthy();
  act(()=>apply());expect(repo.skipSet).toHaveBeenCalledTimes(1);
});
test('a failed passage preserves current actual draft and allows retry without navigation',async()=>{
  repo.skipSet.mockRejectedValueOnce(new Error('Impossible de sauvegarder le passage'));
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{}),view=render(<SessionScreen sessionId="session"/>);
  await view.findByLabelText('Charge réelle (kg)');fireEvent.changeText(view.getByLabelText('Charge réelle (kg)'),'95');
  fireEvent.press(view.getByRole('button',{name:'Passer cette série'}));confirmPassage(alert);await view.findByText('Impossible de sauvegarder le passage');
  expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('95');expect(router.dismissTo).not.toHaveBeenCalled();
  fireEvent.press(view.getByRole('button',{name:'Passer cette série'}));confirmPassage(alert);await waitFor(()=>expect(repo.skipSet).toHaveBeenCalledTimes(2));await view.findByText('Top · Passée');
});
test('a native confirmation from a departed screen never changes a series',async()=>{
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{}),view=render(<SessionScreen sessionId="session"/>);
  fireEvent.press(await view.findByRole('button',{name:'Passer cette série'}));const apply=alert.mock.calls[0]![2]!.find(b=>b.text==='Passer cette série')!.onPress!;
  view.unmount();act(()=>apply());expect(repo.skipSet).not.toHaveBeenCalled();
});
test('another remaining series can be explicitly selected and passed without saving unsaved goals or touching the program',async()=>{
  const alert=jest.spyOn(Alert,'alert').mockImplementation(()=>{}),view=render(<SessionSetEditor sessionId="session" setId="top"/>);
  fireEvent.press(await view.findByRole('button',{name:'Choisir une autre série restante'}));fireEvent.press(view.getByRole('radio',{name:'Barre · Back'}));
  await view.findByText('En attente de la série de référence');fireEvent.changeText(view.getByLabelText('Nom de la série (facultatif)'),'Brouillon non enregistré');
  fireEvent.press(view.getByRole('button',{name:'Passer cette série'}));confirmPassage(alert);
  await waitFor(()=>expect(repo.skipSet).toHaveBeenCalledWith('session','back',0));expect(repo.updateSet).not.toHaveBeenCalled();expect(repo.deleteAddedSet).not.toHaveBeenCalled();
  await waitFor(()=>expect(router.dismissTo).toHaveBeenCalledWith({pathname:'/sessions/[sessionId]',params:{sessionId:'session'}}));
});
test('Réintégrer la série uses its own revision and is locked against rapid taps',async()=>{
  repo.getSession.mockResolvedValue(skipped(initial,['back']));const pending=deferred<WorkoutSession>();repo.reintegrateSet.mockReturnValue(pending.promise);
  const view=render(<SessionScreen sessionId="session"/>);const button=await view.findByRole('button',{name:'Réintégrer la série'});
  fireEvent.press(button);fireEvent.press(button);expect(repo.reintegrateSet).toHaveBeenCalledTimes(1);expect(repo.reintegrateSet).toHaveBeenCalledWith('session','back',1);
  await act(async()=>{pending.resolve(initial);await pending.promise;});await waitFor(()=>expect(view.queryByText('Back · Passée')).toBeNull());
  expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('');expect(repo.validateSet).not.toHaveBeenCalled();
});
test('a reintegration write error leaves the passed series visible with a retryable action',async()=>{
  repo.getSession.mockResolvedValue(skipped(initial,['back']));repo.reintegrateSet.mockRejectedValueOnce(new Error('Réintégration non enregistrée'));
  const view=render(<SessionScreen sessionId="session"/>);fireEvent.press(await view.findByRole('button',{name:'Réintégrer la série'}));
  await view.findByText('Réintégration non enregistrée');expect(view.getByText('Back · Passée')).toBeTruthy();expect(view.getByRole('button',{name:'Réintégrer la série'}).props.accessibilityState.disabled).toBe(false);
});
test('an open paused rest stays visible when every next series is skipped and ends only by its manual action',async()=>{
  const running:WorkoutSession={...skipped(initial,['back','other-set']),performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:0,performedAt:initial.startedAt,advancedAt:null}],rests:[{id:'rest',sessionId:'session',performedSetId:'p',plannedSeconds:60,startedAt:initial.startedAt,endedAt:null,chronologicalMs:null,activeMs:null,pauses:[{id:'pause',startedAt:initial.startedAt,endedAt:null}]}]};
  repo.getSession.mockResolvedValue(running);repo.completeRest.mockResolvedValue({...running,performances:running.performances.map(p=>({...p,advancedAt:initial.startedAt})),rests:running.rests.map(r=>({...r,endedAt:initial.startedAt,chronologicalMs:0,activeMs:0}))});
  const view=render(<SessionScreen sessionId="session"/>);await view.findByText('Aucune série restante. Votre repos continue jusqu’à votre fin manuelle.');
  const props=jest.mocked(RestTimer).mock.calls.at(-1)![0];expect(props.rest).toEqual(running.rests[0]);expect(props.showAction).toBe(false);
  expect(repo.completeRest).not.toHaveBeenCalled();expect(view.queryByRole('button',{name:'Terminer la séance'})).toBeNull();
  fireEvent.press(view.getByRole('button',{name:'Terminer le repos'}));await view.findByRole('button',{name:'Terminer la séance'});
  expect(repo.completeRest).toHaveBeenCalledWith('session','rest');expect(repo.finishSession).not.toHaveBeenCalled();
});
test('reintegration during rest retains the same timer and restores its standard manual continuation',async()=>{
  const resting:WorkoutSession={...skipped({...initial,sets:[top,back]},['back']),performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:0,performedAt:initial.startedAt,advancedAt:null}],rests:[{id:'rest',sessionId:'session',performedSetId:'p',plannedSeconds:60,startedAt:initial.startedAt,endedAt:null,chronologicalMs:null,activeMs:null,pauses:[]}]};
  repo.getSession.mockResolvedValue(resting);repo.reintegrateSet.mockResolvedValue({...resting,sets:[top,back]});const view=render(<SessionScreen sessionId="session"/>);
  fireEvent.press(await view.findByRole('button',{name:'Réintégrer la série'}));await waitFor(()=>expect(jest.mocked(RestTimer).mock.calls.at(-1)![0].showAction).toBe(true));
  expect(jest.mocked(RestTimer).mock.calls.at(-1)![0].rest).toEqual(resting.rests[0]);expect(repo.completeRest).not.toHaveBeenCalled();
});
test('all passed series leave reintegration available but cannot falsely finish an empty workout',async()=>{
  repo.getSession.mockResolvedValue(skipped(initial,initial.sets.map(s=>s.id)));const view=render(<SessionScreen sessionId="session"/>);
  const finish=await view.findByRole('button',{name:'Terminer la séance'});expect(finish.props.accessibilityState.disabled).toBe(true);
  expect(view.getAllByRole('button',{name:'Réintégrer la série'})).toHaveLength(3);expect(view.queryByRole('button',{name:'Valider la série'})).toBeNull();
  fireEvent.press(finish);expect(repo.finishSession).not.toHaveBeenCalled();
});
test('completed historical detail presents skipped goals separately, with no reintegration or fabricated performance',async()=>{
  const completed:WorkoutSession={...skipped(initial,['back','other-set']),status:'completed',finishedAt:'2026-10-17T12:30:00Z',performances:[{id:'p',sessionId:'session',sessionSetId:'top',sortOrder:0,weightKg:95,reps:8,rir:0,performedAt:initial.startedAt,advancedAt:initial.startedAt}]};
  const view=render(<SessionSummaryView session={completed} historical onExit={()=>{}} onRetry={()=>{}}/>);
  expect(view.getByText('Back · Passée')).toBeTruthy();expect(view.getByText('95 kg · 8 reps · RIR 0')).toBeTruthy();
  expect(view.getByLabelText('Séries réalisées').props.children).toBe('1');expect(view.queryByRole('button',{name:'Réintégrer la série'})).toBeNull();
});
test('the editor explains a passed actual reference but keeps planned percentages usable',async()=>{
  repo.getSession.mockResolvedValue(skipped(initial,['top']));const view=render(<SessionSetEditor sessionId="session" setId="back"/>);
  await view.findByText('La série de référence est passée. Utilisez « Réintégrer la série » ou choisissez une charge manuelle.');
  expect(view.getByLabelText('Charge cible (kg)').props.value).toBe('');view.unmount();
  const planned={...back,loadRule:{...back.loadRule!,basis:'planned_target' as const,percent:50},targets:{...back.targets,targetWeightKg:50}};
  repo.getSession.mockResolvedValue(skipped({...initial,sets:[top,planned]},['top']));const other=render(<SessionSetEditor sessionId="session" setId="back"/>);
  await other.findByText('50 kg');expect(other.queryByText('La série de référence est passée. Utilisez « Réintégrer la série » ou choisissez une charge manuelle.')).toBeNull();
});


test('passed goals retain their actual load mode instead of presenting a per-dumbbell target as a total load',async()=>{
  repo.getSession.mockResolvedValue(skipped(initial,['other-set']));const view=render(<SessionScreen sessionId="session"/>);
  await view.findByText(/100 kg \/ haltère/);expect(view.getByText('Autre · Passée')).toBeTruthy();expect(repo.validateSet).not.toHaveBeenCalled();
});
