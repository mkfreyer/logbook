import {
  AmbientLight, Box3, DirectionalLight, Group, HemisphereLight, Mesh, PerspectiveCamera,
  Raycaster, Scene, Vector2, Vector3, WebGLRenderer, AgXToneMapping, SRGBColorSpace, TOUCH,
  type BufferAttribute, type BufferGeometry, type InterleavedBufferAttribute, type Material,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { cameraFraming, MIN_POLAR_ANGLE, MAX_POLAR_ANGLE, VIEW_FOV_DEGREES } from '../camera';
import { SELECTION_MODEL } from '../generated/selectionData';
import { SelectionTap, sampleMuscle, type MuscleId } from '../selection';
import { loadSelectionAtlas, installSelectionMaterial } from './selectionMaterial';
import { MODEL } from '../model';
import type { SurfaceHit, ViewerCommand, ViewerEvent } from '../bridge';

interface ViewerApi {
  command(command: ViewerCommand): void;
  snapshot(): Record<string, unknown>;
}
declare global {
  interface Window {
    ReactNativeWebView?: { postMessage(text: string): void };
    LogbookModelViewer?: ViewerApi;
  }
}
const post = (event: ViewerEvent) => window.ReactNativeWebView?.postMessage(JSON.stringify(event));
function disposeModel(root: Group) {
  const geometries = new Set<BufferGeometry>(), materials = new Set<Material>();
  root.traverse(object => {
    if (!(object instanceof Mesh)) return;
    geometries.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) materials.add(material);
  });
  geometries.forEach(value => value.dispose());
  materials.forEach(value => value.dispose());
  root.removeFromParent();
}
function modelInformation(root: Group) {
  let triangles = 0, geometryBytes = 0;
  const arrays = new Set<ArrayBufferView>();
  root.traverse(object => {
    if (!(object instanceof Mesh)) return;
    triangles += (object.geometry.index?.count ?? object.geometry.getAttribute('position').count) / 3;
    for (const attribute of [...Object.values(object.geometry.attributes), ...(object.geometry.index ? [object.geometry.index] : [])]) {
      const array = (attribute as InterleavedBufferAttribute).isInterleavedBufferAttribute
        ? (attribute as InterleavedBufferAttribute).data.array : (attribute as BufferAttribute).array;
      if (!arrays.has(array)) { arrays.add(array); geometryBytes += array.byteLength; }
    }
  });
  return { triangles, geometryBytes };
}
function decodeModel() {
  const element = document.getElementById('model-data');
  const text = element?.textContent;
  element?.remove();
  if (!text) throw new Error('Modèle local absent.');
  const binary = atob(text);
  if (binary.length !== SELECTION_MODEL.bytes) throw new Error('Modèle local incomplet.');
  const data = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) data[i] = binary.charCodeAt(i);
  return data.buffer;
}
async function start() {
  let disposed = false, frame = 0, renderCount = 0, root: Group | null = null;
  let atlas: Awaited<ReturnType<typeof loadSelectionAtlas>> | null = null;
  let selectedUniform: { value: number } | null = null, selectedMuscle: MuscleId | null = null;
  function select(muscle: ReturnType<typeof sampleMuscle>) {
    selectedMuscle = muscle?.id ?? null;
    if (selectedUniform) selectedUniform.value = muscle?.code ?? 0;
    invalidate(); post({ version: 1, type: 'selection', muscleId: selectedMuscle });
  }
  let loaded = false, geometryBytes = 0, triangles = 0;
  const renderer = new WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'default' });
  renderer.setClearColor(0x050d16);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = AgXToneMapping;
  renderer.toneMappingExposure = 1.1;
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-label', 'Mannequin 3D : un doigt pour tourner, deux doigts pour zoomer.');
  canvas.setAttribute('role', 'img');
  document.body.appendChild(canvas);
  const scene = new Scene();
  const camera = new PerspectiveCamera(VIEW_FOV_DEGREES, 1, 0.01, 100);
  camera.up.set(0, 1, 0);
  scene.add(new AmbientLight(0xffffff, 0.5), new HemisphereLight(0xe1edff, 0x162030, 1.6));
  for (const [x, y, z, intensity] of [[-3, 4, 4, 3], [3, 1, 2, 1.3], [0, 3, -3, 2.2]]) {
    const light = new DirectionalLight(0xffffff, intensity!);
    light.position.set(x!, y!, z!); scene.add(light);
  }
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = 0.12;
  controls.rotateSpeed = 0.65; controls.zoomSpeed = 0.8; controls.panSpeed = 0.7;
  controls.minPolarAngle = MIN_POLAR_ANGLE; controls.maxPolarAngle = MAX_POLAR_ANGLE;
  controls.touches.ONE = TOUCH.ROTATE; controls.touches.TWO = TOUCH.DOLLY_PAN;
  controls.screenSpacePanning = true;
  let size = new Vector3(1, 2, 1), framing = cameraFraming(size, 1);
  function clampTarget() {
    const previous = controls.target.clone();
    controls.target.x = 0; controls.target.z = 0;
    controls.target.y = Math.max(-size.y * 0.46, Math.min(size.y * 0.46, controls.target.y));
    camera.position.sub(previous.sub(controls.target));
    camera.lookAt(controls.target);
  }
  function draw() {
    frame = 0;
    if (disposed || document.hidden || !loaded) return;
    controls.update(); clampTarget();
    renderer.render(scene, camera); renderCount++;
  }
  function invalidate() {
    if (!disposed && loaded && !document.hidden && !frame) frame = requestAnimationFrame(draw);
  }
  controls.addEventListener('change', invalidate);
  function clearMotion() {
    controls.enableDamping = false; controls.update(); controls.enableDamping = true;
  }
  function overview() {
    if (!loaded || disposed) return;
    // Clear pending damping/pan before restoring an exact front overview.
    clearMotion();
    controls.target.set(0, 0, 0); camera.position.set(0, 0, framing.fitDistance);
    controls.update(); controls.saveState(); invalidate();
  }
  function resize() {
    if (disposed) return;
    const width = Math.max(1, document.documentElement.clientWidth), height = Math.max(1, document.documentElement.clientHeight);
    renderer.setSize(width, height, false); camera.aspect = width / height;
    framing = cameraFraming(size, camera.aspect);
    controls.minDistance = framing.minDistance; controls.maxDistance = framing.maxDistance;
    camera.near = framing.near; camera.far = framing.far; camera.updateProjectionMatrix();
    if (loaded) { controls.update(); clampTarget(); invalidate(); }
  }
  const observer = new ResizeObserver(resize); observer.observe(document.documentElement);
  const onVisibility = () => { if (document.hidden) { if (frame) cancelAnimationFrame(frame); frame = 0; } else invalidate(); };
  document.addEventListener('visibilitychange', onVisibility);
  const onContextLost = (event: Event) => {
    event.preventDefault();
    if (!disposed) post({ version: 1, type: 'error', message: 'Le rendu 3D a été interrompu. Réessayez.' });
  };
  canvas.addEventListener('webglcontextlost', onContextLost);
  const raycaster = new Raycaster(), pointer = new Vector2(), taps = new SelectionTap();
  const down = (event: PointerEvent) => taps.down(event.pointerId, event.clientX, event.clientY, event.timeStamp);
  const move = (event: PointerEvent) => taps.move(event.pointerId, event.clientX, event.clientY);
  const up = (event: PointerEvent) => {
    if (!taps.up(event.pointerId, event.clientX, event.clientY, event.timeStamp) || !root || !loaded || !atlas) return;
    const rect = canvas.getBoundingClientRect();
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObject(root, true)[0];
    if (!hit || !(hit.object instanceof Mesh) || hit.faceIndex == null) { select(null); return; }
    select(sampleMuscle(hit.uv, atlas.pixels, atlas.width, atlas.height));
    const point = hit.object.worldToLocal(hit.point.clone());
    const surface: SurfaceHit = { assetId: MODEL.id, coordinateSpace: 'mesh-local', point: { x: point.x, y: point.y, z: point.z }, faceIndex: hit.faceIndex };
    if (hit.uv) surface.uv = { x: hit.uv.x, y: hit.uv.y };
    post({ version: 1, type: 'surface-hit', hit: surface });
  };
  const cancel = (event: PointerEvent) => taps.cancel(event.pointerId);
  canvas.addEventListener('pointerdown', down, true); canvas.addEventListener('pointermove', move, true);
  canvas.addEventListener('pointerup', up, true); canvas.addEventListener('pointercancel', cancel, true);
  function dispose() {
    if (disposed) return;
    disposed = true; loaded = false; taps.clear(); selectedMuscle = null;
    atlas?.texture.dispose(); atlas = null; selectedUniform = null;
    if (frame) cancelAnimationFrame(frame); frame = 0;
    observer.disconnect(); controls.dispose();
    document.removeEventListener('visibilitychange', onVisibility);
    canvas.removeEventListener('webglcontextlost', onContextLost);
    canvas.removeEventListener('pointerdown', down, true); canvas.removeEventListener('pointermove', move, true);
    canvas.removeEventListener('pointerup', up, true); canvas.removeEventListener('pointercancel', cancel, true);
    window.removeEventListener('pagehide', dispose);
    if (root) { disposeModel(root); root = null; }
    scene.clear(); renderer.renderLists.dispose(); renderer.dispose(); renderer.forceContextLoss(); canvas.remove();
  }
  window.addEventListener('pagehide', dispose);
  window.LogbookModelViewer = {
    command(command) {
      if (command === 'dispose') { dispose(); return; }
      if (disposed || !loaded) return;
      if (command === 'reset-selection') select(null);
      if (command === 'overview') overview();
      if (command === 'front') {
        const distance = controls.getDistance(), target = controls.target.clone();
        clearMotion(); controls.target.copy(target); camera.position.copy(target).add(new Vector3(0, 0, distance));
        controls.update(); invalidate();
      }
    },
    snapshot: () => ({ disposed, loaded, renderCount, triangles, geometryBytes, selectedMuscle, atlasBytes: atlas?.pixels.byteLength ?? 0,
      camera: camera.position.toArray(), target: controls.target.toArray(), size: size.toArray(),
      minDistance: controls.minDistance, maxDistance: controls.maxDistance, distance: controls.getDistance(),
      polarAngle: controls.getPolarAngle(), azimuth: controls.getAzimuthalAngle(),
      geometries: renderer.info.memory.geometries, textures: renderer.info.memory.textures,
      renderedTriangles: renderer.info.render.triangles, contextLost: renderer.getContext().isContextLost(),
      projectedBounds: root ? new Box3().setFromObject(root) : null }),
  };
  try {
    const decodedAtlas = await loadSelectionAtlas();
    if (disposed) { decodedAtlas.texture.dispose(); return; }
    atlas = decodedAtlas;
    const parsed = await new GLTFLoader().parseAsync(decodeModel(), '');
    if (disposed) { disposeModel(parsed.scene); return; }
    root = parsed.scene;
    selectedUniform = installSelectionMaterial(root, atlas.texture);
    const info = modelInformation(root); triangles = info.triangles; geometryBytes = info.geometryBytes;
    if (triangles !== MODEL.triangles) throw new Error('Le mannequin ne correspond pas à la version validée.');
    const bounds = new Box3().setFromObject(root), center = bounds.getCenter(new Vector3());
    size = bounds.getSize(new Vector3());
    root.position.sub(center); scene.add(root);
    loaded = true; resize(); overview();
    post({ version: 1, type: 'ready', triangles, geometryBytes });
  } catch {
    dispose(); post({ version: 1, type: 'error', message: 'Le mannequin 3D ne peut pas être affiché. Réessayez.' });
  }
}
void start().catch(() => post({ version: 1, type: 'error', message: 'Le rendu 3D est indisponible sur cet appareil.' }));
