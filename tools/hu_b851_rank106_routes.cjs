// B851: actual rendered rank106 route, no size inferred from a similar model.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('ipfr');
const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sec=new Map(heads.map((x,i)=>[x[1],app.innerHTML.slice(x.index,heads[i+1]?.index??app.innerHTML.length)]));
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n])),id='ln-ipfr-r_model-5ce65m',n=nodes.get(id),parent=n.source;
assert.equal(n.pre,'翻前： 你 BTN 開 ，BB 跟');
assert.equal(n.key,'對手下注、你跟|對手過、你下注、對手跟|對手過');
assert.equal(n.facts.root.spot,'BTN_BB');assert.equal(n.facts.root.pot,5.5);
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')),record=reg.records[id];
assert.deepEqual([record.frequency_rank,record.label,record.solver_profile,record.street],[106,'APPROX','BTN_BB',2]);
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id,tx){const row=sec.get(id)?.match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'));return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];}
const first=v=>{const a=v.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return a?[a[1],a[2].replace(/≈$/,'')]:[];};
const routes={flop:{},turn:{},river:{}};let sources=new Set();
for(const tx of textures){
 for(const [sid,html] of sec){if(!sid.startsWith('ln-ipfr-f_')||!html.includes('BTN 開')||!html.includes('BB 跟'))continue;
  cells(sid,tx).slice(0,5).forEach((v,i)=>{const f=first(v);if(f[0]===parent+'-'+tx&&f[1]==='跟'){routes.flop[tx+':'+i]='跟';sources.add(sid);}});
 }
 const t=cells(parent,tx),v=cells(id,tx);
 for(let i=0;i<5;i++){if(!t[i]||!v[i])continue;const te=first(t[i]),k=tx+':'+i;
  if(te[0]===id+'-'+tx){assert.equal(te[1],'下注 ¾');routes.turn[k]=te[1];}
  if(n.allowed.includes(k)){const a=v[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();assert(['過','下注 ½','下注 ¾'].includes(a));routes.river[k]=a;}
 }
}
assert.equal(sources.size,1);assert(Object.keys(routes.flop).length);assert(Object.keys(routes.turn).length);
assert.deepEqual(Object.keys(routes.turn).sort(),Object.keys(routes.river).sort());
assert(Math.abs((8882/2286)/record.assumed_model_node_spr-1)<=.05);
console.log(JSON.stringify({id,parent,facing:[...sources][0],spot:'BTN_BB',actor:1,line:'b33 c/x b75 c/x',spr:record.assumed_model_node_spr,pot:2286,stack:8882,routes}));
