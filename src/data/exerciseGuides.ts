import type { ExerciseCatalogItem, WeightMode } from '../domain/training';

export interface ExerciseAlternative { exerciseId: string; reason: string }
export interface ExerciseGuide {
  description: string;
  start: string;
  steps: readonly string[];
  tips: readonly string[];
  mistakes: readonly string[];
  load: string;
  alternatives: readonly ExerciseAlternative[];
}

// Editorial content shipped offline, never seeded into personal data. These keys
// are the existing M1.1 catalog identities, not names or muscle-text matches.
const id = (suffix: string) => `b459f856-f639-4cb2-9278-d7ac1e287a${suffix}`;
export const EXERCISE_GUIDES: Readonly<Record<string, ExerciseGuide>> = {
  [id('01')]: {
    description: 'Une poussée allongée sur banc, avec une barre tenue à deux mains.',
    start: 'Allongez-vous sur le banc, pieds stables au sol. Placez les mains de façon symétrique sur la barre.',
    steps: ['Sortez la barre des supports en gardant les épaules stables.', 'Descendez vers la poitrine sans rebond, dans une amplitude que vous contrôlez.', 'Repoussez la barre puis reposez-la sur les supports après la série.'],
    tips: ['Gardez les poignets dans le prolongement des avant-bras.', 'Réglez les sécurités du rack ou faites-vous assister pour une charge difficile.'],
    mistakes: ['Rebondir sur la poitrine.', 'Décoller les pieds ou perdre ses appuis en poussant.'],
    load: 'Enregistrez le poids total de la barre et des disques, sans compter chaque côté séparément.',
    alternatives: [{ exerciseId: id('02'), reason: 'Poussée sur banc avec haltères et inclinaison : angle et stabilité différents du couché barre.' }, { exerciseId: id('03'), reason: 'Poussée au poids du corps, sans banc. La difficulté et le mode de charge diffèrent.' }],
  },
  [id('02')]: {
    description: 'Une poussée avec deux haltères, le dos appuyé sur un banc incliné.',
    start: 'Réglez une légère inclinaison et asseyez-vous avec les pieds en appui. Amenez les haltères près des épaules.',
    steps: ['Poussez les haltères au-dessus de la poitrine en gardant le dos en appui.', 'Redescendez lentement de chaque côté dans une amplitude confortable.', 'À la fin, ramenez les haltères de façon contrôlée avant de vous relever.'],
    tips: ['Commencez avec une charge facile à installer et à reposer.', 'Laissez les deux bras avancer ensemble sans cogner les haltères.'],
    mistakes: ['Cambrer davantage pour finir une répétition.', 'Laisser un haltère descendre beaucoup plus bas que l’autre.'],
    load: 'Saisissez le poids d’un seul haltère : deux haltères de 20 kg se notent 20 kg, pas 40 kg.',
    alternatives: [{ exerciseId: id('01'), reason: 'Poussée sur banc plat à la barre : angle et charge totale différents.' }, { exerciseId: id('03'), reason: 'Poussée au poids du corps ; aucune équivalence de charge avec les haltères.' }],
  },
  [id('03')]: {
    description: 'Une poussée au sol où le corps se déplace en bloc, en appui sur les mains et les pieds.',
    start: 'Placez les mains au sol et allongez les jambes. Trouvez des appuis permettant de garder le corps aligné.',
    steps: ['Pliez les coudes pour rapprocher le buste du sol.', 'Poussez le sol pour revenir, sans laisser le bassin s’affaisser.'],
    tips: ['Un appui des mains sur un support stable surélevé peut faciliter le départ.', 'Choisissez une amplitude que vous pouvez répéter avec le même contrôle.'],
    mistakes: ['Faire remonter le buste avant le bassin.', 'Avancer seulement la tête vers le sol.'],
    load: 'Notez uniquement un éventuel lest ajouté, jamais votre poids corporel. Sans lest, la charge peut rester vide.',
    alternatives: [{ exerciseId: id('01'), reason: 'Poussée sur banc avec une charge externe totale ; le mouvement et la difficulté ne sont pas identiques.' }],
  },
  [id('04')]: {
    description: 'Un tirage où vous soulevez votre corps vers une barre fixe.',
    start: 'Saisissez une barre stable et gardez une suspension contrôlée, sans élan.',
    steps: ['Tirez pour rapprocher le haut du corps de la barre.', 'Redescendez progressivement jusqu’à votre position de départ contrôlée.'],
    tips: ['Gardez les jambes calmes plutôt que de chercher de l’élan.', 'Si le mouvement est trop difficile, le tirage vertical permet de choisir une charge plus accessible.'],
    mistakes: ['Se balancer pour monter.', 'Se laisser tomber à la descente.'],
    load: 'Enregistrez seulement le lest ajouté. Ne saisissez pas votre poids corporel ni une assistance comme une charge négative.',
    alternatives: [{ exerciseId: id('05'), reason: 'Tirage vertical avec une charge réglable à la poulie ; le corps reste assis au lieu d’être soulevé.' }],
  },
  [id('05')]: {
    description: 'Un tirage vertical assis à la poulie, avec une charge réglable.',
    start: 'Réglez le siège et l’appui des cuisses. Saisissez la barre avec des appuis stables.',
    steps: ['Tirez la barre devant vous vers le haut de la poitrine.', 'Accompagnez la remontée de la barre sans laisser la pile de poids retomber.'],
    tips: ['Gardez une inclinaison du buste modérée et stable.', 'Choisissez une charge permettant une remontée aussi contrôlée que la descente.'],
    mistakes: ['Tirer la barre derrière la nuque.', 'Basculer fortement le buste pour déplacer la charge.'],
    load: 'Saisissez la charge indiquée sur cette machine. Deux machines peuvent avoir des résistances différentes malgré le même nombre affiché.',
    alternatives: [{ exerciseId: id('04'), reason: 'Tirage au poids du corps, souvent plus exigeant ; pas de conversion directe entre charge de poulie et lest.' }],
  },
  [id('06')]: {
    description: 'Un tirage avec un haltère, un bras à la fois, en prenant appui sur un banc.',
    start: 'Prenez un appui stable sur le banc. Gardez le dos dans une position confortable et l’haltère sous l’épaule.',
    steps: ['Tirez le coude vers la hanche sans tourner le buste.', 'Redescendez l’haltère avec contrôle puis réalisez l’autre côté.'],
    tips: ['Gardez les épaules à peu près face au sol.', 'Commencez avec une charge permettant de conserver votre appui pendant toute la série.'],
    mistakes: ['Donner un à-coup en tournant le buste.', 'Hausser l’épaule vers l’oreille pour finir le tirage.'],
    load: 'Saisissez le poids de l’haltère utilisé, sans doubler pour les deux côtés. Gardez la même convention de répétitions d’une séance à l’autre.',
    alternatives: [],
  },
  [id('07')]: {
    description: 'Une flexion puis une extension des jambes, debout avec une barre sur le haut du dos.',
    start: 'Réglez les supports et sécurités du rack. Placez la barre de manière stable et choisissez un écartement de pieds confortable.',
    steps: ['Sortez la barre et stabilisez vos appuis.', 'Fléchissez hanches et genoux dans une amplitude maîtrisée.', 'Repoussez le sol pour revenir debout puis replacez la barre après la série.'],
    tips: ['Gardez les pieds en appui et les genoux orientés dans la direction des pieds.', 'Apprenez le trajet avec une barre légère avant d’augmenter la charge.'],
    mistakes: ['Perdre l’équilibre vers l’avant ou l’arrière.', 'Chercher une profondeur qui fait perdre le contrôle du buste.'],
    load: 'Saisissez le poids total de la barre et des disques.',
    alternatives: [{ exerciseId: id('08'), reason: 'Poussée des jambes sur machine avec le dos soutenu ; stabilité et charge affichée non équivalentes au squat.' }],
  },
  [id('08')]: {
    description: 'Une poussée des jambes sur machine, le dos et le bassin soutenus par le siège.',
    start: 'Réglez le dossier, les appuis et les sécurités selon la machine. Posez les pieds sur la plateforme.',
    steps: ['Déverrouillez la machine selon ses consignes.', 'Fléchissez les jambes sans décoller le bassin.', 'Repoussez la plateforme de façon contrôlée puis remettez les sécurités.'],
    tips: ['Réduisez l’amplitude si votre bassin quitte le dossier.', 'Repérez le verrouillage de sécurité avant de commencer.'],
    mistakes: ['Verrouiller brutalement les genoux.', 'Laisser la plateforme descendre sans contrôle.'],
    load: 'Notez la charge affichée ou chargée selon votre machine et gardez la même convention. N’inventez pas un poids de chariot inconnu.',
    alternatives: [{ exerciseId: id('07'), reason: 'Mouvement debout avec barre : davantage d’équilibre à gérer, sans équivalence de kilogrammes avec la presse.' }],
  },
  [id('09')]: {
    description: 'Une bascule des hanches vers l’arrière, avec une barre gardée près des jambes.',
    start: 'Debout avec la barre devant les cuisses, gardez les genoux légèrement fléchis et les pieds stables.',
    steps: ['Reculez les hanches en accompagnant la barre le long des jambes.', 'Arrêtez la descente avant de perdre votre position de dos.', 'Revenez debout en ramenant les hanches, sans vous pencher en arrière.'],
    tips: ['Le but n’est pas de poser la barre au sol à chaque répétition.', 'Conservez une légère flexion des genoux plutôt que de les verrouiller.'],
    mistakes: ['Éloigner la barre des jambes.', 'Transformer le mouvement en squat en pliant beaucoup les genoux.'],
    load: 'Enregistrez le poids total de la barre et des disques.',
    alternatives: [{ exerciseId: id('10'), reason: 'Autre travail des ischio-jambiers, par flexion des genoux assise plutôt que par bascule des hanches ; ce n’est pas le même mouvement.' }],
  },
  [id('10')]: {
    description: 'Une flexion des genoux assise sur machine, contre une résistance réglable.',
    start: 'Réglez le siège et les rouleaux selon les repères de la machine, avec le bassin en appui.',
    steps: ['Pliez les genoux pour ramener le rouleau sous le siège.', 'Revenez lentement vers la position de départ sans laisser claquer les poids.'],
    tips: ['Prenez le temps de régler les appuis avant la première série.', 'Maintenez le dos contre le dossier.'],
    mistakes: ['Décoller le bassin pour tirer davantage.', 'Relâcher brusquement la résistance au retour.'],
    load: 'Saisissez la charge indiquée sur la machine ; elle ne se compare pas directement à une charge de barre.',
    alternatives: [{ exerciseId: id('09'), reason: 'Autre travail des ischio-jambiers avec une barre et une bascule des hanches ; technique et mode de résistance différents.' }],
  },
  [id('11')]: {
    description: 'Une poussée de deux haltères au-dessus de la tête, assis ou debout avec des appuis stables.',
    start: 'Placez les haltères près des épaules, poignets alignés avec les avant-bras et buste stable.',
    steps: ['Poussez les haltères vers le haut dans une amplitude confortable.', 'Redescendez près des épaules en gardant le contrôle des deux bras.'],
    tips: ['Choisissez une installation permettant de reposer les haltères sans précipitation.', 'Gardez le buste stable tout au long du mouvement.'],
    mistakes: ['Cambrer de plus en plus pour finir la série.', 'Cogner les haltères au-dessus de la tête.'],
    load: 'Notez le poids d’un seul haltère, sans additionner les deux.',
    alternatives: [],
  },
  [id('12')]: {
    description: 'Une élévation des bras sur les côtés avec deux haltères.',
    start: 'Tenez-vous stable, haltères près des cuisses et coudes légèrement fléchis.',
    steps: ['Levez les bras sur les côtés jusqu’à une hauteur confortable.', 'Redescendez lentement sans laisser tomber les haltères.'],
    tips: ['Une charge légère facilite un mouvement sans élan.', 'Gardez une flexion des coudes semblable du début à la fin.'],
    mistakes: ['Balancer le buste pour lancer les haltères.', 'Hausser fortement les épaules pour monter plus haut.'],
    load: 'Saisissez le poids d’un haltère, pas la somme des deux.',
    alternatives: [],
  },
  [id('13')]: {
    description: 'Une flexion des coudes avec des haltères, sans déplacer le buste.',
    start: 'Placez les bras près du buste, poignets confortables et pieds stables.',
    steps: ['Pliez les coudes pour monter les haltères.', 'Redescendez avec contrôle en gardant les bras près du buste.'],
    tips: ['Gardez les poignets stables plutôt que de les casser vers l’arrière.', 'Si vous alternez les bras, gardez la même façon de compter les répétitions entre séances.'],
    mistakes: ['Balancer le dos pour monter la charge.', 'Avancer fortement les coudes à chaque répétition.'],
    load: 'Notez le poids d’un seul haltère. Ne doublez pas la charge lorsque les deux bras travaillent.',
    alternatives: [],
  },
  [id('14')]: {
    description: 'Une extension des coudes vers le bas avec une poignée reliée à une poulie haute.',
    start: 'Face à la poulie, prenez des appuis stables et gardez les coudes près du buste.',
    steps: ['Étendez les coudes pour abaisser la poignée.', 'Laissez remonter la poignée en contrôlant la flexion des coudes.'],
    tips: ['Réglez la charge pour garder les épaules et le buste calmes.', 'Choisissez une poignée que vous pouvez tenir confortablement.'],
    mistakes: ['Pousser avec tout le poids du buste.', 'Laisser les coudes s’écarter et avancer à chaque répétition.'],
    load: 'Saisissez la charge affichée par la poulie, sans la doubler pour les deux bras. Comparez de préférence vos résultats sur la même machine.',
    alternatives: [],
  },
  [id('15')]: {
    description: 'Un enroulement court du haut du buste, allongé au sol.',
    start: 'Allongez-vous sur le dos, genoux fléchis et pieds au sol. Placez les mains sans tirer sur la tête.',
    steps: ['Rapprochez doucement le thorax du bassin pour décoller légèrement les épaules.', 'Reposez les épaules lentement sans prendre d’élan.'],
    tips: ['Un petit mouvement contrôlé suffit ; il n’est pas nécessaire de s’asseoir.', 'Expirez pendant la montée et gardez la nuque confortable.'],
    mistakes: ['Tirer la tête avec les mains.', 'Lancer les bras ou le buste pour monter.'],
    load: 'Indiquez uniquement un poids ajouté, si vous en utilisez un. Sans charge externe, laissez vide ; ne saisissez pas votre poids corporel.',
    alternatives: [],
  },
};

export function exerciseGuide(exercise: ExerciseCatalogItem): ExerciseGuide | undefined {
  return exercise.isCustom ? undefined : EXERCISE_GUIDES[exercise.id];
}

/** Explicit editorial order only; absent catalog rows are never fabricated. */
export function availableAlternatives(exercise: ExerciseCatalogItem, catalog: readonly ExerciseCatalogItem[]) {
  const seen = new Set([exercise.id]);
  return (exerciseGuide(exercise)?.alternatives ?? []).flatMap(link => {
    const target = catalog.find(item => item.id === link.exerciseId);
    if (!target || seen.has(target.id)) return [];
    seen.add(target.id);
    return [{ exercise: target, reason: link.reason }];
  });
}

export const loadExplanation: Record<WeightMode, string> = {
  total: 'Charge totale : notez la charge externe totale. Pour une barre, incluez la barre et les disques ; pour une machine, utilisez son indication.',
  per_hand: 'Par haltère : deux haltères de 20 kg se notent 20 kg. Logbook ne double pas cette valeur dans le tonnage enregistré.',
  additional: 'Charge ajoutée : notez uniquement le lest, sans votre poids corporel. Une charge vide reste inconnue ; 0 kg signifie explicitement aucun lest.',
};
