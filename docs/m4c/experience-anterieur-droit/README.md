# Prototype local — antérieur droit uniquement

[Rapport, comparatifs, limites et sources](../../M4C_PROTOTYPE_ANTERIEUR_DROIT_LOCAL.md).

Base `168ac61` / `06fa665` ; géométrie Meshy `e45e5d8` intacte.
Seul le bord côté pectoral du masque ID 6 change. Sept autres masques identiques.
Les branches validées ne sont pas modifiées. Aucune intégration applicative.

Reproduction depuis la racine du dépôt, avec Python/NumPy/SciPy/Pillow et Blender
4.3.2 disponibles :

```sh
python tools/m4c/experimental_anterior.py prepare
blender -b --python-exit-code 1 --python tools/m4c/project_experimental_anterior.py
python tools/m4c/experimental_anterior.py finish
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/experience-anterieur-droit
blender -b --python-exit-code 1 --python tools/m4c/render_experimental_anterior.py
python tools/m4c/compose_experimental_anterior.py
python tools/m4c/audit_experimental_anterior.py
node tools/m4c/audit-picking.mjs docs/m4c/experience-anterieur-droit
```

Le dernier contrôle exige les dépendances verrouillées du projet. Aucun accès
réseau n'est utilisé par les étapes de projection et de rendu.
