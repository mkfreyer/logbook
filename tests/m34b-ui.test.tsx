import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { router } from 'expo-router';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { SessionSet, WorkoutSession } from '../src/domain/session';
import { useSessions } from '../src/store/SessionProvider';
import { SessionSetEditor } from '../src/features/sessions/SessionSetEditor';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionNotes } from '../src/features/sessions/SessionNotes';
import { SessionSummaryView } from '../src/features/sessions/SessionSummaryView';

jest.mock('expo-router',()=>{const React=require('react'); return { router:{push:jest.fn(),dismissTo:jest.fn(),back:jest.fn(),canGoBack:jest.fn()}, useFocusEffect:(effect:()=>any)=>React.useEffect(effect,[effect]) };});
jest.mock('expo-crypto',()=>({randomUUID:()=> 'addition-intent'}));
jest.mock('../src/store/SessionProvider',()=>({useSessions:jest.fn()}));
jest.mock('../src/features/sessions/PreviousPerformanceCard',()=>({PreviousPerformanceCard:()=>null}));
jest.mock('../src/features/sessions/RestTimer',()=>({RestTimer:()=>null}));
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
  deleteAddedSet:jest.fn<SessionRepository['deleteAddedSet']>(),savePersonalNote:jest.fn<SessionRepository['savePersonalNote']>()};
beforeEach(()=>{jest.resetAllMocks(); repo.getSession.mockResolvedValue(initial);repo.canUpdateProgram.mockResolvedValue(true);repo.addSet.mockResolvedValue(initial);repo.updateSet.mockResolvedValue(initial);repo.savePersonalNote.mockResolvedValue(initial);repo.deleteAddedSet.mockResolvedValue(initial);
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
