#!/usr/bin/env node
/* Independently audit all visible class-specific HU next-street paths, not
 * merely the first navigable cell from any texture row. Real vs assumed CFR
 * status remains distinct; an ALL-IN is a terminal, not a missing river.
 */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
 vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),ctx,{filename:file});
const BTS=['low','mid_high','KQ_high','A_high','paired','mono'];
const BTM={'9 以下低牌面':'low','J/T 高面':'mid_high','K/Q 高面':'KQ_high','A 高面':'A_high','成對面':'paired','單色面':'mono'};
function strip(s){return String(s||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim()}
function stage(nd){const n=nd.replace(/^(3b_|3c_|lmp_|iso_)/,'');return n.startsWith('r_')?2:n.startsWith('t_')?1:0;}
function isTerminal(c){const text=c.primary||'';return /^棄|^加注\s*全下|^全下/.test(text)}
function getPrimary(c){const m=c.html.match(/<a class="jmp" href="#([^"]+)">([\s\S]*?)<\/a>/);const p=m&&m[2];const txt=strip(p||c.html.split(/<a class="jmp sub"|<small\b/)[0]);return {href:m&&m[1],primary:txt}}
function sections(html){
 const tags=[...html.matchAll(/<div class="sec" data-node="([^"]+)" id="([^"]+)">/g)];
 return tags.map((m,i)=>{
   const part=html.slice(m.index,i+1<tags.length?tags[i+1].index:html.length),[sp,nd]=m[1].split('/');
   const id=m[2],title=strip((part.match(/<b class="ttl">([\s\S]*?)<\/b>/)||[])[1]);
   const rows=[];
   for(const tr of part.matchAll(/<tr\b([^>]*)>([\s\S]*?)<\/tr>/g)){
     const ts=(tr[1].match(/\bid="([^"]+)"/)||[])[1]||'';
     let bt=BTS.find(b=>ts.endsWith('-'+b));
     if(!bt){const first=strip((tr[2].match(/<th[^>]*>([\s\S]*?)<\/th>/)||[])[1]);bt=Object.entries(BTM).find(([z])=>first===z||first.endsWith('・'+z))?.[1];}
     if(!bt)continue;
     const cells=[...tr[2].matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)].map(mm=>{
       const c={cls:mm[1],html:mm[2],na:/\bna\b/.test(mm[1])||strip(mm[2])==='—'};
       return {...c,...getPrimary(c)};
     });
     rows.push({bt,id:ts,cells});
   }
   return {sp,nd,id,title,st:stage(nd),part,rows,model:nd.includes('_model')};
 });
}
const errs=[],stats={tables:0,modelTables:0,authenticTables:0,primaryCells:0,reachable:0,terminal:0,modelLinks:0,sameClassRiver:0,extras:0};
for(const spot of ctx.NLL.spots){
 ctx.__linesQA.render(spot.id);
 const secs=sections(app.innerHTML),ids=new Map();
 for(const s of secs){
   stats.tables++;stats[s.model?'modelTables':'authenticTables']++;
   if(ids.has(s.id))errs.push({kind:'DUP_ID',id:s.id});
   ids.set(s.id,s);for(const r of s.rows){if(r.id)ids.set(r.id,{...s,targetRow:r});}
 }
 function targetFor(href){return ids.get(href)||ids.get(String(href).replace(/-(?:low|mid_high|KQ_high|A_high|paired|mono)$/,''));}
 function locate(href,bt){const target=targetFor(href),s=target&&secs.find(x=>x.id===target.id);if(!s)return null;
   return {s,row:s.rows.find(x=>x.bt===((href.match(/-(low|mid_high|KQ_high|A_high|paired|mono)$/)||[])[1]||bt))};}
 for(const s of secs){
   if(s.model){
     if(s.rows.length!==6)errs.push({kind:'MODEL_ROW_COUNT',table:s.id,rows:s.rows.length});
     if(!s.part.includes('MODEL／待真實 CFR')||!s.part.includes('根 SPR')||!s.part.includes('SPR 約')||!s.part.includes('100bb'))
       errs.push({kind:'MODEL_ASSUMPTION_DISCLOSURE_MISSING',table:s.id});
     for(const row of s.rows){
       if(row.cells.length!==5)errs.push({kind:'MODEL_COL_COUNT',table:s.id,board:row.bt,cols:row.cells.length});
       for(const c of row.cells)if(!c.na && !c.html.includes('ASSUMED（非 GTO，非 CERT）'))
         errs.push({kind:'MODEL_ACTION_NOT_CLEARY_MARKED_UNCERTIFIED',table:s.id,board:row.bt});
     }
   }
   for(const row of s.rows)for(let ci=0;ci<row.cells.length;ci++){
     const c=row.cells[ci];if(c.na)continue;
     for(const ext of c.html.matchAll(/<a class="jmp sub" href="#([^"]+)"/g)){
       stats.extras++;if(!targetFor(ext[1]))errs.push({kind:'BROKEN_SUB',src:s.id,href:ext[1]});
     }
     if(s.st>=2||isTerminal(c)){if(isTerminal(c))stats.terminal++;continue;}
     stats.primaryCells++;
     if(!c.href){errs.push({kind:'NO_PRIMARY',src:s.id,bt:row.bt,ci,txt:c.primary});continue;}
     const dest=locate(c.href,row.bt);
     if(!dest){errs.push({kind:'BROKEN',src:s.id,href:c.href});continue;}
     if(dest.s.sp!==s.sp||dest.s.st!==s.st+1){errs.push({kind:'STAGE_OR_SPOT',src:s.id,href:c.href});continue;}
     if(s.title.split(' → ')[0]!==dest.s.title.split(' → ')[0])errs.push({kind:'PRE',src:s.id,href:c.href});
     if(!dest.row||dest.row.cells.length<=ci||dest.row.cells[ci].na){errs.push({kind:'UNREACHABLE_CLASS',src:s.id,href:c.href,bt:row.bt,ci});continue;}
     stats.reachable++;if(dest.s.model)stats.modelLinks++;
     if(s.st===0){
       const nxt=dest.row.cells[ci];
       if(isTerminal(nxt)){
         errs.push({kind:'TURN_ALLIN_NO_RIVER',src:s.id,href:c.href,bt:row.bt,ci});
       } else if(!nxt.href){errs.push({kind:'NO_RIVER_FROM_TURN_CLASS',src:s.id,href:c.href,bt:row.bt,ci});}
       else {const rv=locate(nxt.href,row.bt);if(!rv||rv.s.st!==2||!rv.row||rv.row.cells[ci]?.na){errs.push({kind:'NO_VALID_RIVER_CLASS',src:s.id,href:nxt.href,bt:row.bt,ci});}else stats.sameClassRiver++;}
     }
   }
 }
}
const results={stats,violations:errs,coverage:stats.primaryCells?+(100*stats.reachable/stats.primaryCells).toFixed(3):0};
const out=process.argv[2];if(out)fs.writeFileSync(out,JSON.stringify(results,null,2));
console.log(JSON.stringify({stats,coverage:results.coverage,violations:errs.length,examples:errs.slice(0,15)}));
process.exitCode=errs.length?1:0;