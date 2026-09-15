/* Bounded, two-thread export. Streams frames; never stores a frame directory. */
'use strict';
const fs=require('fs'),path=require('path'),{once}=require('events');
const sharp=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
sharp.concurrency(2);sharp.cache(false);
const R=require('./demo-renderer.js').ReconDemo;
const OUT='/workspace/scratch/42ed9c9c2a4a/recon-demo',D=JSON.parse(fs.readFileSync(path.join(OUT,'demo-data.json')));
const watchdog=setTimeout(()=>{console.error('Render time cap reached');process.exit(2);},240000);
async function raster(svg,width=1600){return sharp(Buffer.from(svg)).resize(width,Math.round(width*9/16)).removeAlpha();}
async function main(){
 if(process.argv.includes('--svg-stream')){
  const kind=process.argv[2],frames=(kind==='growth'?36:42)*24;
  for(let i=0;i<frames;i++){
   const t=Math.max(0,Math.min(1,(i/24-1.5)/(frames/24-3)));
   const svg=kind==='growth'?R.growth(D,t):R.trace(D,t);
   if(!process.stdout.write(JSON.stringify(svg)+'\n'))await once(process.stdout,'drain');
  }
  return;
 }
 if(process.argv.includes('--stills')){
  for(const [name,svg]of [['Growth-preview.png',R.growth(D,.43)],['Execution-preview.png',R.trace(D,17.8/28)],['Checkmate-preview.png',R.trace(D,1)]])await (await raster(svg)).png().toFile(path.join(OUT,name));
  // Check every exported frame for invalid positions and every inline script for JS syntax.
  for(let i=0;i<=280;i++){for(const svg of [R.trace(D,i/280),R.growth(D,i/280)])if(/NaN|undefined/.test(svg))throw Error('Invalid render geometry');}
  const html=fs.readFileSync(path.join(OUT,'Hector-Network-Demo.html'),'utf8');
  for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new Function(match[1]);
  console.log('Stills and render/syntax checks complete');return;
 }
 throw Error('Use --stills or growth/trace --svg-stream. Video export uses render_video.py.');
}
main().then(()=>clearTimeout(watchdog)).catch(e=>{console.error(e);clearTimeout(watchdog);process.exitCode=1;});
