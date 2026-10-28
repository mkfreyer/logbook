/** Real WebGL and actual touch events, software Chromium. Not an iPhone certification. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { Box3, PerspectiveCamera, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { buildViewerDocument } from '../../src/features/model3d/document';
import { MUSCLES } from '../../src/features/model3d/selection';
async function main() {
const out = process.env.M4D_ARTIFACT_DIR ?? 'docs/m4d/anterieurs-valides';
await mkdir(out,{recursive:true});
const glb=await readFile('assets/models/meshy-m4d-uv.glb');
const scene=await new GLTFLoader().parseAsync(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength),'');
const center=new Box3().setFromObject(scene.scene).getCenter(new Vector3());
const witnesses=JSON.parse(await readFile('docs/m4c/meshy-anterieurs-valides/picking-witnesses.json','utf8'));
const html=buildViewerDocument(glb.toString('base64'));
const server=createServer((_req,res)=>{res.writeHead(200,{'Content-Type':'text/html'});res.end(html);});
await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));
const addr=server.address();assert.ok(addr&&typeof addr!=='string');const origin=`http://127.0.0.1:${addr.port}`;
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
try {
const context=await browser.newContext({viewport:{width:430,height:760},deviceScaleFactor:1,hasTouch:true,isMobile:true});
const errors:string[]=[],requests:string[]=[];
await context.route('**/*',async route=>{const url=route.request().url();requests.push(url);if(!url.startsWith(origin))throw Error(`External resource ${url}`);await route.continue();});
await context.addInitScript('window.events=[];window.ReactNativeWebView={postMessage(text){window.events.push(JSON.parse(text));}}');
const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
const snapshot=()=>page.evaluate(()=>window.LogbookModelViewer!.snapshot());
const command=(c:'overview'|'front'|'reset-selection'|'dispose')=>page.evaluate(c=>window.LogbookModelViewer!.command(c),c);
const selected=async()=> (await snapshot()).selectedMuscle;
function sameCoordinates(a:unknown,b:unknown){
 assert.ok(Array.isArray(a)&&Array.isArray(b));assert.equal(a.length,b.length);
 // OrbitControls may round-trip spherical floats on an invalidated frame.
 for(let i=0;i<a.length;i++)assert.ok(typeof a[i]==='number'&&typeof b[i]==='number'&&Math.abs(a[i]-b[i])<1e-7);
}
const cdp=await context.newCDPSession(page);
type P={x:number;y:number;id:number};
// With software WebGL, inertia may still run after a fixed delay. Projecting a
// witness before it settles would target a different surface at touch release.
async function settleCamera(){
 let previous=(await snapshot()).camera as number[],stable=0;
 for(let i=0;i<100;i++){
  await page.waitForTimeout(200);const current=(await snapshot()).camera as number[];
  if(current.every((value,k)=>Math.abs(value-previous[k]!)<1e-8))stable++;else stable=0;
  if(stable>=3)return;previous=current;
 }
 throw Error('Camera inertia did not settle in the test environment');
}
async function gesture(start:P[],end:P[],steps=3){
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:start});
 for(let i=1;i<=steps;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:start.map((p,k)=>({...p,x:p.x+(end[k]!.x-p.x)*i/steps,y:p.y+(end[k]!.y-p.y)*i/steps}))});await page.waitForTimeout(10);}
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(200);await settleCamera();
}
async function tap(x:number,y:number){const timestamp=Date.now()/1000;await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,id:1}],timestamp});await page.waitForTimeout(45);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[],timestamp:timestamp+.06});await page.waitForTimeout(180);}
async function orient(angle:number){
 for(let i=0;i<6;i++){let delta=angle-((await snapshot()).azimuth as number);while(delta>Math.PI)delta-=2*Math.PI;while(delta< -Math.PI)delta+=2*Math.PI;if(Math.abs(delta)<.12)break;
 const dx=Math.max(-150,Math.min(150,-delta*760/(2*Math.PI*.65)));
 await gesture([{x:215,y:450,id:1}],[{x:215+dx,y:450,id:1}]);}
}
async function screenPoint(point:{x:number;y:number;z:number}){
 const s=await snapshot(),c=new PerspectiveCamera(36,430/760,.01,100);c.position.fromArray(s.camera as number[]);c.lookAt(new Vector3().fromArray(s.target as number[]));c.updateMatrixWorld();c.updateProjectionMatrix();
 const p=new Vector3(point.x,point.y,point.z).sub(center).project(c);return {x:(p.x+1)*215,y:(1-p.y)*380};
}
await page.goto(origin);await page.waitForFunction(()=>window.LogbookModelViewer?.snapshot().loaded===true);await page.waitForTimeout(750);
await context.setOffline(true);
const initial=await snapshot();assert.equal(initial.selectedMuscle,null);assert.equal(initial.atlasBytes,2048*2048);
await page.screenshot({path:`${out}/neutre-vue-generale.png`});
// Actual two-finger zoom and vertical framing, preserving the production controls.
await gesture([{x:150,y:430,id:1},{x:280,y:430,id:2}],[{x:80,y:430,id:1},{x:350,y:430,id:2}]);
await gesture([{x:150,y:400,id:1},{x:280,y:400,id:2}],[{x:150,y:550,id:1},{x:280,y:550,id:2}]);
assert.equal(await selected(),null);
const checks=[];
for(const witness of witnesses){
 const angle=witness.expectedId.endsWith('.lateral') ? (witness.expectedId.includes('.left.') ? Math.PI/2 : -Math.PI/2) : Math.atan2(witness.normal[0],witness.normal[2]);console.log(`Checking ${witness.expectedId}`);await orient(angle);
 await command('reset-selection');await page.waitForTimeout(200);
 const p=await screenPoint(witness.point);assert.ok(p.x>0&&p.x<430&&p.y>0&&p.y<760,JSON.stringify(p));
 const before=await page.screenshot();await tap(p.x,p.y);
 assert.equal(await selected(),witness.expectedId,JSON.stringify({p,s:await snapshot()}));
 const after=await page.screenshot({path:`${out}/selection-${witness.expectedId}.png`});assert.equal(after.equals(before),false,'Selection must change visible pixels');
 const record={id:witness.expectedId,label:MUSCLES.find(m=>m.id===witness.expectedId)!.name,touch:p,azimuth:(await snapshot()).azimuth};checks.push(record);
 // A camera gesture must not change the active ID.

 await command('reset-selection');await page.waitForTimeout(200);assert.equal(await selected(),null);
 const resetImage=await page.screenshot(checks.length===1?{path:`${out}/selection-reinitialisee.png`}:{});assert.equal(resetImage.equals(after),false,'Reset must remove visible highlight');
}
// Compare the two approved anteriors from the EXACT same front camera, using
// the existing single-selection behavior. No new multi-selection UI/shader.
await command('front');await settleCamera();const faceSelections=[];
for(const [id,side] of [['deltoid.right.anterior','droit'],['deltoid.left.anterior','gauche']] as const){
 const w=witnesses.find((value:{expectedId:string})=>value.expectedId===id);assert.ok(w);
 await command('reset-selection');await page.waitForTimeout(200);const p=await screenPoint(w.point);await tap(p.x,p.y);assert.equal(await selected(),id);
 const s=await snapshot();faceSelections.push({id,camera:s.camera,target:s.target});await page.screenshot({path:`${out}/face-anterieur-${side}.png`});
}
sameCoordinates(faceSelections[0]!.camera,faceSelections[1]!.camera);sameCoordinates(faceSelections[0]!.target,faceSelections[1]!.target);
await command('front');await settleCamera();assert.equal(await selected(),'deltoid.left.anterior');
// Front clears OrbitControls' residual damping. Check reset invariance from
// this stable, zoomed/panned view, rather than during a software-rendered turn.
const resetCamera=(await snapshot()).camera,resetTarget=(await snapshot()).target;
await command('reset-selection');await page.waitForTimeout(200);assert.equal(await selected(),null);
sameCoordinates((await snapshot()).camera,resetCamera);sameCoordinates((await snapshot()).target,resetTarget);
// Change directly from left to right pectoral without an intervening reset.
await orient(0);for(const w of witnesses.slice(0,2)){const p=await screenPoint(w.point);await tap(p.x,p.y);assert.equal(await selected(),w.expectedId);}
const previous=await selected();
await gesture([{x:170,y:420,id:1}],[{x:210,y:420,id:1}]);assert.equal(await selected(),previous);
await gesture([{x:150,y:430,id:1},{x:280,y:430,id:2}],[{x:130,y:430,id:1},{x:300,y:430,id:2}]);assert.equal(await selected(),previous);
// A long hold does not select, even over a different valid muscle.
const left=await screenPoint(witnesses[0].point);await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...left,id:1}]});await page.waitForTimeout(450);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});assert.equal(await selected(),previous);
await command('overview');await page.waitForTimeout(750);
assert.equal(await selected(),previous);
// Head is a real neutral surface, not merely an empty background.
const head=await screenPoint({x:0,y:.85,z:.04});await tap(head.x,head.y);assert.equal(await selected(),null);
await tap(4,4);assert.equal(await selected(),null);
const events=await page.evaluate(()=>(window as unknown as {events:Array<{type:string;muscleId?:string|null}>}).events);
for(const muscle of MUSCLES)assert.ok(events.some(e=>e.type==='selection'&&e.muscleId===muscle.id));
const idle=await snapshot();await page.waitForTimeout(400);assert.equal((await snapshot()).renderCount,idle.renderCount);
await command('dispose');const disposed=await snapshot();assert.equal(disposed.atlasBytes,0);assert.equal(disposed.geometries,0);assert.equal(disposed.selectedMuscle,null);assert.equal(await page.locator('canvas').count(),0);
assert.deepEqual(errors,[]);assert.ok(requests.every(u=>u.startsWith(origin)));
await writeFile(`${out}/browser-verification.json`,JSON.stringify({status:'passed',environment:'Chromium SwiftShader, actual CDP touch events, 430×760 CSS px; not an iPhone',eightMuscles:checks,faceSelections,frontComparisonCameraIdentical:true,neutralSurfaceAndBackground:true,directChange:true,resetRemovesVisibleHighlight:true,resetPreservesCamera:true,frontAndOverviewPreserveSelection:true,rotationAndPinchPreserveSelection:true,longHoldRejected:true,localOnly:true,cleanup:true,initial,disposed,errors},null,2)+'\n');
console.log('Eight WebGL selections, actual touch gestures, neutral surfaces, reset, cleanup: passed. iPhone pending.');
}finally{await browser.close();server.close();}

}
void main().catch(error=>{console.error(error);process.exitCode=1;});
