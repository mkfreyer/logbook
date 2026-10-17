-- Generated with released M3.4A 7a079b4 repositories. Test fixture only.
PRAGMA foreign_keys=OFF;
CREATE TABLE programs (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 1000),
    sport_type TEXT NOT NULL DEFAULT 'musculation' CHECK(sport_type = 'musculation'),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );
CREATE TABLE workout_templates (
    id TEXT PRIMARY KEY NOT NULL,
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(program_id, sort_order)
  );
CREATE TABLE exercise_catalog (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    muscle_group TEXT NOT NULL CHECK(length(trim(muscle_group)) BETWEEN 1 AND 80),
    equipment TEXT NOT NULL CHECK(length(trim(equipment)) BETWEEN 1 AND 80),
    instructions TEXT NOT NULL DEFAULT '' CHECK(length(instructions) <= 1000),
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total', 'per_hand', 'additional')),
    is_custom INTEGER NOT NULL CHECK(is_custom IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );
CREATE TABLE workout_exercises (
    id TEXT PRIMARY KEY NOT NULL,
    workout_template_id TEXT NOT NULL REFERENCES workout_templates(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL REFERENCES exercise_catalog(id) ON DELETE RESTRICT,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_template_id, sort_order)
  );
CREATE TABLE set_templates (
    id TEXT PRIMARY KEY NOT NULL,
    workout_exercise_id TEXT NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    label TEXT NOT NULL DEFAULT '' CHECK(length(label) <= 80),
    kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real', 'integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_exercise_id, sort_order)
  );
CREATE TABLE workout_sessions (
    id TEXT PRIMARY KEY NOT NULL,
    source_workout_template_id TEXT NOT NULL,
    source_program_id TEXT NOT NULL,
    workout_name TEXT NOT NULL,
    program_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'completed')),
    started_at TEXT NOT NULL,
    finished_at TEXT, selected_exercise_id TEXT,
    CHECK((status = 'active' AND finished_at IS NULL) OR (status = 'completed' AND finished_at IS NOT NULL AND finished_at >= started_at))
  );
CREATE TABLE session_exercises (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    source_workout_exercise_id TEXT NOT NULL,
    source_catalog_exercise_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    name TEXT NOT NULL, muscle_group TEXT NOT NULL, equipment TEXT NOT NULL,
    instructions TEXT NOT NULL, notes TEXT NOT NULL,
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total', 'per_hand', 'additional')), planned_order INTEGER NOT NULL DEFAULT 0 CHECK(typeof(planned_order) = 'integer' AND planned_order >= 0),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id)
  );
CREATE TABLE session_sets (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_exercise_id TEXT NOT NULL,
    source_set_template_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    series_index INTEGER NOT NULL CHECK(typeof(series_index) = 'integer' AND series_index >= 0),
    label TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    notes TEXT NOT NULL,
    original_targets TEXT NOT NULL CHECK(json_valid(original_targets)),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real','integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400), load_rule_snapshot TEXT CHECK(load_rule_snapshot IS NULL OR json_valid(load_rule_snapshot)),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id),
    FOREIGN KEY(session_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE CASCADE
  );
CREATE TABLE performed_sets (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_set_id TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    weight_kg REAL CHECK(weight_kg IS NULL OR (typeof(weight_kg) IN ('real','integer') AND weight_kg >= 0 AND weight_kg <= 1.7976931348623157e308)),
    reps INTEGER NOT NULL CHECK(typeof(reps) = 'integer' AND reps >= 0),
    rir INTEGER CHECK(rir IS NULL OR (typeof(rir) = 'integer' AND rir BETWEEN 0 AND 10)),
    performed_at TEXT NOT NULL, advanced_at TEXT CHECK(advanced_at IS NULL OR advanced_at >= performed_at),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id),
    FOREIGN KEY(session_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE rest_intervals (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    performed_set_id TEXT NOT NULL UNIQUE,
    planned_seconds INTEGER NOT NULL CHECK(typeof(planned_seconds) = 'integer' AND planned_seconds BETWEEN 1 AND 86400),
    started_at TEXT NOT NULL, ended_at TEXT CHECK(ended_at IS NULL OR ended_at >= started_at),
    chronological_ms INTEGER CHECK(chronological_ms IS NULL OR (typeof(chronological_ms) = 'integer' AND chronological_ms >= 0)),
    active_ms INTEGER CHECK(active_ms IS NULL OR (typeof(active_ms) = 'integer' AND active_ms >= 0 AND active_ms <= chronological_ms)),
    CHECK((ended_at IS NULL AND chronological_ms IS NULL AND active_ms IS NULL) OR
      (ended_at IS NOT NULL AND chronological_ms IS NOT NULL AND active_ms IS NOT NULL)),
    FOREIGN KEY(performed_set_id, session_id) REFERENCES performed_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE rest_pauses (
    id TEXT PRIMARY KEY NOT NULL,
    rest_interval_id TEXT NOT NULL REFERENCES rest_intervals(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL, ended_at TEXT CHECK(ended_at IS NULL OR ended_at >= started_at)
  );
CREATE TABLE session_exercise_replacements (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    from_exercise_id TEXT NOT NULL,
    to_exercise_id TEXT NOT NULL,
    active_set_id TEXT NOT NULL,
    remaining_set_count INTEGER NOT NULL CHECK(typeof(remaining_set_count) = 'integer' AND remaining_set_count > 0),
    changed_at TEXT NOT NULL,
    CHECK(from_exercise_id != to_exercise_id),
    UNIQUE(session_id, from_exercise_id),
    UNIQUE(session_id, to_exercise_id),
    FOREIGN KEY(from_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(to_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(active_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE session_exercise_choices (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL,
    expected_set_id TEXT NOT NULL,
    chosen_at TEXT NOT NULL,
    FOREIGN KEY(exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(expected_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE app_preferences (
    key TEXT PRIMARY KEY NOT NULL CHECK(length(key) BETWEEN 1 AND 80),
    value_json TEXT NOT NULL CHECK(json_valid(value_json)),
    updated_at TEXT NOT NULL
  );
CREATE TABLE set_load_rules (
    set_template_id TEXT PRIMARY KEY NOT NULL REFERENCES set_templates(id) ON DELETE CASCADE,
    reference_set_id TEXT REFERENCES set_templates(id) ON DELETE SET NULL,
    percent REAL NOT NULL CHECK(typeof(percent) IN ('real', 'integer') AND percent > 0 AND percent <= 100),
    basis TEXT NOT NULL DEFAULT 'planned_target' CHECK(basis = 'planned_target')
  );
INSERT INTO programs (rowid,id,name,description,sport_type,created_at,updated_at) VALUES (1,'v6-1','Programme personnel v6','','musculation','2026-10-16T12:00:01.000Z','2026-10-16T12:00:01.000Z');
INSERT INTO workout_templates (rowid,id,program_id,name,notes,sort_order,created_at,updated_at) VALUES (1,'v6-2','v6-1','Séance conservée','',0,'2026-10-16T12:00:02.000Z','2026-10-16T12:00:02.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (1,'b459f856-f639-4cb2-9278-d7ac1e287a01','Développé couché barre','Pectoraux','Barre et banc','Gardez les pieds stables et les omoplates rapprochées. Descendez la barre de manière contrôlée puis poussez sans rebond.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (2,'b459f856-f639-4cb2-9278-d7ac1e287a02','Développé incliné haltères','Pectoraux','Haltères et banc incliné','Placez le banc en légère inclinaison. Descendez les haltères avec contrôle et poussez en conservant les épaules stables.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (3,'b459f856-f639-4cb2-9278-d7ac1e287a03','Pompes','Pectoraux','Poids du corps','Gardez le corps aligné et les abdominaux engagés. Pliez les coudes pour descendre puis poussez le sol. La charge cible indique un éventuel lest ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (4,'b459f856-f639-4cb2-9278-d7ac1e287a04','Tractions','Dos','Barre de traction','Depuis une suspension contrôlée, tirez le corps vers la barre sans balancer les jambes. Redescendez avec contrôle. La charge cible indique un éventuel lest ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (5,'b459f856-f639-4cb2-9278-d7ac1e287a05','Tirage vertical à la poulie','Dos','Poulie','Asseyez-vous avec le buste stable. Tirez la barre vers le haut de la poitrine et remontez sans laisser les épaules partir vers l’avant.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (6,'b459f856-f639-4cb2-9278-d7ac1e287a06','Rowing haltère','Dos','Haltère et banc','Prenez un appui stable sur le banc et gardez le dos neutre. Tirez le coude vers la hanche puis redescendez avec contrôle.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (7,'b459f856-f639-4cb2-9278-d7ac1e287a07','Squat barre','Quadriceps','Barre et rack','Gardez les pieds stables et le buste gainé. Descendez à une amplitude confortable en suivant la direction des pieds avec les genoux, puis remontez avec contrôle.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (8,'b459f856-f639-4cb2-9278-d7ac1e287a08','Presse à cuisses','Quadriceps','Machine','Réglez le siège pour conserver le bassin en appui. Fléchissez les jambes à une amplitude confortable puis poussez sans verrouiller brusquement les genoux. Indiquez la charge affichée par la machine.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (9,'b459f856-f639-4cb2-9278-d7ac1e287a09','Soulevé de terre roumain','Ischio-jambiers','Barre','Avec les genoux légèrement fléchis, reculez les hanches en gardant la barre près des jambes et le dos neutre. Revenez debout en poussant les hanches vers l’avant.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (10,'b459f856-f639-4cb2-9278-d7ac1e287a10','Leg curl assis','Ischio-jambiers','Machine','Réglez les appuis à votre taille. Fléchissez les genoux sans décoller le bassin puis revenez avec contrôle. Indiquez la charge affichée par la machine.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (11,'b459f856-f639-4cb2-9278-d7ac1e287a11','Développé épaules haltères','Épaules','Haltères','Gardez le buste stable et poussez les haltères au-dessus de la tête à une amplitude confortable. Redescendez avec contrôle sans cambrer excessivement.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (12,'b459f856-f639-4cb2-9278-d7ac1e287a12','Élévations latérales','Épaules','Haltères','Levez les bras sur les côtés avec les coudes légèrement fléchis. Arrêtez à une hauteur confortable et redescendez sans élan.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (13,'b459f856-f639-4cb2-9278-d7ac1e287a13','Curl haltères','Biceps','Haltères','Gardez les coudes près du buste et fléchissez les bras sans balancer le corps. Redescendez les haltères avec contrôle.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (14,'b459f856-f639-4cb2-9278-d7ac1e287a14','Extension triceps à la poulie','Triceps','Poulie','Gardez les coudes près du buste et étendez les bras vers le bas. Remontez avec contrôle sans déplacer les épaules.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (15,'b459f856-f639-4cb2-9278-d7ac1e287a15','Crunch au sol','Abdominaux','Poids du corps','Décollez légèrement les épaules en rapprochant le thorax du bassin, sans tirer sur la nuque. Revenez avec contrôle. La charge cible indique un éventuel poids ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (16,'v6-3','Barre personnelle','Pectoraux','Barre','','total',1,'2026-10-16T12:00:03.000Z','2026-10-16T12:00:03.000Z');
INSERT INTO workout_exercises (rowid,id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES (1,'v6-4','v6-2','v6-3',0,'','2026-10-16T12:00:04.000Z','2026-10-16T12:00:04.000Z');
INSERT INTO workout_exercises (rowid,id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES (2,'v6-7','v6-2','v6-3',1,'','2026-10-16T12:00:07.000Z','2026-10-16T12:00:07.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (1,'v6-5','v6-4',0,'Référence','top_set',8,10,100,NULL,60,'Consigne v6','2026-10-16T12:00:05.000Z','2026-10-16T12:00:05.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (2,'v6-6','v6-4',1,'','back_off',10,12,NULL,NULL,120,'','2026-10-16T12:00:06.000Z','2026-10-16T12:00:06.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (3,'v6-8','v6-7',0,'','work',5,5,NULL,NULL,0,'','2026-10-16T12:00:08.000Z','2026-10-16T12:00:08.000Z');
INSERT INTO workout_sessions (rowid,id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES (1,'v6-9','v6-2','v6-1','Séance conservée','Programme personnel v6','completed','2026-10-16T12:00:09.000Z','2026-10-16T12:00:17.000Z',NULL);
INSERT INTO workout_sessions (rowid,id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES (2,'v6-22','v6-2','v6-1','Séance conservée','Programme personnel v6','active','2026-10-16T12:00:18.000Z',NULL,NULL);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (1,'v6-10','v6-9','v6-4','v6-3',0,'Barre personnelle','Pectoraux','Barre','','','total',0);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (2,'v6-13','v6-9','v6-7','v6-3',1,'Barre personnelle','Pectoraux','Barre','','','total',1);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (3,'v6-23','v6-22','v6-4','v6-3',0,'Barre personnelle','Pectoraux','Barre','','','total',0);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (4,'v6-26','v6-22','v6-7','v6-3',1,'Barre personnelle','Pectoraux','Barre','','','total',1);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (1,'v6-11','v6-9','v6-10','v6-5',0,0,'Référence','top_set','Consigne v6','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":null,"restAfterSec":60}',8,10,100,NULL,60,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (2,'v6-12','v6-9','v6-10','v6-6',1,1,'','back_off','','{"repsMin":10,"repsMax":12,"targetWeightKg":90,"targetRir":null,"restAfterSec":120}',10,12,90,NULL,120,'{"basis":"planned_target","referenceSetTemplateId":"v6-5","percent":90,"referenceWeightKg":100,"resolvedWeightKg":90,"weightMode":"total"}');
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (3,'v6-14','v6-9','v6-13','v6-8',2,0,'','work','','{"repsMin":5,"repsMax":5,"targetWeightKg":null,"targetRir":null,"restAfterSec":0}',5,5,NULL,NULL,0,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (4,'v6-24','v6-22','v6-23','v6-5',0,0,'Référence','top_set','Consigne v6','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":null,"restAfterSec":60}',8,10,100,NULL,60,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (5,'v6-25','v6-22','v6-23','v6-6',1,1,'','back_off','','{"repsMin":10,"repsMax":12,"targetWeightKg":90,"targetRir":null,"restAfterSec":120}',10,12,90,NULL,120,'{"basis":"planned_target","referenceSetTemplateId":"v6-5","percent":90,"referenceWeightKg":100,"resolvedWeightKg":90,"weightMode":"total"}');
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot) VALUES (6,'v6-27','v6-22','v6-26','v6-8',2,0,'','work','','{"repsMin":5,"repsMax":5,"targetWeightKg":null,"targetRir":null,"restAfterSec":0}',5,5,NULL,NULL,0,NULL);
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (1,'v6-15','v6-9','v6-11',0,95,9,0,'2026-10-16T12:00:10.000Z','2026-10-16T12:00:12.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (2,'v6-18','v6-9','v6-12',1,NULL,9,NULL,'2026-10-16T12:00:13.000Z','2026-10-16T12:00:15.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (3,'v6-21','v6-9','v6-14',2,NULL,9,NULL,'2026-10-16T12:00:16.000Z','2026-10-16T12:00:16.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (4,'v6-28','v6-22','v6-24',0,0,8,NULL,'2026-10-16T12:00:19.000Z',NULL);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (1,'v6-16','v6-9','v6-15',60,'2026-10-16T12:00:10.000Z','2026-10-16T12:00:12.000Z',2000,1000);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (2,'v6-19','v6-9','v6-18',120,'2026-10-16T12:00:13.000Z','2026-10-16T12:00:15.000Z',2000,1000);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (3,'v6-29','v6-22','v6-28',60,'2026-10-16T12:00:19.000Z',NULL,NULL,NULL);
INSERT INTO rest_pauses (rowid,id,rest_interval_id,started_at,ended_at) VALUES (1,'v6-17','v6-16','2026-10-16T12:00:11.000Z','2026-10-16T12:00:12.000Z');
INSERT INTO rest_pauses (rowid,id,rest_interval_id,started_at,ended_at) VALUES (2,'v6-20','v6-19','2026-10-16T12:00:14.000Z','2026-10-16T12:00:15.000Z');
INSERT INTO rest_pauses (rowid,id,rest_interval_id,started_at,ended_at) VALUES (3,'v6-30','v6-29','2026-10-16T12:00:20.000Z',NULL);
INSERT INTO app_preferences (rowid,key,value_json,updated_at) VALUES (1,'series_display','"both"','2026-10-16T12:00:21.000Z');
INSERT INTO app_preferences (rowid,key,value_json,updated_at) VALUES (2,'rest_sound_enabled','false','2026-10-16T12:00:22.000Z');
INSERT INTO set_load_rules (rowid,set_template_id,reference_set_id,percent,basis) VALUES (1,'v6-6','v6-5',90,'planned_target');
CREATE INDEX programs_updated_at ON programs(updated_at DESC, created_at DESC, id);
CREATE INDEX workouts_program_order ON workout_templates(program_id, sort_order, id);
CREATE INDEX exercises_workout_order ON workout_exercises(workout_template_id, sort_order, id);
CREATE INDEX sets_exercise_order ON set_templates(workout_exercise_id, sort_order, id);
CREATE UNIQUE INDEX one_active_session ON workout_sessions((1)) WHERE status = 'active';
CREATE UNIQUE INDEX one_open_rest_per_session ON rest_intervals(session_id) WHERE ended_at IS NULL;
CREATE UNIQUE INDEX one_open_pause ON rest_pauses(rest_interval_id) WHERE ended_at IS NULL;
CREATE INDEX pauses_interval ON rest_pauses(rest_interval_id, started_at, id);
CREATE TRIGGER preserve_original_targets BEFORE UPDATE OF original_targets ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Original session targets are immutable'); END;
CREATE TRIGGER preserve_performed_targets BEFORE UPDATE ON session_sets
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.id)
    BEGIN SELECT RAISE(ABORT, 'Performed session targets are immutable'); END;
CREATE TRIGGER preserve_performance BEFORE UPDATE OF session_id, session_set_id, sort_order, weight_kg, reps, rir, performed_at ON performed_sets
    BEGIN SELECT RAISE(ABORT, 'Performed values are immutable'); END;
CREATE INDEX replacements_session ON session_exercise_replacements(session_id, changed_at, id);
CREATE INDEX choices_session ON session_exercise_choices(session_id, chosen_at, id);
CREATE INDEX completed_sessions ON workout_sessions(finished_at DESC, id) WHERE status = 'completed';
CREATE TRIGGER selected_exercise_belongs_to_session BEFORE UPDATE OF selected_exercise_id ON workout_sessions
    WHEN NEW.selected_exercise_id IS NOT NULL AND NOT EXISTS
      (SELECT 1 FROM session_exercises WHERE id = NEW.selected_exercise_id AND session_id = NEW.id)
    BEGIN SELECT RAISE(ABORT, 'Selected exercise belongs to another session'); END;
CREATE TRIGGER preserve_execution_exercise BEFORE UPDATE ON session_exercises
    BEGIN SELECT RAISE(ABORT, 'Execution exercise identity is immutable'); END;
CREATE INDEX load_rules_reference ON set_load_rules(reference_set_id);
CREATE TRIGGER validate_load_rule_insert BEFORE INSERT ON set_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup', 'back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work', 'top_set', 'custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid planned load reference'); END;
CREATE TRIGGER validate_load_rule_update BEFORE UPDATE ON set_load_rules
  WHEN NEW.set_template_id != OLD.set_template_id OR NEW.basis != 'planned_target'
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work', 'top_set', 'custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid planned load reference'); END;
CREATE TRIGGER preserve_load_reference BEFORE UPDATE OF kind, workout_exercise_id ON set_templates
  WHEN EXISTS (SELECT 1 FROM set_load_rules r JOIN set_templates dependent ON dependent.id = r.set_template_id
    WHERE r.reference_set_id = OLD.id AND (NEW.workout_exercise_id != dependent.workout_exercise_id
      OR NEW.kind NOT IN ('work', 'top_set', 'custom') OR (dependent.kind = 'back_off' AND NEW.kind != 'top_set')))
    OR EXISTS (SELECT 1 FROM set_load_rules r WHERE r.set_template_id = OLD.id
      AND (NEW.kind != OLD.kind OR NEW.workout_exercise_id != OLD.workout_exercise_id))
  BEGIN SELECT RAISE(ABORT, 'Remove dependent load rules before changing this reference'); END;
CREATE TRIGGER calculated_weight_is_derived BEFORE UPDATE OF target_weight_kg ON set_templates
  WHEN NEW.target_weight_kg IS NOT NULL AND EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = NEW.id)
  BEGIN SELECT RAISE(ABORT, 'Calculated weight must remain derived'); END;
CREATE TRIGGER preserve_load_rule_snapshot BEFORE UPDATE OF load_rule_snapshot ON session_sets
  BEGIN SELECT RAISE(ABORT, 'Original load rule snapshot is immutable'); END;
PRAGMA user_version=6;
PRAGMA foreign_keys=ON;
