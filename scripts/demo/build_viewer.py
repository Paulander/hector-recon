"""Package the recorded SVG demo into a portable single HTML file."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
OUT=Path('/workspace/scratch/42ed9c9c2a4a/recon-demo')
data=(OUT/'demo-data.json').read_text()
renderer=(HERE/'demo-renderer.js').read_text()
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hector · recorded growth and execution</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#05070a;color:#edf3fa;font:14px system-ui,sans-serif}button,select{font:inherit;background:#151c25;color:#edf3fa;border:1px solid #3a4655;border-radius:7px;padding:9px 14px;cursor:pointer}button.on{background:#e4edf6;color:#10151c}button:hover{border-color:#90cafa}header{display:flex;gap:9px;align-items:center;padding:14px 22px;border-bottom:1px solid #26303b;flex-wrap:wrap}header strong{margin-right:auto;letter-spacing:2px;font-size:12px;color:#a7b4c5}#stage{width:100%;max-width:1920px;margin:auto;position:relative}#stage svg{display:block;width:100%;height:auto}#controls{display:flex;align-items:center;gap:13px;padding:12px 24px;max-width:1500px;margin:auto}input[type=range]{flex:1;min-width:80px;accent-color:#d2e9ff}#stamp{font-variant-numeric:tabular-nums;min-width:130px;color:#b4c2d1}#inspector{max-width:1452px;margin:8px auto;padding:14px 20px;border:1px solid #283441;border-radius:9px;min-height:65px;color:#bdc9d7;line-height:1.6}details{max-width:1452px;margin:18px auto 40px;padding:18px 20px;border-top:1px solid #283441;line-height:1.7;color:#b3bfcd}summary{cursor:pointer;color:#edf3fa}code{color:#a8d3fc}#stage [data-node]{cursor:crosshair}label{white-space:nowrap;color:#b5c2d1}body.theater header,body.theater #controls,body.theater #inspector,body.theater details{display:none}body.theater #stage{height:100vh;max-width:none;display:flex;align-items:center}body.theater #stage svg{max-height:100vh}.key{color:#8190a2;font-size:12px}a{color:#9bd2ff}@media(max-width:700px){header{padding:10px}header strong{width:100%}#controls{flex-wrap:wrap}#inspector,details{margin:10px}}
</style>
<header><strong>HECTOR / RECORDED NETWORK</strong><button id="growth" class="on">Growth</button><button id="trace">One chess move</button><label><input id="clean" type="checkbox"> Minimal growth view</label><button id="fullscreen">Present fullscreen</button></header>
<main><div id="stage"></div><div id="controls"><button id="play">Play</button><button id="back" aria-label="Previous tick or earlier growth">←</button><button id="next" aria-label="Next tick or later growth">→</button><input id="scrub" aria-label="Playback position" type="range" min="0" max="10000" value="0"><span id="stamp"></span><select id="speed" aria-label="Playback speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></div>
<div id="inspector" aria-live="polite">Hover or click a node to inspect its definition. Space plays or pauses; arrows step; F enters presentation mode; Escape restores controls.</div>
<details><summary>Presenter notes and what this demonstrates</summary>
<p><b>Growth:</b> one recorded seed, 1,280–4,096 training decisions. Diamonds are shared condition definitions, outer dots are equality readers, and the center represents their shared action-support calculation. The runtime instantiates a separate bound copy for each action. This view folds those repeated copies together; it is not the complete physical graph.</p>
<p>Green marks a birth; red marks retirement. Lifetimes come from saved birth records and retirement exposure counts, checked against all 27 checkpoints. Stable display positions and fades are presentation choices. Scores are the last scheduled development measurement, held until the next measurement. A removed condition loses its decision influence; its history remains stored.</p>
<p><b>Execution:</b> the final saved actor, without learning or exploration, chooses <b>Rh2#</b> on development row 2. Both the ordinary execution and the traced execution choose the same move and preserve learned state. All legal action options are shown; only the b2→h2 option's descendants are expanded. This branch is selected for inspection retrospectively, not supplied to the actor as an answer.</p>
<p>A formal tick has two phases: emit messages from the current states, then compute the next states. Playback slows these phases and animates message travel. It does not invent additional runtime microticks. The rook moves at the recorded output-terminal call, during tick 25's update, before its later CONFIRMED state.</p>
<p><b>State ≠ activation ≠ reward.</b> Blue means requested; amber means active/waiting; green means true/confirmed; red means a false predicate or failed node. An equality reader can confirm a test for a <i>false</i> Boolean value. A confirmed action-choice node means an action was selected, not that the goal was achieved. Inspect nodes for their numeric activation. Boolean condition activations may stay at 1 while FAILED; their state gates contribution.</p>
<p><b>Current limits:</b> the chess actor uses supplied random proposal, pruning and credit rules; the graph has not learned its own developmental policy. The runtime requests catalog, choice and execution roots in sequence; there is no learned dispatch edge between those roots. This is mate-in-one development evidence, not a general chess agent. The newer recursive Boolean prototype is a separate experiment and is not depicted here.</p>
<p><b>Suggested narration:</b> “These are structures from actual rewarded experience. Conditions appear and retire while shared weights learn. On the right, we can watch a request descend to measurements and evidence return to the action chooser. The chosen move is then executed through an output terminal. Bringing developmental control inside this same architecture is the next research step.”</p>
<p>This file works offline without external scripts, fonts, accounts or network access. Space: play/pause. Left/right: step one formal tick (growth: 32 decisions). F: fullscreen. Escape: exit presentation mode. Click a node to retain inspection; click blank space to release it.</p>
</details></main><script>const DATA=__DATA__;</script><script>__RENDERER__</script><script>
let mode='growth',t=0,playing=false,prev=0,pinned=null,theater=false;
const $=id=>document.getElementById(id),R=window.ReconDemo;
function inspect(id){
 let s='';const e=R.esc;
 if(mode==='growth'){
  if(id.startsWith('condition:')){const d=DATA.definitions.find(d=>d.id===Number(id.split(':')[1]));s=`<b>Condition ${d.id} · ${d.op.toUpperCase()}</b><br>${d.atoms.map(([i,v])=>e(DATA.coordinates[i].name)+' = '+v).join(' · ')}<br>Born after decision ${d.born}; ${d.death>DATA.end?'still present at the endpoint':'retired after decision '+d.death}.`;}
  else if(id.startsWith('reader:')){const [,i,v]=id.split(':');s=`<b>Equality reader</b><br>${e(DATA.coordinates[i].name)} = ${v}. Shared definition; runtime readings are separately bound to each move.`;}
  else s='<b>Shared action support</b><br>Bias plus the weighted contributions of confirmed conditions. The full graph evaluates a bound copy for each legal action.';
 }else{
  const n=DATA.trace.nodes.find(n=>n.id===id);if(!n)return;
  const k=Math.min(27,Math.floor(t*28)),f=DATA.trace.frames[k],q=t>=1?1:(t*28)%1,state=(q<.62?f.states_before:f.states_after)[id];
  const activation=q<.62?(k?DATA.trace.frames[k-1].activations[id]:null):f.activations[id];
  s=`<b>${e(id)}</b> · ${e(n.type)} · ${e(state)}<br>Activation: ${activation===null||activation===undefined?'not sampled at this phase':Number(activation).toFixed(4)}`;
  if(n.meta.atom){const [i,v]=n.meta.atom;s+=` · Test: ${e(DATA.coordinates[i].name)} = ${e(v)}`;if(['TRUE','CONFIRMED','FAILED'].includes(state))s+=` · Measured: ${e(n.meta.reading)}`;}
  if(n.meta.condition_id!==undefined){const c=DATA.trace.conditions.find(c=>c.id===n.meta.condition_id);s+=` · ${e(c.op.toUpperCase())} · Learned SUR weight: ${c.weight.toFixed(5)}`;}
  if(n.binding)s+=` · Move binding: ${e(n.binding)}`;
 }
 $('inspector').innerHTML=s;
}
function draw(){
 $('stage').innerHTML=mode==='growth'?R.growth(DATA,t,$('clean').checked):R.trace(DATA,t);
 $('scrub').value=Math.round(t*10000);$('play').textContent=playing?'Pause':'Play';
 $('stamp').textContent=mode==='growth'?`${Math.floor(DATA.start+t*(DATA.end-DATA.start))} decisions`:`Tick ${Math.min(28,Math.floor(t*28)+1)} / 28`;
 if(pinned)inspect(pinned);
}
function switchMode(m){mode=m;t=0;playing=false;pinned=null;['growth','trace'].forEach(id=>$(id).classList.toggle('on',id===mode));$('inspector').textContent='Hover or click a node to inspect its state, activation or definition.';draw();}
function toggle(){if(t>=1)t=0;playing=!playing;draw();}
function step(d){playing=false;t=Math.max(0,Math.min(1,t+d*(mode==='trace'?1/28:32/(DATA.end-DATA.start))));draw();}
function presentation(){theater=!theater;document.body.classList.toggle('theater',theater);if(theater&&document.documentElement.requestFullscreen)document.documentElement.requestFullscreen().catch(()=>{});else if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});}
$('growth').onclick=()=>switchMode('growth');$('trace').onclick=()=>switchMode('trace');$('play').onclick=toggle;$('back').onclick=()=>step(-1);$('next').onclick=()=>step(1);$('clean').onchange=draw;$('fullscreen').onclick=presentation;
$('scrub').oninput=()=>{playing=false;t=Number($('scrub').value)/10000;draw();};
$('stage').addEventListener('pointerover',ev=>{const n=ev.target.closest('[data-node]');if(n&&!pinned)inspect(n.dataset.node);});
$('stage').addEventListener('click',ev=>{const n=ev.target.closest('[data-node]');pinned=n?n.dataset.node:null;if(pinned)inspect(pinned);});
document.addEventListener('keydown',ev=>{if(ev.target.tagName==='SELECT'||ev.target.tagName==='INPUT')return;if(ev.code==='Space'){ev.preventDefault();toggle();}if(ev.key==='ArrowRight'){ev.preventDefault();step(1);}if(ev.key==='ArrowLeft'){ev.preventDefault();step(-1);}if(ev.key.toLowerCase()==='f')presentation();if(ev.key==='Escape'){theater=false;document.body.classList.remove('theater');}});
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement){theater=false;document.body.classList.remove('theater');}});
function loop(now){if(playing&&prev){t=Math.min(1,t+(now-prev)/1000*Number($('speed').value)/(mode==='growth'?36:42));if(t===1)playing=false;draw();}prev=now;requestAnimationFrame(loop);}draw();requestAnimationFrame(loop);
</script></html>'''
(OUT/'Hector-Network-Demo.html').write_text(html.replace('__DATA__',data).replace('__RENDERER__',renderer))
print('Built self-contained viewer')
