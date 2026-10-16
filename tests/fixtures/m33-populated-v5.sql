-- Frozen test fixture produced by released M3.3 commit 52f9b49. No application seed.
PRAGMA foreign_keys = OFF;
CREATE TABLE app_preferences (
    key TEXT PRIMARY KEY NOT NULL CHECK(length(key) BETWEEN 1 AND 80),
    value_json TEXT NOT NULL CHECK(json_valid(value_json)),
    updated_at TEXT NOT NULL
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
CREATE TABLE programs (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 1000),
    sport_type TEXT NOT NULL DEFAULT 'musculation' CHECK(sport_type = 'musculation'),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
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
CREATE TABLE session_exercise_choices (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL,
    expected_set_id TEXT NOT NULL,
    chosen_at TEXT NOT NULL,
    FOREIGN KEY(exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(expected_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
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
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400),
    UNIQUE(session_id, sort_order), UNIQUE(id, session_id),
    FOREIGN KEY(session_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE CASCADE
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
INSERT INTO app_preferences (key,value_json,updated_at) VALUES ('rest_sound_enabled','false','2026-10-15T12:01:20.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a01','Développé couché barre','Pectoraux','Barre et banc','Gardez les pieds stables et les omoplates rapprochées. Descendez la barre de manière contrôlée puis poussez sans rebond.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a02','Développé incliné haltères','Pectoraux','Haltères et banc incliné','Placez le banc en légère inclinaison. Descendez les haltères avec contrôle et poussez en conservant les épaules stables.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a03','Pompes','Pectoraux','Poids du corps','Gardez le corps aligné et les abdominaux engagés. Pliez les coudes pour descendre puis poussez le sol. La charge cible indique un éventuel lest ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a04','Tractions','Dos','Barre de traction','Depuis une suspension contrôlée, tirez le corps vers la barre sans balancer les jambes. Redescendez avec contrôle. La charge cible indique un éventuel lest ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a05','Tirage vertical à la poulie','Dos','Poulie','Asseyez-vous avec le buste stable. Tirez la barre vers le haut de la poitrine et remontez sans laisser les épaules partir vers l’avant.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a06','Rowing haltère','Dos','Haltère et banc','Prenez un appui stable sur le banc et gardez le dos neutre. Tirez le coude vers la hanche puis redescendez avec contrôle.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a07','Squat barre','Quadriceps','Barre et rack','Gardez les pieds stables et le buste gainé. Descendez à une amplitude confortable en suivant la direction des pieds avec les genoux, puis remontez avec contrôle.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a08','Presse à cuisses','Quadriceps','Machine','Réglez le siège pour conserver le bassin en appui. Fléchissez les jambes à une amplitude confortable puis poussez sans verrouiller brusquement les genoux. Indiquez la charge affichée par la machine.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a09','Soulevé de terre roumain','Ischio-jambiers','Barre','Avec les genoux légèrement fléchis, reculez les hanches en gardant la barre près des jambes et le dos neutre. Revenez debout en poussant les hanches vers l’avant.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a10','Leg curl assis','Ischio-jambiers','Machine','Réglez les appuis à votre taille. Fléchissez les genoux sans décoller le bassin puis revenez avec contrôle. Indiquez la charge affichée par la machine.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a11','Développé épaules haltères','Épaules','Haltères','Gardez le buste stable et poussez les haltères au-dessus de la tête à une amplitude confortable. Redescendez avec contrôle sans cambrer excessivement.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a12','Élévations latérales','Épaules','Haltères','Levez les bras sur les côtés avec les coudes légèrement fléchis. Arrêtez à une hauteur confortable et redescendez sans élan.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a13','Curl haltères','Biceps','Haltères','Gardez les coudes près du buste et fléchissez les bras sans balancer le corps. Redescendez les haltères avec contrôle.','per_hand',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a14','Extension triceps à la poulie','Triceps','Poulie','Gardez les coudes près du buste et étendez les bras vers le bas. Remontez avec contrôle sans déplacer les épaules.','total',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('b459f856-f639-4cb2-9278-d7ac1e287a15','Crunch au sol','Abdominaux','Poids du corps','Décollez légèrement les épaules en rapprochant le thorax du bassin, sans tirer sur la nuque. Revenez avec contrôle. La charge cible indique un éventuel poids ajouté.','additional',0,'2026-10-14T00:00:00.000Z','2026-10-14T00:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('id-99997','Barre','Dos','Salle','','total',1,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('id-99996','Tractions','Dos','Salle','','additional',1,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES ('id-99995','Haltères','Dos','Salle','','per_hand',1,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('id-99981','id-99988','id-99986',0,40,8,0,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:10.000Z');
INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('id-99973','id-99988','id-99983',1,NULL,10,NULL,'2026-10-15T12:00:11.000Z','2026-10-15T12:00:12.000Z');
INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('id-99971','id-99988','id-99982',2,NULL,10,NULL,'2026-10-15T12:00:13.000Z','2026-10-15T12:00:14.000Z');
INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('id-99969','id-99988','id-99985',3,15,10,NULL,'2026-10-15T12:00:15.000Z','2026-10-15T12:00:15.000Z');
INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('id-99961','id-99968','id-99966',0,NULL,10,NULL,'2026-10-15T12:01:15.000Z',NULL);
INSERT INTO programs (id,name,description,sport_type,created_at,updated_at) VALUES ('id-99999','Mes vrais repères de test','Texte "cité"
avec accents 🏋️','musculation','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO rest_intervals (id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES ('id-99980','id-99988','id-99981',30,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:10.000Z',10000,8000);
INSERT INTO rest_intervals (id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES ('id-99972','id-99988','id-99973',30,'2026-10-15T12:00:11.000Z','2026-10-15T12:00:12.000Z',1000,1000);
INSERT INTO rest_intervals (id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES ('id-99970','id-99988','id-99971',30,'2026-10-15T12:00:13.000Z','2026-10-15T12:00:14.000Z',1000,1000);
INSERT INTO rest_intervals (id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES ('id-99960','id-99968','id-99961',30,'2026-10-15T12:01:15.000Z',NULL,NULL,NULL);
INSERT INTO rest_pauses (id,rest_interval_id,started_at,ended_at) VALUES ('id-99979','id-99980','2026-10-15T12:00:03.000Z','2026-10-15T12:00:05.000Z');
INSERT INTO rest_pauses (id,rest_interval_id,started_at,ended_at) VALUES ('id-99959','id-99960','2026-10-15T12:01:20.000Z',NULL);
INSERT INTO session_exercise_choices (id,session_id,exercise_id,expected_set_id,chosen_at) VALUES ('id-99976','id-99988','id-99984','id-99985','2026-10-15T12:00:10.000Z');
INSERT INTO session_exercise_choices (id,session_id,exercise_id,expected_set_id,chosen_at) VALUES ('id-99975','id-99988','id-99978','id-99983','2026-10-15T12:00:10.000Z');
INSERT INTO session_exercise_choices (id,session_id,exercise_id,expected_set_id,chosen_at) VALUES ('id-99974','id-99988','id-99984','id-99985','2026-10-15T12:00:10.000Z');
INSERT INTO session_exercise_replacements (id,session_id,from_exercise_id,to_exercise_id,active_set_id,remaining_set_count,changed_at) VALUES ('id-99977','id-99988','id-99987','id-99978','id-99985',1,'2026-10-15T12:00:10.000Z');
INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES ('id-99987','id-99988','id-99994','id-99997',0,'Barre','Dos','Salle','','','total',0);
INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES ('id-99984','id-99988','id-99991','id-99996',1,'Tractions','Dos','Salle','','','additional',1);
INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES ('id-99978','id-99988','id-99994','id-99995',2,'Haltères','Dos','Salle','','','per_hand',0);
INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES ('id-99967','id-99968','id-99994','id-99997',0,'Barre','Dos','Salle','','','total',0);
INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES ('id-99964','id-99968','id-99991','id-99996',1,'Tractions','Dos','Salle','','','additional',1);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99986','id-99988','id-99987','id-99993',0,0,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99985','id-99988','id-99978','id-99992',1,1,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,NULL,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99983','id-99988','id-99984','id-99990',2,0,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99982','id-99988','id-99984','id-99989',3,1,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99966','id-99968','id-99967','id-99993',0,0,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99965','id-99968','id-99967','id-99992',1,1,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99963','id-99968','id-99964','id-99990',2,0,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec) VALUES ('id-99962','id-99968','id-99964','id-99989',3,1,'','work','','{"repsMin":99,"repsMax":99,"targetWeightKg":999,"targetRir":7,"restAfterSec":30}',99,99,999,7,30);
INSERT INTO set_templates (id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES ('id-99993','id-99994',0,'','work',99,99,999,7,30,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO set_templates (id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES ('id-99992','id-99994',1,'','work',99,99,999,7,30,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO set_templates (id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES ('id-99990','id-99991',0,'','work',99,99,999,7,30,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO set_templates (id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES ('id-99989','id-99991',1,'','work',99,99,999,7,30,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO workout_exercises (id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES ('id-99994','id-99998','id-99997',0,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO workout_exercises (id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES ('id-99991','id-99998','id-99996',1,'','2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
INSERT INTO workout_sessions (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES ('id-99988','id-99998','id-99999','Haut du corps','Mes vrais repères de test','completed','2026-10-15T12:00:00.000Z','2026-10-15T12:00:15.000Z',NULL);
INSERT INTO workout_sessions (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES ('id-99968','id-99998','id-99999','Haut du corps','Mes vrais repères de test','active','2026-10-15T12:01:15.000Z',NULL,NULL);
INSERT INTO workout_templates (id,program_id,name,notes,sort_order,created_at,updated_at) VALUES ('id-99998','id-99999','Haut du corps','',0,'2026-10-15T12:00:00.000Z','2026-10-15T12:00:00.000Z');
CREATE INDEX choices_session ON session_exercise_choices(session_id, chosen_at, id);
CREATE INDEX completed_sessions ON workout_sessions(finished_at DESC, id) WHERE status = 'completed';
CREATE INDEX exercises_workout_order ON workout_exercises(workout_template_id, sort_order, id);
CREATE UNIQUE INDEX one_active_session ON workout_sessions((1)) WHERE status = 'active';
CREATE UNIQUE INDEX one_open_pause ON rest_pauses(rest_interval_id) WHERE ended_at IS NULL;
CREATE UNIQUE INDEX one_open_rest_per_session ON rest_intervals(session_id) WHERE ended_at IS NULL;
CREATE INDEX pauses_interval ON rest_pauses(rest_interval_id, started_at, id);
CREATE TRIGGER preserve_execution_exercise BEFORE UPDATE ON session_exercises
    BEGIN SELECT RAISE(ABORT, 'Execution exercise identity is immutable'); END;
CREATE TRIGGER preserve_original_targets BEFORE UPDATE OF original_targets ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Original session targets are immutable'); END;
CREATE TRIGGER preserve_performance BEFORE UPDATE OF session_id, session_set_id, sort_order, weight_kg, reps, rir, performed_at ON performed_sets
    BEGIN SELECT RAISE(ABORT, 'Performed values are immutable'); END;
CREATE TRIGGER preserve_performed_targets BEFORE UPDATE ON session_sets
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.id)
    BEGIN SELECT RAISE(ABORT, 'Performed session targets are immutable'); END;
CREATE INDEX programs_updated_at ON programs(updated_at DESC, created_at DESC, id);
CREATE INDEX replacements_session ON session_exercise_replacements(session_id, changed_at, id);
CREATE TRIGGER selected_exercise_belongs_to_session BEFORE UPDATE OF selected_exercise_id ON workout_sessions
    WHEN NEW.selected_exercise_id IS NOT NULL AND NOT EXISTS
      (SELECT 1 FROM session_exercises WHERE id = NEW.selected_exercise_id AND session_id = NEW.id)
    BEGIN SELECT RAISE(ABORT, 'Selected exercise belongs to another session'); END;
CREATE INDEX sets_exercise_order ON set_templates(workout_exercise_id, sort_order, id);
CREATE INDEX workouts_program_order ON workout_templates(program_id, sort_order, id);
PRAGMA user_version = 5;
PRAGMA foreign_keys = ON;
