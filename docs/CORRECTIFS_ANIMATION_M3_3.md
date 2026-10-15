# M3.3 — Correctif du Switch conservé, modifications de swipe retirées

Le propriétaire a confirmé que le correctif du Switch sonore de `262a844` fonctionne sur son iPhone. Ce correctif est conservé à l’identique. Les modifications de navigation de ce commit et de `86c5119` sont retirées à sa demande ; suivre [le guide courant](NAVIGATION_M3_2_RESTAUREE.md) pour tester le retour à la navigation M3.2 sur la branche M3.3.

## Switch sonore conservé

Le Switch devenait désactivé pendant chaque écriture SQLite et sa valeur contrôlée restait ancienne jusqu’au retour de la base. Cela pouvait rendre le contrôle translucide sur iOS et forcer un retour visuel pendant le mouvement natif. Le texte temporaire « Enregistrement… » pouvait aussi déplacer la ligne.

Le code conservé acquitte immédiatement le choix visuel, laisse le contrôle actif pendant les écritures et garde une aide stable. Le fond iOS est explicite ; l’apparence du pouce reste native.

Le repository sérialise les sauvegardes. Une réponse ancienne ne remplace pas une intention plus récente ; un doublon de la même intention n’ajoute pas d’écriture. Si la dernière demande échoue, le contrôle revient à la dernière valeur confirmée avec une erreur et une relecture possible. Le son reste coupé pendant une écriture non confirmée ou une erreur.

Quitter Paramètres n’annule pas les écritures du provider de l’application. Au redémarrage, SQLite fournit la dernière valeur commise. Les tests d’appuis rapides, de persistance, d’erreurs et de son restent exécutés.

## Navigation

`UniversePager.tsx` et `app/index.tsx` retrouvent exactement `289cad0`. Les reçus de sélection et la compensation sont supprimés ; le bloc inférieur de l’accueil retrouve sa marge automatique. Aucun nouveau mécanisme ne remplace ceux retirés.

Les anciens tests et protocoles de reçus/compensation ne s’appliquent plus. Le [guide de navigation rétablie](NAVIGATION_M3_2_RESTAUREE.md) explique les comparaisons Git, les éléments M3.3 préservés, les commandes Windows et les essais iPhone. M3.4 reste en attente du retour du propriétaire.
