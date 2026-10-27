# Antérieurs bilatéraux — gauche proposé, droit validé inchangé

[Rapport et rendus](../../M4C_ANTERIEURS_BILATERAUX.md).

Base immuable : `../experience-anterieur-droit/`, commit `7b69e3d`.
Seul l'ID 3 est modifié dans cette nouvelle version ; l'ID 6 reste identique.

Reproduction depuis la racine du dépôt (Python/NumPy/SciPy/Pillow, Blender 4.3.2) :

```sh
blender -b --python-exit-code 1 --python tools/m4c/project_bilateral_anterior.py
python tools/m4c/bake_bilateral_anterior.py prepare
blender -b --python-exit-code 1 --python tools/m4c/project_bilateral_anterior.py -- --visibility
python tools/m4c/bake_bilateral_anterior.py finish
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/experience-anterieurs-bilateraux
blender -b --python-exit-code 1 --python tools/m4c/project_bilateral_anterior.py -- --measure
blender -b --python-exit-code 1 --python tools/m4c/render_bilateral_anterior.py
python tools/m4c/compose_bilateral_anterior.py
python tools/m4c/audit_bilateral_anterior.py
node tools/m4c/audit-picking.mjs docs/m4c/experience-anterieurs-bilateraux
```

Le dernier contrôle nécessite les dépendances verrouillées du projet. Projection,
textures et rendus sont calculés localement, sans CDN ni service payant.
Le cache de surface partagé du premier prototype est extérieur au dépôt.
La vérification d'identité lit les références Git ; aucun historique n'est modifié.
