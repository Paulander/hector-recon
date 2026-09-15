/* One SVG renderer for the offline viewer, video and stills. No remote assets. */
(function(root){
'use strict';
const C={bg:'#05070a',white:'#edf3fa',muted:'#86919f',line:'#34404e',green:'#77e5ac',red:'#f18e95',blue:'#80c5ff',amber:'#e5c183'};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clamp=x=>Math.max(0,Math.min(1,x));
const mix=(a,b,t)=>a+(b-a)*t;
const text=(x,y,s,size=16,color=C.white,extra='')=>`<text x="${x}" y="${y}" fill="${color}" font-size="${size}" ${extra}>${esc(s)}</text>`;
const line=(a,b,color=C.line,opacity=1,width=1,extra='')=>`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="${color}" opacity="${opacity}" stroke-width="${width}" ${extra}/>`;
const circle=(p,r,color,opacity=1,extra='')=>`<circle cx="${p[0]}" cy="${p[1]}" r="${r}" fill="${color}" opacity="${opacity}" ${extra}/>`;
function node(p,r,color,shape='circle',id='',opacity=1){
 const tip=id?`data-node="${esc(id)}"`:'';
 return `<g ${tip} opacity="${opacity}">${circle(p,r+8,color,.06)}${shape==='diamond'?`<path d="M ${p[0]} ${p[1]-r} l ${r} ${r} l ${-r} ${r} l ${-r} ${-r} Z" fill="${color}"/>`:shape==='square'?`<rect x="${p[0]-r}" y="${p[1]-r}" width="${2*r}" height="${2*r}" rx="2" fill="${color}"/>`:circle(p,r,color)}${id?circle(p,Math.max(r,10),'transparent',1):''}</g>`;
}
function base(title,subtitle){return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900" role="img" aria-label="${esc(title)}"><rect width="1600" height="900" fill="${C.bg}"/><g font-family="DejaVu Sans, sans-serif">${text(54,42,'H E C T O R   /   R e C o N',13,C.muted)}${text(54,90,title,33)}${text(54,120,subtitle,15,C.muted)}`;}
const finish=s=>s+'</g></svg>';
function growth(D,t,clean=false){
 const event=D.start+(D.end-D.start)*clamp(t), fade=48, center=[800,465];
 const alive=D.definitions.filter(d=>d.born<=event&&event<d.death);
 const visible=D.definitions.filter(d=>d.born<=event&&event<d.death+fade);
 const readerMap=new Map();
 const allAtoms=[];D.coordinates.forEach((c,i)=>c.values.forEach(v=>allAtoms.push([i,Number(v)])));
 allAtoms.forEach(([i,v],j)=>{const a=2*Math.PI*j/allAtoms.length-Math.PI/2;readerMap.set(`${i}:${v}`,[800+530*Math.cos(a),465+285*Math.sin(a)]);});
 const pos=d=>{const a=2*Math.PI*d.seat/64-Math.PI/2;const drift=event>=d.death?18*clamp((event-d.death)/fade):0;return[800+(292+drift)*Math.cos(a),465+(168+drift)*Math.sin(a)];};
 const appearance=d=>event>=d.death?[C.red,1-clamp((event-d.death)/fade)]:[event-d.born<fade&&d.born>D.start?C.green:C.white,clamp((event-d.born)/7)];
 let s=base(clean?'':'A structure that changes with experience',clean?'':'Recorded chess training · seed 7 · shared condition definitions across move bindings');
 let readers=new Map();
 for(const d of visible){const [col,alpha]=appearance(d),p=pos(d);s+=line(center,p,col,alpha*.20,.8);
  for(const [i,v]of d.atoms){const k=`${i}:${v}`,q=readerMap.get(k);s+=line(p,q,col,alpha*.23,.8);readers.set(k,Math.max(readers.get(k)||0,alpha));}}
 for(const [k,a]of readers){s+=node(readerMap.get(k),3.6,C.white,'circle',`reader:${k}`,a*.9);}
 for(const d of visible){const [col,a]=appearance(d);s+=node(pos(d),5.3,col,'diamond',`condition:${d.id}`,a);}
 s+=node(center,13,C.white,'circle','support');
 if(!clean){s+=text(800,498,'ACTION SUPPORT',10,C.muted,'text-anchor="middle"');
 s+=text(54,186,'TRAINING DECISIONS',11,C.muted)+text(54,224,Math.floor(event).toLocaleString('en-US'),32);
 s+=text(54,262,`${alive.length} live conditions`,15)+text(54,290,`${D.definitions.filter(d=>d.born>D.start&&d.born<=event).length} births since start`,14,C.green)+text(54,317,`${D.definitions.filter(d=>d.death<=event).length} retirements since start`,14,C.red);
 const m=D.milestones.filter(m=>m.event<=event).at(-1);
 s+=text(1340,186,'LAST MEASUREMENT',11,C.muted)+text(1340,224,`${m.mates} / 128`,28)+text(1340,252,`at ${m.event.toLocaleString('en-US')} decisions`,13,C.muted);
 s+=text(54,783,'●  READER',12,C.muted)+text(212,783,'◆  CONDITION',12,C.muted)+text(411,783,'●  SHARED SUPPORT',12,C.muted);
 s+=text(1150,783,'BORN',12,C.green)+text(1260,783,'RETIRED',12,C.red);
 s+=line([54,823],[1546,823],C.line,1,2)+line([54,823],[54+1492*clamp(t),823],C.white,1,2);
 for(const m of D.milestones){const x=54+1492*(m.event-D.start)/(D.end-D.start);s+=circle([x,823],4,m.event<=event?C.white:C.line)+text(x,848,String(m.event),11,C.muted,'text-anchor="middle"');}
 s+=text(54,882,'Actual lifetimes verified at 27 checkpoints. Animation timing is compressed. Proposal and pruning rules are supplied by the runtime.',12,C.muted);}
 return finish(s);
}
function tracePositions(D){
 const P={},T=D.trace,nodes=T.nodes;
 P.action_choice=[1040,193];P.catalog_root=[545,317];P.catalog=[545,379];P.execute=[545,631];P.actuator=[545,706];
 const opts=nodes.filter(n=>n.id.startsWith('option:'));
 opts.forEach((n,i)=>P[n.id]=[697+i*(705/Math.max(1,opts.length-1)),251]);
 P[T.selected]=[1040,489];
 const gates=nodes.filter(n=>n.id.startsWith('gate:')).sort((a,b)=>a.meta.condition_id-b.meta.condition_id);
 gates.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/gates.length;P[n.id]=[1040+183*Math.cos(a),489+138*Math.sin(a)];});
 const readers=nodes.filter(n=>n.id.startsWith('read:')).sort((a,b)=>a.meta.atom[0]-b.meta.atom[0]||Number(a.meta.atom[1])-Number(b.meta.atom[1]));
 readers.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/readers.length;P[n.id]=[1040+365*Math.cos(a),489+215*Math.sin(a)];});
 P[`bias:${T.slot}`]=[1008,560];P[`explore:${T.slot}`]=[1072,560];return P;
}
const colors={INACTIVE:'#3c4653',REQUESTED:C.blue,ACTIVE:C.amber,WAITING:C.amber,TRUE:C.green,CONFIRMED:C.green,FAILED:C.red,SUPPRESSED:C.muted};
function phaseText(tick,emitting){
 const suffix=emitting?'Messages travel along existing edges.':'Recorded states after the update.';
 if(tick<=7)return ['1 / READ THE ACTION CATALOG','The input terminal supplies legal move bindings.',suffix];
 if(tick<=13)return ['2 / REQUEST EVIDENCE','Each legal move has a bound copy of the conditions.',suffix];
 if(tick<=18)return ['3 / EVALUATE CONDITIONS','Readers return values; AND / OR / XOR combine their truth.',suffix];
 if(tick<=21)return ['4 / SELECT AN ACTION','Weighted condition evidence determines the chosen binding.',suffix];
 if(tick<=24)return ['5 / REQUEST THE OUTPUT TERMINAL','The runtime requests execution after graph selection.',suffix];
 return ['6 / ACT ON THE ENVIRONMENT','The output terminal moves the rook. The environment detects mate.',suffix];
}
function board(D,moved){
 const T=D.trace,x=54,y=208,z=46;let s='';
 const from=T.action.slice(0,2),to=T.action.slice(2,4);
 for(let r=0;r<8;r++)for(let f=0;f<8;f++){const sq=String.fromCharCode(97+f)+(8-r),on=moved&&(sq===from||sq===to);s+=`<rect x="${x+f*z}" y="${y+r*z}" width="${z}" height="${z}" fill="${on?'#668676':(r+f)%2?'#536071':'#bac3ce'}"/>`;}
 for(const p of T.pieces){let sq=moved&&p.square===from?to:p.square;const f=sq.charCodeAt(0)-97,r=8-Number(sq[1]);
  const glyph={K:'♚',k:'♚',R:'♜'}[p.piece];s+=`<text x="${x+(f+.5)*z}" y="${y+r*z+36}" font-family="DejaVu Sans" text-anchor="middle" font-size="42" fill="${p.piece==='k'?'#11151d':'#ffffff'}" stroke="${p.piece==='k'?'#d8e0e9':'#151b22'}" stroke-width=".7" paint-order="stroke">${glyph}</text>`;}
 for(let i=0;i<8;i++){s+=text(x+(i+.5)*z,y+8*z+22,String.fromCharCode(97+i),12,C.muted,'text-anchor="middle"')+text(x-17,y+i*z+29,String(8-i),12,C.muted);}
 return s;
}
function trace(D,t,focus=false){
 const T=D.trace,idx=Math.min(T.frames.length-1,Math.floor(clamp(t)*(T.frames.length))),frac=t>=1?1:(clamp(t)*T.frames.length)%1;
 const frame=T.frames[idx],emitting=frac<.62,states=emitting?frame.states_before:frame.states_after,P=tracePositions(D);
 const moved=frame.tick>T.execution_tick||(frame.tick===T.execution_tick&&!emitting);
 let s=base('From a request to a move','Frozen learned chess actor · seed 7 at 4,096 decisions · real two-phase formal tick trace');
 s+=line([469,155],[469,802],C.line,.7)+board(D,moved);
 const phase=phaseText(frame.tick,emitting);
 s+=text(54,172,'CORNER / KING SEPARATION 2 FILES, 1 RANK',12,C.muted);
 s+=text(54,641,moved?'Rh2#  ·  CHECKMATE':'White to move',28,moved?C.green:C.white);
 s+=text(54,676,'Inspected binding: b2 → h2',15,C.muted)+text(54,707,'Board changes only when the output terminal acts.',12,C.muted);
 s+=text(54,749,`Formal tick ${frame.tick} / ${T.frames.length}`,20)+text(54,778,emitting?'Phase A · emit messages':'Phase B · update states',14,C.blue);
 const finalStates=T.frames.at(-1).states_after;
 const dim=n=>focus&&n.startsWith('gate:')&&finalStates[n]!=='CONFIRMED'?.18:1;
 for(const e of T.edges.filter(e=>e.type==='SUB'))s+=line(P[e.src],P[e.dst],C.line,.65*Math.min(dim(e.src),dim(e.dst)),.9);
 if(emitting){const progress=clamp(frac/.62);for(const m of frame.messages){
  if(m.message==='wait'||m.message.startsWith('inhibit'))continue;
  const a=P[m.src],b=P[m.dst],col=m.message==='request'?C.blue:m.message==='fail'?C.red:C.green;
  s+=line(a,b,col,.22*Math.min(dim(m.src),dim(m.dst)),1.2);
  s+=circle([mix(a[0],b[0],progress),mix(a[1],b[1],progress)],2.4,col,.9*Math.min(dim(m.src),dim(m.dst)));}}
 for(const n of T.nodes){const gate=n.id.startsWith('gate:'),option=n.id.startsWith('option:'),selected=n.id===T.selected;
  const r=selected?12:gate?5:option?4:n.id==='action_choice'?12:7;
  s+=node(P[n.id],r,colors[states[n.id]]||C.muted,gate?'diamond':n.type==='TERMINAL'?'square':'circle',n.id,dim(n.id));}
 s+=text(1040,166,'ACTION CHOICE',11,C.muted,'text-anchor="middle"')+text(1440,251,'options',10,C.muted);
 s+=text(1040,517,'b2 → h2',13,C.white,'text-anchor="middle"')+text(1040,539,'inspected option',10,C.muted,'text-anchor="middle"');
 s+=text(545,291,'CATALOG',11,C.muted,'text-anchor="middle"')+text(545,407,'input terminal',10,C.muted,'text-anchor="middle"');
 s+=text(545,604,'EXECUTE',11,C.muted,'text-anchor="middle"')+text(545,733,'output terminal',10,C.muted,'text-anchor="middle"');
 s+=text(508,468,'Runtime requests',11,C.muted)+text(508,485,'these roots in order.',11,C.muted)+text(508,513,'No learned',11,C.muted)+text(508,530,'dispatch edge.',11,C.muted);
 s+=text(713,745,phase[0],14,C.white)+text(713,773,phase[1],13,C.muted);
 s+=text(54,831,'REQUESTED',11,C.blue)+text(205,831,'ACTIVE / WAITING',11,C.amber)+text(401,831,'TRUE / CONFIRMED',11,C.green)+text(613,831,'FALSE / FAILED',11,C.red)+text(799,831,'INACTIVE',11,colors.INACTIVE);
 s+=text(54,867,'All action options shown; detailed descendants shown only for b2 → h2. State color is separate from activation and reward.',12,C.muted);
 s+=text(54,888,'Each tick emits messages, then updates states. Moving dots slow down recorded messages; they are not additional runtime microticks.',11,C.muted);
 return finish(s);
}
root.ReconDemo={growth,trace,tracePositions,esc,phaseText};
})(typeof module!=='undefined'?module.exports:window);
