import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { inflateSync } from 'node:zlib';
import { test } from 'node:test';
import { BufferGeometry, BufferAttribute, Mesh, MeshBasicMaterial, Raycaster, Vector3, DoubleSide } from 'three';
import { MUSCLES, SelectionTap, sampleMuscle } from '../src/features/model3d/selection';
import { SELECTION_MODEL, muscleAtlasBase64 } from '../src/features/model3d/generated/selectionData';
import { parseViewerEvent, commandScript } from '../src/features/model3d/bridge';
const base = 'docs/m4c/meshy-anterieurs-valides';
function glb(path: string) {
  const bytes = readFileSync(path), n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.toString('utf8', 20, 20+n));
  const bin = bytes.subarray(28+n), p = doc.meshes[0].primitives[0];
  function values(index: number): number[] {
    const a = doc.accessors[index], view = doc.bufferViews[a.bufferView], start = (view.byteOffset ?? 0)+(a.byteOffset ?? 0);
    const size = a.type === 'VEC3' ? 3 : a.type === 'VEC2' ? 2 : 1;
    const result=[]; for(let i=0;i<a.count*size;i++) result.push(a.componentType===5126 ? bin.readFloatLE(start+4*i) : a.componentType===5125 ? bin.readUInt32LE(start+4*i) : bin.readUInt16LE(start+2*i));
    return result;
  }
  return { bytes, doc, p, values };
}
function decodeL8(bytes: Buffer) {
  const parts: Buffer[]=[]; let width=0,height=0;
  for(let at=8;at<bytes.length;){const n=bytes.readUInt32BE(at),tag=bytes.toString('ascii',at+4,at+8),data=bytes.subarray(at+8,at+8+n); if(tag==='IHDR'){width=data.readUInt32BE(0);height=data.readUInt32BE(4);assert.equal(data[8],8);assert.equal(data[9],0);} if(tag==='IDAT') parts.push(data);at+=n+12;}
  const packed=inflateSync(Buffer.concat(parts)),pixels=new Uint8Array(width*height);
  const paeth=(a:number,b:number,c:number)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){const i=y*width+x,a=x?pixels[i-1]!:0,b=y?pixels[i-width]!:0,c=x&&y?pixels[i-width-1]!:0,f=packed[y*(width+1)]!;pixels[i]=(packed[y*(width+1)+x+1]!+[0,a,b,Math.floor((a+b)/2),paeth(a,b,c)][f]!)&255;}
  return {pixels,width,height};
}
test('runtime UV derivative preserves all validated positions, normals, triangles, UV and neutral material',()=>{
  const runtime=glb('assets/models/meshy-m4d-uv.glb'),control=glb(`${base}/exports/meshy-eight-zones-control.glb`),original=glb('assets/models/meshy-e45e5d8.glb');
  assert.equal(runtime.bytes.length,SELECTION_MODEL.bytes);assert.equal(createHash('sha256').update(runtime.bytes).digest('hex'),SELECTION_MODEL.sha256);
  for(const field of ['POSITION','NORMAL','TEXCOORD_0'])assert.deepEqual(runtime.values(runtime.p.attributes[field]),control.values(control.p.attributes[field]));
  assert.deepEqual(runtime.values(runtime.p.indices),control.values(control.p.indices));
  assert.deepEqual(runtime.doc.materials,original.doc.materials);assert.equal(runtime.doc.images,undefined);
  const pos=runtime.values(runtime.p.attributes.POSITION),normal=runtime.values(runtime.p.attributes.NORMAL),indices=runtime.values(runtime.p.indices);
  const origPos=original.values(original.p.attributes.POSITION),origNorm=original.values(original.p.attributes.NORMAL),origIndices=original.values(original.p.indices);
  assert.equal(indices.length,origIndices.length);
  for(let i=0;i<indices.length;i++)for(let k=0;k<3;k++){assert.equal(pos[indices[i]!*3+k],origPos[origIndices[i]!*3+k]);assert.equal(normal[indices[i]!*3+k],origNorm[origIndices[i]!*3+k]);}
});
test('eight actual raycasts resolve the exact validated atlas, including anatomical left/right',()=>{
  const png=Buffer.from(muscleAtlasBase64,'base64');assert.deepEqual(png,readFileSync(`${base}/textures/muscle-ids.png`));
  const atlas=decodeL8(png),runtime=glb('assets/models/meshy-m4d-uv.glb');
  const geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(Float32Array.from(runtime.values(runtime.p.attributes.POSITION)),3));geometry.setAttribute('uv',new BufferAttribute(Float32Array.from(runtime.values(runtime.p.attributes.TEXCOORD_0)),2));geometry.setIndex(runtime.values(runtime.p.indices));
  const material=new MeshBasicMaterial({side:DoubleSide}),mesh=new Mesh(geometry,material);mesh.updateMatrixWorld();
  const witnesses=JSON.parse(readFileSync(`${base}/picking-witnesses.json`,'utf8'));
  for(const w of witnesses){const p=new Vector3(w.point.x,w.point.y,w.point.z),n=new Vector3(...w.normal as [number,number,number]).normalize();const hit=new Raycaster(p.clone().addScaledVector(n,.025),n.clone().negate(),0,.1).intersectObject(mesh)[0];assert.ok(hit);assert.equal(sampleMuscle(hit.uv,atlas.pixels,atlas.width,atlas.height)?.id,w.expectedId);assert.equal(Math.sign(p.x),w.expectedId.includes('.left')?1:-1);}
  const neutralHit = new Raycaster(new Vector3(0,.85,2),new Vector3(0,0,-1),0,4).intersectObject(mesh)[0];
  assert.ok(neutralHit, 'Neutral head must be a real first surface hit');
  assert.equal(sampleMuscle(neutralHit.uv,atlas.pixels,atlas.width,atlas.height),null);
  geometry.dispose();material.dispose();
  assert.equal(sampleMuscle({x:0,y:0},atlas.pixels,atlas.width,atlas.height),null);
  for(const uv of [undefined,{x:NaN,y:0},{x:-.1,y:0},{x:1.01,y:0}])assert.equal(sampleMuscle(uv,atlas.pixels,atlas.width,atlas.height),null);
  assert.equal(sampleMuscle({x:.49,y:0},Uint8Array.from([1,2]),2,1)?.code,1);assert.equal(sampleMuscle({x:.5,y:0},Uint8Array.from([1,2]),2,1)?.code,2);
});
test('runtime atlas changes only the two approved anterior zones and preserves six restored muscles',()=>{
  const before=decodeL8(readFileSync('docs/m4c/meshy-posterieurs-harmonises/textures/muscle-ids.png'));
  const after=decodeL8(Buffer.from(muscleAtlasBase64,'base64'));
  assert.equal(after.width,before.width);assert.equal(after.height,before.height);
  const protectedCodes=new Set([1,2,4,5,7,8]),allowedCodes=new Set([0,3,6]);
  let changesLeft=0,changesRight=0;
  for(let i=0;i<after.pixels.length;i++){
    const a=before.pixels[i]!,b=after.pixels[i]!;
    if(protectedCodes.has(a)||protectedCodes.has(b))assert.equal(a,b,`Protected muscle changed at texel ${i}`);
    if(a!==b){assert.ok(allowedCodes.has(a)&&allowedCodes.has(b));if(a===3||b===3)changesLeft++;if(a===6||b===6)changesRight++;}
  }
  assert.ok(changesLeft>0&&changesRight>0,'Both approved anterior changes must actually reach the runtime atlas');
});
test('selection bridge accepts exactly eight IDs and null; reset is a bounded command',()=>{
  for(const m of MUSCLES) assert.deepEqual(parseViewerEvent(JSON.stringify({version:1,type:'selection',muscleId:m.id})),{version:1,type:'selection',muscleId:m.id});
  for(const id of [0,9,'deltoid.left','bogus',{},undefined])assert.equal(parseViewerEvent(JSON.stringify({version:1,type:'selection',muscleId:id})),null);
  assert.deepEqual(parseViewerEvent('{"version":1,"type":"selection","muscleId":null}'),{version:1,type:'selection',muscleId:null});
  assert.match(commandScript('reset-selection'),/command\("reset-selection"\)/);
});
test('brief taps survive jitter; drag-return, pinch, hold, cancellation and residual releases never select',()=>{
  const tap=new SelectionTap();tap.down(1,10,10,0);tap.move(1,12,12);assert.equal(tap.up(1,12,12,100),true);
  tap.down(1,10,10,0);tap.move(1,30,10);assert.equal(tap.up(1,10,10,100),false);
  tap.down(1,10,10,0);tap.down(2,30,10,20);assert.equal(tap.up(2,30,10,50),false);assert.equal(tap.up(1,10,10,80),false);
  tap.down(1,10,10,0);assert.equal(tap.up(1,10,10,351),false);
  tap.down(1,10,10,0);assert.equal(tap.up(1,30,10,30),false);
  tap.down(1,10,10,0);tap.cancel(1);assert.equal(tap.up(1,10,10,30),false);
  tap.down(1,10,10,0);tap.clear();assert.equal(tap.up(1,10,10,30),false);
});
