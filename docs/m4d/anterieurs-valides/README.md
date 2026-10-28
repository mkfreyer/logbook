# M4D-A — captures et contrôles des antérieurs approuvés

[Rapport](../../M4D_ANTERIEURS_VALIDES_INTEGRATION.md) ·
[Guide Windows → iPhone](../../M4D_ANTERIEURS_VALIDES_GUIDE_IPHONE_WINDOWS.md).

Source M4C : `d552e23`, masques validés `09c61ab`, six autres masques `06fa665`.
Le GLB applicatif est régénéré par le pipeline existant avec le matériau neutre.

Les captures proviennent du moteur WebGL local dans Chromium/SwiftShader,
pas d'un véritable iPhone. Les deux vues de face sont deux états successifs
avec une sélection active à la fois ; le comparatif juxtapose les captures.
Les recadrages ne repeignent aucun pixel de la surface.

Commandes de vérification depuis la racine, avec les dépendances verrouillées :

```sh
node tools/m4d/build-selection.mjs
npm run viewer:build
npm run viewer:check
npm run typecheck
npm test
npm run test:selection-browser
npm run test:viewer-browser
npm run export:ios
python tools/m4d/compose-captures.py docs/m4d/anterieurs-valides
python tools/m4d/compose-approved-anteriors.py
python tools/m4c/audit_validated_anterior.py --runtime docs/m4d/anterieurs-valides/asset-verification.json
```

Le test général WebGL écrit ses résultats dans `M4B_ARTIFACT_DIR` (ou dans un
dossier temporaire par défaut) ; `viewer-regression.json` en conserve le résultat
de cette livraison. Les journaux et les diagnostics Expo sont décrits dans le
rapport, avec distinction entre contrôle hors ligne et recommandations en ligne.
