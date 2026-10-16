import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { test } from 'node:test';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import type { Database } from '../src/db/types';
import type { SetTemplateInput, WeightMode } from '../src/domain/training';
import { selectSessionStep, type WorkoutSession } from '../src/domain/session';
import { summarizeSession } from '../src/domain/sessionSummary';
import { EXPORT_TABLES, writePersonalExport } from '../src/data/personalExport';
import { SqliteDatabase } from './helpers/SqliteDatabase';

const manual: SetTemplateInput = { kind: 'top_set', label: 'Top', repsMin: 8, repsMax: 10, targetWeightKg: 100, targetRir: 2, restAfterSec: 60, notes: 'Consigne' };
const actualRule = (id: string) => ({ basis: 'performed_weight' as const, referenceSetId: id, percent: 90 });
async function fixture(t: { after(fn: () => void): void }, mode: WeightMode = 'total') {
  const directory = mkdtempSync(join(tmpdir(),'logbook-m34b-')), path = join(directory,'logbook.db'), db = new SqliteDatabase(path);
  t.after(() => { db.close(); rmSync(directory,{recursive:true,force:true}); }); await initializeDatabase(db);
  let serial = 0, clock = Date.parse('2026-10-16T12:00:00Z');
  const id = () => `b-${++serial}`, now = () => new Date(clock += 1000).toISOString();
  const programs = new ProgramRepository(db,id,now), training = new TrainingRepository(db,id,now), sessions = new SessionRepository(db,id,now);
  const program = await programs.createProgram({name:'Test personnel'}), workout = await programs.createWorkout(program.id,{name:'Séance'});
  const catalog = await training.createCustomExercise({name:'Exercice réel',muscleGroup:'Dos',equipment:'Salle',weightMode:mode});
  const exercise = await training.addWorkoutExercise(workout.id,{exerciseId:catalog.id});
  const top = await training.createSet(exercise.id,manual);
  const back = await training.createSet(exercise.id,{...manual,kind:'back_off',label:'Back',loadRule:actualRule(top.id)});
  const other = await training.addWorkoutExercise(workout.id,{exerciseId:(await training.listCatalog()).find(e => e.id!==catalog.id)!.id});
  await training.createSet(other.id,{...manual,kind:'work',label:'Autre'});
  return {db,path,id,now,programs,training,sessions,program,workout,exercise,top,back,other};
}
async function advance(sessions: SessionRepository, session: WorkoutSession) {
  const step = selectSessionStep(session);
  if (step.phase==='rest') return sessions.completeRest(session.id,step.rest.id);
  if (step.phase==='between_sets') return sessions.advanceAfterSet(session.id,step.performed.id);
  return session;
}
async function capture(db: SqliteDatabase) {
  const tables = await db.getAllAsync<{name:string}>("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name");
  return Promise.all(tables.map(async ({name})=>({name,columns:(await db.getAllAsync<{name:string}>(`PRAGMA table_info(${name})`)).map(c=>c.name),rows:await db.getAllAsync(`SELECT * FROM ${name} ORDER BY rowid`)})));
}

for (const mode of ['total','per_hand','additional'] as const) test(`100 planned, 95 performed yields 85.5 proposed in ${mode}, originals and actual fields stay distinct`, async t => {
  const f=await fixture(t,mode); assert.equal(f.back.targetWeightKg,null); assert.equal(f.back.loadRule?.basis,'performed_weight');
  let session=await f.sessions.startOrResume(f.workout.id); const top=session.sets[0]!, back=session.sets[1]!;
  assert.equal(back.targets.targetWeightKg,null); assert.equal(back.loadRuleSnapshot?.referenceWeightKg,null);
  assert.equal(back.loadRule?.referenceSetId,top.id);
  session=await f.sessions.updateSet(session.id,top.id,{...manual,targetWeightKg:105},'session');
  session=await f.sessions.validateSet(session.id,top.id,{weightKg:95,reps:9,rir:1});
  assert.equal(session.sets[1]!.targets.targetWeightKg,85.5); assert.deepEqual(session.sets[1]!.originalTargets,back.originalTargets);
  assert.deepEqual(session.sets[1]!.loadRuleSnapshot,back.loadRuleSnapshot); assert.equal(session.performances.length,1);
  const applied=session.adjustments!.find(a=>a.action==='resolve')!;
  assert.equal(applied.payload.referenceWeightKg,95); assert.equal(applied.payload.resolvedWeightKg,85.5);
  assert.equal(applied.payload.referencePerformanceId,session.performances[0]!.id);
  assert.equal((await f.training.getSet(f.top.id)).targetWeightKg,100);
});
for (const weightKg of [null,0]) test(`actual reference ${weightKg} is preserved without treating absence as zero`, async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg,reps:8,rir:null});
  assert.equal(s.sets[1]!.targets.targetWeightKg,weightKg===null?null:0);
  assert.equal(s.performances[0]!.weightKg,weightKg);
});
test('a manual override is not overwritten when its reference is subsequently validated', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const back=s.sets[1]!;
  s=await f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',label:'Manuel',targetWeightKg:82,loadRule:null},'session');
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:2});
  assert.equal(s.sets[1]!.targets.targetWeightKg,82); assert.equal(s.sets[1]!.loadRule,undefined);
  assert.deepEqual(s.sets[1]!.loadRuleSnapshot,back.loadRuleSnapshot);
});
test('planned percentages remain separate and never use the performed reference weight', async t => {
  const f=await fixture(t); await f.training.updateSet(f.back.id,{...manual,kind:'back_off',loadRule:{basis:'planned_target',referenceSetId:f.top.id,percent:90}});
  let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:null}); assert.equal(s.sets[1]!.targets.targetWeightKg,90);
});
test('session-only additions persist all targets, notes, type and provenance without a fake template or actual performance', async t => {
  const f=await fixture(t); const s=await f.sessions.startOrResume(f.workout.id), exercise=s.exercises[0]!;
  const updated=await f.sessions.addSet(s.id,exercise.id,{...manual,kind:'custom',label:'Bonus',repsMin:12,repsMax:15,targetWeightKg:null,notes:'Libre'},'session','bonus');
  const bonus=updated.sets.find(item=>item.addition)!; assert.equal(updated.sets.length,4); assert.equal(updated.performances.length,0);
  assert.equal(bonus.sourceSetTemplateId,null); assert.equal(bonus.kind,'custom'); assert.equal(bonus.label,'Bonus'); assert.equal(bonus.notes,'Libre');
  assert.deepEqual(bonus.targets,{repsMin:12,repsMax:15,targetWeightKg:null,targetRir:2,restAfterSec:60});
  assert.equal(bonus.addition!.scope,'session'); assert.equal((await f.training.listSets(f.exercise.id)).length,2);
  const db=new SqliteDatabase(f.path); t.after(()=>db.close());
  assert.deepEqual(await new SessionRepository(db,f.id).getActiveSession(),updated);
});
test('rapid duplicate addition tokens append one set to both execution and program', async t => {
  const f=await fixture(t); const s=await f.sessions.startOrResume(f.workout.id);
  const results=await Promise.all([1,2,3].map(()=>f.sessions.addSet(s.id,s.exercises[0]!.id,{...manual,label:'Bonus'},'program','same-intent')));
  assert.ok(results.every(item=>item.sets.length===4)); assert.equal((await f.training.listSets(f.exercise.id)).length,3);
  const bonus=results[0]!.sets.find(item=>item.addition)!; assert.equal(bonus.addition!.scope,'program'); assert.ok(bonus.sourceSetTemplateId);
});
test('an addition during paused rest leaves the interval, timestamps and its original performed series identical', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:null}); s=await f.sessions.pauseRest(s.id,s.rests[0]!.id);
  const rest=s.rests[0]!, performed=s.performances[0]!;
  s=await f.sessions.addSet(s.id,s.exercises[1]!.id,{...manual,restAfterSec:180},'session','during-rest');
  assert.deepEqual(s.rests[0],rest); assert.deepEqual(s.performances[0],performed); assert.equal(selectSessionStep(s).phase,'rest');
  s=await f.sessions.completeRest(s.id,rest.id); assert.equal(s.rests.length,1); assert.ok(s.rests[0]!.chronologicalMs!>=s.rests[0]!.activeMs!);
});
test('adding after the last validation reopens the remaining path without a retrospective rest', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  while(selectSessionStep(s).phase!=='ready_to_finish') {
    const step=selectSessionStep(s); if(step.phase==='set')s=await f.sessions.validateSet(s.id,step.set.id,{weightKg:10,reps:8,rir:null}); else s=await advance(f.sessions,s);
  }
  const before=structuredClone(s); s=await f.sessions.addSet(s.id,s.exercises[0]!.id,{...manual,label:'Extra finale'},'session','last-extra');
  assert.equal(selectSessionStep(s).phase,'set'); assert.deepEqual(s.performances,before.performances); assert.deepEqual(s.rests,before.rests);
  await assert.rejects(f.sessions.finishSession(s.id),/toutes les séries/);
  const step=selectSessionStep(s); if(step.phase!=='set')throw new Error('set');
  s=await f.sessions.validateSet(s.id,step.set.id,{weightKg:12,reps:7,rir:0}); s=await f.sessions.finishSession(s.id);
  assert.equal(s.performances.length,4); assert.deepEqual(s.rests,before.rests);
});
test('any remaining series can be edited with an explicit scope, but performed targets/results remain protected', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const initial=structuredClone(s);
  s=await f.sessions.updateSet(s.id,s.sets[1]!.id,{...manual,kind:'custom',label:'Différée',notes:'Note',loadRule:null},'program');
  assert.equal(s.sets[1]!.editScope,'program'); assert.equal((await f.training.getSet(f.back.id)).label,'Différée');
  assert.deepEqual(s.sets[1]!.originalTargets,initial.sets[1]!.originalTargets);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:1}); const performed=structuredClone(s.performances);
  await assert.rejects(f.sessions.updateSet(s.id,s.sets[0]!.id,manual,'session'),/déjà validée/);
  assert.deepEqual((await f.sessions.getSession(s.id))!.performances,performed);
});
test('current rules accept explicit planned or actual references and program scope updates the future only', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const back=s.sets[1]!, top=s.sets[0]!;
  s=await f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',loadRule:{basis:'planned_target',referenceSetId:top.id,percent:80}},'program');
  assert.equal(s.sets[1]!.targets.targetWeightKg,80); assert.equal((await f.training.getSet(f.back.id)).loadRule!.referenceSetId,f.top.id);
  assert.equal(s.sets[1]!.loadRuleSnapshot!.basis,'performed_weight');
  s=await f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',loadRule:actualRule(top.id)},'program');
  assert.equal(s.sets[1]!.targets.targetWeightKg,null); assert.equal((await f.training.getSet(f.back.id)).loadRule!.basis,'performed_weight');
});
test('explicit order choices resolve by stable IDs and do not affect the original exercise program', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const top=s.sets[0]!, other=s.exercises[1]!;
  s=await f.sessions.chooseNextExercise(s.id,other.id,top.id); let step=selectSessionStep(s); assert.equal(step.phase,'set');
  if(step.phase!=='set')throw new Error('set'); s=await f.sessions.validateSet(s.id,step.set.id,{weightKg:5,reps:9,rir:null}); s=await advance(f.sessions,s);
  s=await f.sessions.validateSet(s.id,top.id,{weightKg:95,reps:8,rir:null});
  assert.equal(s.sets[1]!.targets.targetWeightKg,85.5); assert.deepEqual(s.performances.map(p=>p.sessionSetId),[s.sets[2]!.id,top.id]);
});
test('an already performed dependent keeps its missing target when the reference is executed later', async t => {
  const f=await fixture(t); await f.training.reorderSets(f.exercise.id,[f.back.id,f.top.id]);
  let s=await f.sessions.startOrResume(f.workout.id); const dependent=s.sets[0]!, ref=s.sets[1]!;
  s=await f.sessions.validateSet(s.id,dependent.id,{weightKg:80,reps:8,rir:0}); s=await advance(f.sessions,s);
  s=await f.sessions.validateSet(s.id,ref.id,{weightKg:95,reps:8,rir:null});
  assert.equal(s.sets[0]!.targets.targetWeightKg,null); assert.equal(s.performances[0]!.weightKg,80);
});
test('replacement suspends incompatible rules, keeps performed identity and disables program changes', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const top=s.sets[0]!;
  s=await f.sessions.validateSet(s.id,top.id,{weightKg:95,reps:8,rir:null}); s=await advance(f.sessions,s);
  const step=selectSessionStep(s); if(step.phase!=='set')throw new Error('set');
  const replacement=await f.training.createCustomExercise({name:'Haltères',muscleGroup:'Dos',equipment:'Haltères',weightMode:'per_hand'});
  s=await f.sessions.replaceExercise(s.id,step.exercise.id,replacement.id,step.set.id);
  const back=s.sets[1]!; assert.equal(back.targets.targetWeightKg,null); assert.equal(back.loadRule!.suspended,true);
  assert.equal(s.sets[0]!.sessionExerciseId,top.sessionExerciseId); assert.equal(await f.sessions.canUpdateProgram(s.id,back.sessionExerciseId),false);
  await assert.rejects(f.sessions.addSet(s.id,back.sessionExerciseId,manual,'program','bad-program'),/Cette séance/);
  s=await f.sessions.addSet(s.id,back.sessionExerciseId,manual,'session','safe-replacement'); assert.equal(s.performances.length,1);
});
test('cross-exercise, self, chains, invalid percentages and incompatible top-set references are rejected atomically', async t => {
  const f=await fixture(t); const s=await f.sessions.startOrResume(f.workout.id), back=s.sets[1]!, top=s.sets[0]!;
  for (const referenceSetId of [back.id,s.sets[2]!.id,'missing']) await assert.rejects(f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',loadRule:actualRule(referenceSetId)},'session'));
  await assert.rejects(f.sessions.updateSet(s.id,top.id,{...manual,kind:'warmup',loadRule:actualRule(back.id)},'session'));
  await assert.rejects(f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',loadRule:{...actualRule(top.id),percent:0}},'session'));
  assert.deepEqual(await f.sessions.getSession(s.id),s);
});
test('unperformed extra removal preserves program additions, original sets and retry idempotence', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','remove-me'); const extra=s.sets.find(i=>i.addition)!;
  s=await f.sessions.deleteAddedSet(s.id,extra.id); assert.equal(s.sets.length,3); assert.equal((await f.training.listSets(f.exercise.id)).length,3);
  assert.deepEqual(await f.sessions.deleteAddedSet(s.id,extra.id),s);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','remove-me'); assert.equal(s.sets.length,3);
  await assert.rejects(f.sessions.deleteAddedSet(s.id,s.sets[0]!.id),/ajoutée non validée/);
});
test('a validated added set cannot be removed or edited', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'session','performed-extra'); const extra=s.sets.find(i=>i.addition)!;
  while(!s.performances.some(p=>p.sessionSetId===extra.id)) { const step=selectSessionStep(s); if(step.phase==='set')s=await f.sessions.validateSet(s.id,step.set.id,{weightKg:20,reps:8,rir:null}); else s=await advance(f.sessions,s); }
  await assert.rejects(f.sessions.deleteAddedSet(s.id,extra.id),/non validée/);
  await assert.rejects(f.sessions.updateSet(s.id,extra.id,manual,'session'),/déjà validée/);
});
test('deleting the source program cannot erase execution additions, applied targets or notes', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','survive'); s=await f.sessions.savePersonalNote(s.id,'Énergie');
  await f.programs.deleteProgram(f.program.id); assert.deepEqual(await f.sessions.getSession(s.id),s);
  await assert.rejects(f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','missing'),/Cette séance/);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'session','still-safe'); assert.equal(s.sets.length,5);
});
test('notes are independent of template instructions, editable after completion and leave performance/rests unchanged', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  while(selectSessionStep(s).phase!=='ready_to_finish') { const step=selectSessionStep(s); if(step.phase==='set')s=await f.sessions.validateSet(s.id,step.set.id,{weightKg:10,reps:8,rir:null}); else s=await advance(f.sessions,s); }
  s=await f.sessions.finishSession(s.id); const before=structuredClone(s);
  s=await f.sessions.savePersonalNote(s.id,'Bonne énergie'); s=await f.sessions.savePersonalNote(s.id,'Réduire la charge',s.exercises[0]!.id);
  assert.equal(s.personalNote,'Bonne énergie'); assert.equal(s.exerciseNotes![s.exercises[0]!.id],'Réduire la charge');
  assert.deepEqual(s.performances,before.performances); assert.deepEqual(s.rests,before.rests); assert.deepEqual(s.sets,before.sets);
  assert.deepEqual(summarizeSession(s),summarizeSession(before));
  await assert.rejects(f.sessions.savePersonalNote(s.id,'Non','another-session-exercise'));
});
test('a failed atomic program addition or reference resolution rolls everything back and retry stays safe', async t => {
  const f=await fixture(t); const s=await f.sessions.startOrResume(f.workout.id), before=await capture(f.db);
  await f.db.execAsync("CREATE TRIGGER storage_failure BEFORE INSERT ON session_set_adjustments BEGIN SELECT RAISE(ABORT,'disk full'); END;");
  await assert.rejects(f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','retry'),/disk full/);
  await assert.rejects(f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:null}),/disk full/);
  assert.deepEqual(await capture(f.db),before); await f.db.execAsync('DROP TRIGGER storage_failure');
  const updated=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'program','retry'); assert.equal(updated.sets.length,4);
});
test('a populated released v6 database migrates without changing any old column or active paused rest', async t => {
  const db=new SqliteDatabase(); t.after(()=>db.close()); await db.execAsync(readFileSync(new URL('./fixtures/m34a-populated-v6.sql',import.meta.url),'utf8'));
  const before=await capture(db), saved=JSON.parse(readFileSync(new URL('./fixtures/m34a-populated-snapshots.json',import.meta.url),'utf8'));
  await initializeDatabase(db); await initializeDatabase(db);
  for(const table of before) assert.deepEqual(await db.getAllAsync(`SELECT ${table.columns.join(',')} FROM ${table.name} ORDER BY rowid`),table.rows,table.name);
  const repo=new SessionRepository(db,()=> 'unused'); assert.deepEqual(await repo.getSession(saved.active.id),saved.active); assert.deepEqual(await repo.getSession(saved.completed.id),saved.completed);
  assert.equal((await db.getFirstAsync<{user_version:number}>('PRAGMA user_version'))!.user_version,DATABASE_VERSION);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'),[]);
});
test('failed v7 migration is fully rolled back, preserves v6 and can be retried', async t => {
  const db=new SqliteDatabase(); t.after(()=>db.close()); await db.execAsync(readFileSync(new URL('./fixtures/m34a-populated-v6.sql',import.meta.url),'utf8'));
  const before=await capture(db), exec=db.execAsync.bind(db);
  db.execAsync=async sql=>{ await exec(sql); if(sql.includes('CREATE TABLE session_personal_notes'))throw new Error('migration full'); };
  await assert.rejects(initializeDatabase(db),/migration full/); assert.deepEqual(await capture(db),before);
  assert.equal((await db.getFirstAsync<{user_version:number}>('PRAGMA user_version'))!.user_version,6);
  db.execAsync=exec; await initializeDatabase(db);
});
test('export includes all current rules, additions, scopes, notes and immutable originals, without a write', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  s=await f.sessions.addSet(s.id,s.exercises[0]!.id,{...manual,kind:'back_off',loadRule:actualRule(s.sets[0]!.id)},'session','export');
  s=await f.sessions.savePersonalNote(s.id,'Personnel'); s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:1});
  const before=await capture(f.db), reader=new SqliteDatabase(f.path); t.after(()=>reader.close()); let json='';
  await writePersonalExport(reader,chunk=>{json+=chunk;},{appVersion:'0.1.0'}); const file=JSON.parse(json);
  assert.equal(file.sqliteSchemaVersion,7); assert.equal(file.restorationAvailableInExporter,false);
  for(const [name] of EXPORT_TABLES) assert.equal(file.tables[name].rowCount,before.find(t=>t.name===name)!.rows.length);
  assert.equal(file.tables.session_personal_notes.rows[0].body,'Personnel');
  assert.ok(file.tables.session_set_adjustments.rows.some((a:any)=>JSON.parse(a.payload).resolvedWeightKg===85.5));
  assert.deepEqual(await capture(f.db),before);
});
test('exclusive Expo-style transactions with FK disabled still reject missing sources and persist valid additions', async t => {
  const f=await fixture(t), exclusive=Object.create(f.db) as Database;
  exclusive.withExclusiveTransactionAsync=async task=>{const connection=new SqliteDatabase(f.path); await connection.execAsync('PRAGMA foreign_keys=OFF');
    try{await connection.withTransactionAsync(()=>task(connection));}finally{connection.close();}};
  const repo=new SessionRepository(exclusive,f.id,f.now); let s=await repo.startOrResume(f.workout.id);
  await assert.rejects(repo.addSet(s.id,'missing',manual,'session','bad'));
  await assert.rejects(repo.addSet(s.id,s.exercises[0]!.id,{...manual,kind:'back_off',loadRule:actualRule('missing')},'program','bad-rule'));
  s=await repo.addSet(s.id,s.exercises[0]!.id,manual,'program','good'); assert.equal(s.sets.length,4);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'),[]);
});

test('all five kinds can be explicitly added, with exact/range and independent rests, without performing them', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id);
  for(const [i,kind] of (['work','warmup','top_set','back_off','custom'] as const).entries()) {
    s=await f.sessions.addSet(s.id,s.exercises[0]!.id,{...manual,kind,label:`Bonus ${kind}`,repsMin:5,repsMax:i%2?8:5,restAfterSec:i*30,targetWeightKg:i%2?null:0,notes:`Note ${kind}`},'session',`kind-${kind}`);
  }
  assert.equal(s.sets.length,8); assert.equal(s.performances.length,0); assert.deepEqual(s.sets.filter(i=>i.addition).map(i=>i.targets.restAfterSec),[0,30,60,90,120]);
});
test('original metadata, performed rules and the actual performance remain immutable at SQLite level', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); const back=s.sets[1]!;
  const before=(await f.db.getFirstAsync<{initial_metadata:string}>('SELECT initial_metadata FROM session_sets WHERE id=?',back.id))!.initial_metadata;
  s=await f.sessions.updateSet(s.id,back.id,{...manual,kind:'back_off',label:'Nouveau nom',notes:'Nouvelle note',loadRule:actualRule(s.sets[0]!.id)},'session');
  assert.equal((await f.db.getFirstAsync<{initial_metadata:string}>('SELECT initial_metadata FROM session_sets WHERE id=?',back.id))!.initial_metadata,before);
  await assert.rejects(f.db.runAsync("UPDATE session_sets SET initial_metadata='{}' WHERE id=?",back.id),/immutable/);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:null});s=await advance(f.sessions,s);
  s=await f.sessions.validateSet(s.id,back.id,{weightKg:85,reps:8,rir:null});
  await assert.rejects(f.db.runAsync('DELETE FROM performed_sets WHERE session_set_id=?',back.id),/immutable/);
  await assert.rejects(f.db.runAsync('DELETE FROM session_set_load_rules WHERE session_set_id=?',back.id),/immutable/);
  await assert.rejects(f.db.runAsync('UPDATE session_set_load_rules SET suspended=1 WHERE session_set_id=?',back.id),/immutable/);
});
test('an export refuses inconsistent addition provenance without modifying a damaged database', async t => {
  const f=await fixture(t); let s=await f.sessions.startOrResume(f.workout.id); s=await f.sessions.addSet(s.id,s.exercises[0]!.id,manual,'session','corrupted');
  await f.db.execAsync('DROP TRIGGER preserve_addition_provenance'); await f.db.runAsync("UPDATE session_sets SET addition_scope='program' WHERE addition_key='corrupted'");
  const before=await capture(f.db), reader=new SqliteDatabase(f.path); t.after(()=>reader.close());
  await assert.rejects(writePersonalExport(reader,()=>{}, {appVersion:'0.1.0'}),/relation de série/); assert.deepEqual(await capture(f.db),before);
});

test('configuring an actual rule never evaluates an incompatible tiny planned weight as if it were an actual result', async t => {
  const f=await fixture(t); await f.training.updateSet(f.top.id,{...manual,targetWeightKg:Number.MIN_VALUE});
  await f.training.updateSet(f.back.id,{...manual,kind:'back_off',loadRule:{...actualRule(f.top.id),percent:1}});
  let s=await f.sessions.startOrResume(f.workout.id); assert.equal(s.sets[1]!.targets.targetWeightKg,null);
  s=await f.sessions.validateSet(s.id,s.sets[0]!.id,{weightKg:95,reps:8,rir:null}); assert.equal(s.sets[1]!.targets.targetWeightKg,0.95);
});
