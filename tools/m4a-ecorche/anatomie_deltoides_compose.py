"""Same-camera anatomical-boundary comparisons and direct P4 neutral controls."""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_comparison(before, after):
    a = np.array(Image.open(before).convert('RGB')).astype(np.int16)
    b = np.array(Image.open(after).convert('RGB')).astype(np.int16)
    d = np.abs(a - b)
    return {'changed_pixels_percent': float(np.any(d, axis=2).mean() * 100),
            'max_channel_difference_8bit': int(d.max()),
            'mean_channel_difference_8bit': float(d.mean()),
            'before_sha256': sha(before), 'after_sha256': sha(after)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    p.add_argument('--baseline-asset', type=Path, required=True)
    args = p.parse_args()
    asset, baseline = args.asset.resolve(), args.baseline_asset.resolve()
    root = asset / 'renders'
    verification = json.loads((asset / 'verification.json').read_text())
    assert verification['all_original_surface_vertices_unchanged']
    assert verification['all_six_surface_landmarks_assigned_to_intended_regions']
    helper_path = Path(__file__).with_name('frontieres_deltoides_compose.py')
    spec = importlib.util.spec_from_file_location('render_layout', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    old = {r['file']: r for r in json.loads((baseline / 'renders/after/metadata.json').read_text())['frames']}
    after = {r['file']: r for r in json.loads((root / 'after/metadata.json').read_text())['frames']}
    comparisons = []
    for name, rec in after.items():
        for key in ['camera_matrix', 'ortho_scale', 'resolution']:
            assert rec[key] == old[name][key], (name, key)
        assert sha(baseline / 'renders/after' / name) == old[name]['sha256']
        assert sha(root / 'after' / name) == rec['sha256']
        comparisons.append({'file': name, 'same_camera_resolution_lighting': True,
                            'before_source': os.path.relpath(baseline / 'renders/after' / name, root),
                            'before_sha256': old[name]['sha256'], 'after_sha256': rec['sha256']})
    neutral = []
    for view in ['epaule-profil', 'epaule-droite', 'epaule-face-droite', 'epaule-face-gauche']:
        name = view + '.png'
        neutral.append({'file': name, 'reference': '990201f',
                        **pixel_comparison(baseline / 'renders/neutral' / name, root / 'neutral' / name)})
    p4_root = baseline.parent / 'ecorche-beatriz-combinaison-p4-p5/renders'
    direct_p4 = []
    for view in ['epaule-profil', 'epaule-droite']:
        name = view + '.png'
        direct_p4.append({'file': name, 'reference': '0ab3d83 original P4 + P5',
                          **pixel_comparison(p4_root / name, root / 'neutral' / name)})
    entries = []
    for view, title in [('epaule-profil', 'Profil'), ('epaule-droite', 'Trois quarts'),
                        ('epaule-arriere', 'Arrière oblique'), ('epaules-face', 'Face')]:
        entries += [(baseline / 'renders/after' / (view + '.png'), title + ' — 990201f'),
                    (root / 'after' / (view + '.png'), title + ' — répartition en éventail')]
    plates = [helper.plate(root, 'comparatif-anatomie.png', 'Placement avant / après — mêmes caméras', entries)]
    views = [('epaule-face-droite', 'Épaule droite — face'), ('epaule-face-gauche', 'Épaule gauche — face'),
             ('epaule-droite', 'Épaule droite — trois quarts'), ('epaule-gauche', 'Épaule gauche — trois quarts'),
             ('epaule-profil', 'Profil'), ('epaule-arriere', 'Arrière oblique'),
             ('epaules-face', 'Deux épaules — face'), ('epaules-dos', 'Deux épaules — dos')]
    plates.append(helper.plate(root, 'controle-six-zones-anatomiques.png', 'Antérieur enveloppant / dôme latéral / postérieur',
                               [(root / 'after' / (view + '.png'), title) for view, title in views]))
    entries = []
    for view, title in [('epaule-profil', 'Profil'), ('epaule-droite', 'Trois quarts')]:
        entries += [(p4_root / (view + '.png'), title + ' — P4/P5 original 0ab3d83'),
                    (root / 'neutral' / (view + '.png'), title + ' — nouvelles zones, neutre')]
    plates.append(helper.plate(root, 'comparatif-neutre-P4.png', 'Contrôle neutre direct — géométrie P4 conservée', entries,
                               color_legend=False))
    plates.append(helper.plate(root, 'epaules-face-neutres.png', 'Deux épaules — matériau mat neutre', [
        (root / 'neutral/epaule-face-droite.png', 'Épaule droite'),
        (root / 'neutral/epaule-face-gauche.png', 'Épaule gauche')], color_legend=False))
    (root / 'comparisons.json').write_text(json.dumps({
        'baseline_commit': '990201f214c91272a5274a53c28e049670128064',
        'before_after_views': comparisons, 'neutral_checks': neutral,
        'direct_original_P4_neutral_checks': direct_p4,
        'plates': plates, 'pixels_repainted': False,
        'compositor_sha256': sha(Path(__file__)), 'layout_helper_sha256': sha(helper_path),
    }, indent=2) + '\n')
    preview = root / 'preview'
    if preview.exists():
        shutil.rmtree(preview)
    print('COMPOSED', json.dumps({'neutral': neutral, 'direct_P4': direct_p4, 'plates': len(plates)}), flush=True)


if __name__ == '__main__':
    main()
