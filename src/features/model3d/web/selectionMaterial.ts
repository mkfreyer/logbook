import { Color, DataTexture, Mesh, MeshStandardMaterial, NearestFilter, NoColorSpace, RedFormat, UnsignedByteType, type Group } from 'three';
import { muscleAtlasBase64, SELECTION_MODEL } from '../generated/selectionData';
import { SELECTION_COLOR } from '../selection';

/** Decode PNG once, then keep only one byte per texel on CPU and GPU. No mipmaps. */
export async function loadSelectionAtlas() {
  const image = new Image();
  image.src = `data:image/png;base64,${muscleAtlasBase64}`;
  await image.decode();
  if (image.width !== SELECTION_MODEL.width || image.height !== SELECTION_MODEL.height) throw Error('Atlas invalide');
  const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  if (!context) throw Error('Atlas indisponible');
  context.drawImage(image, 0, 0);
  const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
  const pixels = new Uint8Array(image.width * image.height);
  for (let i = 0; i < pixels.length; i++) {
    const code = rgba[i * 4]!;
    if (code > 8) throw Error('Identifiant invalide');
    pixels[i] = code;
  }
  canvas.width = canvas.height = 0; image.src = '';
  const texture = new DataTexture(pixels, SELECTION_MODEL.width, SELECTION_MODEL.height, RedFormat, UnsignedByteType);
  texture.flipY = false; texture.colorSpace = NoColorSpace;
  texture.minFilter = texture.magFilter = NearestFilter; texture.generateMipmaps = false; texture.needsUpdate = true;
  return { pixels, texture, width: SELECTION_MODEL.width, height: SELECTION_MODEL.height };
}
export function installSelectionMaterial(root: Group, texture: DataTexture) {
  const selected = { value: 0 }, color = { value: new Color(SELECTION_COLOR) };
  root.traverse(object => {
    if (!(object instanceof Mesh) || !(object.material instanceof MeshStandardMaterial)) return;
    const material = object.material;
    // Explicit varying: no dependency on a base-color map to enable TEXCOORD_0.
    material.defines = { ...material.defines, USE_UV: '' };
    material.onBeforeCompile = shader => {
      shader.uniforms.muscleAtlas = { value: texture };
      shader.uniforms.selectedMuscle = selected; shader.uniforms.selectionColor = color;
      shader.vertexShader = 'varying vec2 vMuscleUv;\n' + shader.vertexShader;
      shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvMuscleUv = uv;');
      shader.fragmentShader = 'uniform sampler2D muscleAtlas;\nuniform float selectedMuscle;\nuniform vec3 selectionColor;\nvarying vec2 vMuscleUv;\n' + shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>', `#include <color_fragment>
        if (selectedMuscle > 0.5) {
          float muscleCode = floor(texture2D(muscleAtlas, vMuscleUv).r * 255.0 + 0.5);
          if (abs(muscleCode - selectedMuscle) < 0.5) diffuseColor.rgb = selectionColor;
        }`);
    };
    material.customProgramCacheKey = () => 'logbook-muscle-selection-v1'; material.needsUpdate = true;
  });
  return selected;
}
