-- Generated with released M3.4B 1da942a repositories. Test fixture only.
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
    legacy_source_set_template_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    series_index INTEGER NOT NULL CHECK(typeof(series_index) = 'integer' AND series_index >= 0),
    label TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    notes TEXT NOT NULL,
    original_targets TEXT NOT NULL CHECK(json_valid(original_targets)),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real','integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400), load_rule_snapshot TEXT CHECK(load_rule_snapshot IS NULL OR json_valid(load_rule_snapshot)), source_set_template_id TEXT, initial_metadata TEXT CHECK(initial_metadata IS NULL OR json_valid(initial_metadata)), added_at TEXT, addition_scope TEXT CHECK(addition_scope IN ('session', 'program')), addition_key TEXT, edit_scope TEXT CHECK(edit_scope IN ('session', 'program')), removed_at TEXT,
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
CREATE TABLE set_actual_load_rules (
    set_template_id TEXT PRIMARY KEY NOT NULL REFERENCES set_templates(id) ON DELETE CASCADE,
    reference_set_id TEXT REFERENCES set_templates(id) ON DELETE SET NULL,
    percent REAL NOT NULL CHECK(typeof(percent) IN ('real', 'integer') AND percent > 0 AND percent <= 100),
    basis TEXT NOT NULL DEFAULT 'performed_weight' CHECK(basis = 'performed_weight')
  );
CREATE TABLE session_set_load_rules (
    session_set_id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    reference_set_id TEXT NOT NULL,
    basis TEXT NOT NULL CHECK(basis IN ('planned_target', 'performed_weight')),
    percent REAL NOT NULL CHECK(typeof(percent) IN ('real', 'integer') AND percent > 0 AND percent <= 100),
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total','per_hand','additional')),
    suspended INTEGER NOT NULL DEFAULT 0 CHECK(suspended IN (0,1)),
    CHECK(session_set_id != reference_set_id),
    FOREIGN KEY(session_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT,
    FOREIGN KEY(reference_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE session_set_adjustments (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_set_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('session','program')),
    action TEXT NOT NULL CHECK(action IN ('add','edit','delete','resolve','suspend')),
    payload TEXT NOT NULL CHECK(json_valid(payload)), changed_at TEXT NOT NULL,
    FOREIGN KEY(session_set_id, session_id) REFERENCES session_sets(id, session_id) ON DELETE RESTRICT
  );
CREATE TABLE session_personal_notes (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    session_exercise_id TEXT,
    body TEXT NOT NULL CHECK(length(body) <= 4000), updated_at TEXT NOT NULL,
    FOREIGN KEY(session_exercise_id, session_id) REFERENCES session_exercises(id, session_id) ON DELETE RESTRICT
  );
INSERT INTO programs (rowid,id,name,description,sport_type,created_at,updated_at) VALUES (1,'v7-1','Mon carnet v7','','musculation','2026-10-16T12:00:01.000Z','2026-10-16T12:00:01.000Z');
INSERT INTO workout_templates (rowid,id,program_id,name,notes,sort_order,created_at,updated_at) VALUES (1,'v7-2','v7-1','Séance v7','',0,'2026-10-16T12:00:02.000Z','2026-10-16T12:00:02.000Z');
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
INSERT INTO exercise_catalog (rowid,id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at) VALUES (16,'v7-3','Barre personnelle v7','Dos','Barre','','total',1,'2026-10-16T12:00:03.000Z','2026-10-16T12:00:03.000Z');
INSERT INTO workout_exercises (rowid,id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES (1,'v7-4','v7-2','v7-3',0,'','2026-10-16T12:00:04.000Z','2026-10-16T12:00:04.000Z');
INSERT INTO workout_exercises (rowid,id,workout_template_id,exercise_id,sort_order,notes,created_at,updated_at) VALUES (2,'v7-8','v7-2','b459f856-f639-4cb2-9278-d7ac1e287a15',1,'','2026-10-16T12:00:08.000Z','2026-10-16T12:00:08.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (1,'v7-5','v7-4',0,'Top','top_set',8,10,100,2,60,'Consigne initiale','2026-10-16T12:00:05.000Z','2026-10-16T12:00:05.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (2,'v7-6','v7-4',1,'Top','warmup',8,10,NULL,2,60,'Consigne initiale','2026-10-16T12:00:06.000Z','2026-10-16T12:00:06.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (3,'v7-7','v7-4',2,'Top','back_off',8,10,NULL,2,60,'Consigne initiale','2026-10-16T12:00:07.000Z','2026-10-16T12:00:07.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (4,'v7-9','v7-8',0,'Top','work',8,10,NULL,NULL,0,'Consigne initiale','2026-10-16T12:00:09.000Z','2026-10-16T12:00:09.000Z');
INSERT INTO set_templates (rowid,id,workout_exercise_id,sort_order,label,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,notes,created_at,updated_at) VALUES (5,'v7-40','v7-4',3,'Extra future','work',8,10,100,2,60,'Consigne initiale','2026-10-16T12:00:25.000Z','2026-10-16T12:00:25.000Z');
INSERT INTO workout_sessions (rowid,id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES (1,'v7-10','v7-2','v7-1','Séance v7','Mon carnet v7','completed','2026-10-16T12:00:10.000Z','2026-10-16T12:00:18.000Z',NULL);
INSERT INTO workout_sessions (rowid,id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at,selected_exercise_id) VALUES (2,'v7-25','v7-2','v7-1','Séance v7','Mon carnet v7','active','2026-10-16T12:00:20.000Z',NULL,NULL);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (1,'v7-11','v7-10','v7-4','v7-3',0,'Barre personnelle v7','Dos','Barre','','','total',0);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (2,'v7-15','v7-10','v7-8','b459f856-f639-4cb2-9278-d7ac1e287a15',1,'Crunch au sol','Abdominaux','Poids du corps','Décollez légèrement les épaules en rapprochant le thorax du bassin, sans tirer sur la nuque. Revenez avec contrôle. La charge cible indique un éventuel poids ajouté.','','additional',1);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (3,'v7-26','v7-25','v7-4','v7-3',0,'Barre personnelle v7','Dos','Barre','','','total',0);
INSERT INTO session_exercises (rowid,id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode,planned_order) VALUES (4,'v7-30','v7-25','v7-8','b459f856-f639-4cb2-9278-d7ac1e287a15',1,'Crunch au sol','Abdominaux','Poids du corps','Décollez légèrement les épaules en rapprochant le thorax du bassin, sans tirer sur la nuque. Revenez avec contrôle. La charge cible indique un éventuel poids ajouté.','','additional',1);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (1,'v7-12','v7-10','v7-11','v7-5',0,0,'Top','top_set','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60}',8,10,100,2,60,NULL,'v7-5','{"label":"Top","kind":"top_set","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (2,'v7-13','v7-10','v7-11','v7-6',1,1,'Top','warmup','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":50,"targetRir":2,"restAfterSec":60}',8,10,50,2,60,'{"basis":"planned_target","referenceSetTemplateId":"v7-5","percent":50,"referenceWeightKg":100,"resolvedWeightKg":50,"weightMode":"total"}','v7-6','{"label":"Top","kind":"warmup","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (3,'v7-14','v7-10','v7-11','v7-7',2,2,'Top','back_off','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":null,"targetRir":2,"restAfterSec":60}',8,10,85.5,2,60,'{"basis":"performed_weight","referenceSetTemplateId":"v7-5","percent":90,"referenceWeightKg":null,"resolvedWeightKg":null,"weightMode":"total"}','v7-7','{"label":"Top","kind":"back_off","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (4,'v7-16','v7-10','v7-15','v7-9',3,0,'Top','work','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":null,"targetRir":null,"restAfterSec":0}',8,10,NULL,NULL,0,NULL,'v7-9','{"label":"Top","kind":"work","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (5,'v7-27','v7-25','v7-26','v7-5',0,0,'Top','top_set','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60}',8,10,100,2,60,NULL,'v7-5','{"label":"Top","kind":"top_set","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (6,'v7-28','v7-25','v7-26','v7-6',1,1,'Top','warmup','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":50,"targetRir":2,"restAfterSec":60}',8,10,50,2,60,'{"basis":"planned_target","referenceSetTemplateId":"v7-5","percent":50,"referenceWeightKg":100,"resolvedWeightKg":50,"weightMode":"total"}','v7-6','{"label":"Top","kind":"warmup","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (7,'v7-29','v7-25','v7-26','v7-7',2,2,'Top','back_off','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":null,"targetRir":2,"restAfterSec":60}',8,10,0,2,60,'{"basis":"performed_weight","referenceSetTemplateId":"v7-5","percent":90,"referenceWeightKg":null,"resolvedWeightKg":null,"weightMode":"total"}','v7-7','{"label":"Top","kind":"back_off","notes":"Consigne initiale"}',NULL,NULL,NULL,'session',NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (8,'v7-31','v7-25','v7-30','v7-9',3,0,'Top','work','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":null,"targetRir":null,"restAfterSec":0}',8,10,NULL,NULL,0,NULL,'v7-9','{"label":"Top","kind":"work","notes":"Consigne initiale"}',NULL,NULL,NULL,NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (9,'v7-37','v7-25','v7-26','',4,3,'Extra locale','custom','Note ajoutée','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60}',8,10,100,2,60,NULL,NULL,'{"label":"Extra locale","kind":"custom","notes":"Note ajoutée"}','2026-10-16T12:00:24.000Z','session','v7-local',NULL,NULL);
INSERT INTO session_sets (rowid,id,session_id,session_exercise_id,legacy_source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,load_rule_snapshot,source_set_template_id,initial_metadata,added_at,addition_scope,addition_key,edit_scope,removed_at) VALUES (10,'v7-39','v7-25','v7-26','v7-40',5,4,'Extra future','work','Consigne initiale','{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60}',8,10,100,2,60,NULL,'v7-40','{"label":"Extra future","kind":"work","notes":"Consigne initiale"}','2026-10-16T12:00:25.000Z','program','v7-program',NULL,'2026-10-16T12:00:26.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (1,'v7-17','v7-10','v7-12',0,95,8,0,'2026-10-16T12:00:11.000Z','2026-10-16T12:00:12.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (2,'v7-20','v7-10','v7-13',1,NULL,8,NULL,'2026-10-16T12:00:13.000Z','2026-10-16T12:00:14.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (3,'v7-22','v7-10','v7-14',2,85.5,8,NULL,'2026-10-16T12:00:15.000Z','2026-10-16T12:00:16.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (4,'v7-24','v7-10','v7-16',3,NULL,8,NULL,'2026-10-16T12:00:17.000Z','2026-10-16T12:00:17.000Z');
INSERT INTO performed_sets (rowid,id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES (5,'v7-32','v7-25','v7-27',0,0,8,NULL,'2026-10-16T12:00:21.000Z',NULL);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (1,'v7-19','v7-10','v7-17',60,'2026-10-16T12:00:11.000Z','2026-10-16T12:00:12.000Z',1000,1000);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (2,'v7-21','v7-10','v7-20',60,'2026-10-16T12:00:13.000Z','2026-10-16T12:00:14.000Z',1000,1000);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (3,'v7-23','v7-10','v7-22',60,'2026-10-16T12:00:15.000Z','2026-10-16T12:00:16.000Z',1000,1000);
INSERT INTO rest_intervals (rowid,id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms) VALUES (4,'v7-34','v7-25','v7-32',60,'2026-10-16T12:00:21.000Z',NULL,NULL,NULL);
INSERT INTO rest_pauses (rowid,id,rest_interval_id,started_at,ended_at) VALUES (1,'v7-35','v7-34','2026-10-16T12:00:22.000Z',NULL);
INSERT INTO app_preferences (rowid,key,value_json,updated_at) VALUES (1,'rest_sound_enabled','false','2026-10-16T12:00:29.000Z');
INSERT INTO app_preferences (rowid,key,value_json,updated_at) VALUES (2,'series_display','"both"','2026-10-16T12:00:30.000Z');
INSERT INTO set_load_rules (rowid,set_template_id,reference_set_id,percent,basis) VALUES (1,'v7-6','v7-5',50,'planned_target');
INSERT INTO set_actual_load_rules (rowid,set_template_id,reference_set_id,percent,basis) VALUES (1,'v7-7','v7-5',90,'performed_weight');
INSERT INTO session_set_load_rules (rowid,session_set_id,session_id,reference_set_id,basis,percent,weight_mode,suspended) VALUES (1,'v7-13','v7-10','v7-12','planned_target',50,'total',0);
INSERT INTO session_set_load_rules (rowid,session_set_id,session_id,reference_set_id,basis,percent,weight_mode,suspended) VALUES (2,'v7-14','v7-10','v7-12','performed_weight',90,'total',0);
INSERT INTO session_set_load_rules (rowid,session_set_id,session_id,reference_set_id,basis,percent,weight_mode,suspended) VALUES (3,'v7-28','v7-25','v7-27','planned_target',50,'total',0);
INSERT INTO session_set_load_rules (rowid,session_set_id,session_id,reference_set_id,basis,percent,weight_mode,suspended) VALUES (4,'v7-29','v7-25','v7-27','performed_weight',85,'total',0);
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (1,'v7-18','v7-10','v7-14','session','resolve','{"rule":{"referenceSetId":"v7-12","basis":"performed_weight","percent":90,"weightMode":"total","suspended":false},"referenceWeightKg":95,"referencePerformanceId":"v7-17","resolvedWeightKg":85.5}','2026-10-16T12:00:11.000Z');
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (2,'v7-33','v7-25','v7-29','session','resolve','{"rule":{"referenceSetId":"v7-27","basis":"performed_weight","percent":90,"weightMode":"total","suspended":false},"referenceWeightKg":0,"referencePerformanceId":"v7-32","resolvedWeightKg":0}','2026-10-16T12:00:21.000Z');
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (3,'v7-36','v7-25','v7-29','session','edit','{"targets":{"repsMin":8,"repsMax":10,"targetWeightKg":0,"targetRir":2,"restAfterSec":60},"kind":"back_off","label":"Top","notes":"Consigne initiale","rule":{"basis":"performed_weight","referenceSetId":"v7-27","percent":85},"referenceWeightKg":0,"referencePerformanceId":"v7-32","resolvedWeightKg":0,"sourceSetTemplateId":"v7-7"}','2026-10-16T12:00:23.000Z');
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (4,'v7-38','v7-25','v7-37','session','add','{"targets":{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60},"kind":"custom","label":"Extra locale","notes":"Note ajoutée","rule":null,"referenceWeightKg":null,"referencePerformanceId":null,"resolvedWeightKg":100,"sourceSetTemplateId":null}','2026-10-16T12:00:24.000Z');
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (5,'v7-41','v7-25','v7-39','program','add','{"targets":{"repsMin":8,"repsMax":10,"targetWeightKg":100,"targetRir":2,"restAfterSec":60},"kind":"work","label":"Extra future","notes":"Consigne initiale","rule":null,"referenceWeightKg":null,"referencePerformanceId":null,"resolvedWeightKg":100,"sourceSetTemplateId":"v7-40"}','2026-10-16T12:00:25.000Z');
INSERT INTO session_set_adjustments (rowid,id,session_id,session_set_id,scope,action,payload,changed_at) VALUES (6,'v7-42','v7-25','v7-39','session','delete','{"programPreserved":true}','2026-10-16T12:00:26.000Z');
INSERT INTO session_personal_notes (rowid,id,session_id,session_exercise_id,body,updated_at) VALUES (1,'session:v7-10','v7-10',NULL,'Note de bilan v7','2026-10-16T12:00:19.000Z');
INSERT INTO session_personal_notes (rowid,id,session_id,session_exercise_id,body,updated_at) VALUES (2,'session:v7-25','v7-25',NULL,'Ressenti v7','2026-10-16T12:00:27.000Z');
INSERT INTO session_personal_notes (rowid,id,session_id,session_exercise_id,body,updated_at) VALUES (3,'exercise:v7-26','v7-25','v7-26','Note exercice v7','2026-10-16T12:00:28.000Z');
CREATE VIEW all_load_rules AS SELECT * FROM set_load_rules UNION ALL SELECT * FROM set_actual_load_rules;
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
CREATE TRIGGER preserve_load_rule_snapshot BEFORE UPDATE OF load_rule_snapshot ON session_sets
  BEGIN SELECT RAISE(ABORT, 'Original load rule snapshot is immutable'); END;
CREATE TRIGGER preserve_performed_targets BEFORE UPDATE ON session_sets
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.id)
    BEGIN SELECT RAISE(ABORT, 'Performed session targets are immutable'); END;
CREATE UNIQUE INDEX unique_session_addition ON session_sets(session_id, addition_key) WHERE addition_key IS NOT NULL;
CREATE INDEX actual_load_rules_reference ON set_actual_load_rules(reference_set_id);
CREATE TRIGGER preserve_load_reference BEFORE UPDATE OF kind, workout_exercise_id ON set_templates
  WHEN EXISTS (SELECT 1 FROM all_load_rules r JOIN set_templates dependent ON dependent.id = r.set_template_id
    WHERE r.reference_set_id = OLD.id AND (NEW.workout_exercise_id != dependent.workout_exercise_id
      OR NEW.kind NOT IN ('work', 'top_set', 'custom') OR (dependent.kind = 'back_off' AND NEW.kind != 'top_set')))
    OR EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = OLD.id
      AND (NEW.kind != OLD.kind OR NEW.workout_exercise_id != OLD.workout_exercise_id))
  BEGIN SELECT RAISE(ABORT, 'Remove dependent load rules before changing this reference'); END;
CREATE TRIGGER calculated_weight_is_derived BEFORE UPDATE OF target_weight_kg ON set_templates
  WHEN NEW.target_weight_kg IS NOT NULL AND EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = NEW.id)
  BEGIN SELECT RAISE(ABORT, 'Calculated weight must remain derived'); END;
CREATE INDEX session_rules_reference ON session_set_load_rules(reference_set_id);
CREATE TRIGGER preserve_rule_definition BEFORE UPDATE OF session_set_id, session_id, reference_set_id, basis, percent, weight_mode ON session_set_load_rules
    BEGIN SELECT RAISE(ABORT, 'Replace an unperformed rule explicitly'); END;
CREATE TRIGGER protect_performance_delete BEFORE DELETE ON performed_sets
    BEGIN SELECT RAISE(ABORT, 'Performed values are immutable'); END;
CREATE TRIGGER protect_performed_rule_update BEFORE UPDATE ON session_set_load_rules
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.session_set_id)
    BEGIN SELECT RAISE(ABORT, 'Performed load rule is immutable'); END;
CREATE TRIGGER protect_performed_rule_delete BEFORE DELETE ON session_set_load_rules
    WHEN EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = OLD.session_set_id)
    BEGIN SELECT RAISE(ABORT, 'Performed load rule is immutable'); END;
CREATE TRIGGER validate_execution_rule BEFORE INSERT ON session_set_load_rules
    WHEN NOT EXISTS (
      SELECT 1 FROM session_sets s JOIN session_sets ref ON ref.id = NEW.reference_set_id
      JOIN session_exercises e ON e.id = s.session_exercise_id
      WHERE s.id = NEW.session_set_id AND s.session_id = NEW.session_id AND ref.session_id = NEW.session_id
      AND s.session_exercise_id = ref.session_exercise_id AND e.weight_mode = NEW.weight_mode
      AND s.removed_at IS NULL AND ref.removed_at IS NULL AND s.kind IN ('warmup','back_off')
      AND ref.kind IN ('work','top_set','custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS(SELECT 1 FROM performed_sets WHERE session_set_id = s.id)
      AND NOT EXISTS(SELECT 1 FROM session_set_load_rules WHERE session_set_id = ref.id OR reference_set_id = s.id))
    BEGIN SELECT RAISE(ABORT, 'Invalid execution load reference'); END;
CREATE TRIGGER preserve_initial_series_metadata BEFORE UPDATE OF initial_metadata ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Initial series metadata is immutable'); END;
CREATE TRIGGER preserve_addition_provenance BEFORE UPDATE OF legacy_source_set_template_id, source_set_template_id,
    added_at, addition_scope, addition_key ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Session origin is immutable'); END;
CREATE TRIGGER protect_removed_series BEFORE UPDATE OF removed_at ON session_sets
    WHEN OLD.addition_key IS NULL OR OLD.removed_at IS NOT NULL OR NEW.removed_at IS NULL
    BEGIN SELECT RAISE(ABORT, 'Only unperformed added series can be removed once'); END;
CREATE INDEX adjustments_session ON session_set_adjustments(session_id, changed_at, id);
CREATE TRIGGER preserve_adjustment BEFORE UPDATE ON session_set_adjustments
    BEGIN SELECT RAISE(ABORT, 'Session adjustment log is immutable'); END;
CREATE TRIGGER preserve_adjustment_delete BEFORE DELETE ON session_set_adjustments
    BEGIN SELECT RAISE(ABORT, 'Session adjustment log is immutable'); END;
CREATE UNIQUE INDEX one_personal_note ON session_personal_notes(session_id, COALESCE(session_exercise_id, ''));
CREATE TRIGGER protect_session_set_delete BEFORE DELETE ON session_sets
    BEGIN SELECT RAISE(ABORT, 'Session series must be retained'); END;
CREATE TRIGGER validate_set_load_rules_insert BEFORE INSERT ON set_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup','back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_actual_load_rules WHERE set_template_id = NEW.set_template_id)
    OR EXISTS (SELECT 1 FROM all_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work','top_set','custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid load reference'); END;
CREATE TRIGGER validate_set_load_rules_update BEFORE UPDATE ON set_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup','back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_actual_load_rules WHERE set_template_id = NEW.set_template_id)
    OR EXISTS (SELECT 1 FROM all_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work','top_set','custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid load reference'); END;
CREATE TRIGGER validate_set_actual_load_rules_insert BEFORE INSERT ON set_actual_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup','back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = NEW.set_template_id)
    OR EXISTS (SELECT 1 FROM all_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work','top_set','custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid load reference'); END;
CREATE TRIGGER validate_set_actual_load_rules_update BEFORE UPDATE ON set_actual_load_rules
  WHEN NOT EXISTS (SELECT 1 FROM set_templates s WHERE s.id = NEW.set_template_id
    AND s.kind IN ('warmup','back_off') AND s.target_weight_kg IS NULL)
    OR EXISTS (SELECT 1 FROM set_load_rules WHERE set_template_id = NEW.set_template_id)
    OR EXISTS (SELECT 1 FROM all_load_rules WHERE reference_set_id = NEW.set_template_id)
    OR (NEW.reference_set_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM set_templates s JOIN set_templates ref ON ref.id = NEW.reference_set_id
      WHERE s.id = NEW.set_template_id AND s.id != ref.id AND s.workout_exercise_id = ref.workout_exercise_id
      AND ref.kind IN ('work','top_set','custom') AND (s.kind != 'back_off' OR ref.kind = 'top_set')
      AND NOT EXISTS (SELECT 1 FROM all_load_rules WHERE set_template_id = ref.id)))
  BEGIN SELECT RAISE(ABORT, 'Invalid load reference'); END;
PRAGMA user_version=7;
PRAGMA foreign_keys=ON;
