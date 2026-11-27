// B910: the real t_stab parent is not a synthetic model. Reuse B851's rendered-link method.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('ipfr');
const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sec=new Map(heads.map((x,i)=>[x[1],app.innerHTML.slice(x.index,heads[i+1]?.index??app.innerHTML.length)]));
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')).records;
const priority=JSON.parse(fs.readFileSync('data/nl2_hu_b838_234_approx_frequency_priority.json')).rows;
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id,tx){const row=sec.get(id)?.match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'));return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];}
const first=v=>{const a=v.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return a?[a[1],a[2].replace(/≈$/,'')]:[];};
const configs={106:['ln-ipfr-r_model-5ce65m',75,'下注 ¾',2286,8882],107:['ln-ipfr-r_model-ujl14x',50,'下注 ½',1828,9111]};
const out={};
for(const [rank,[id,pct,label,pot,stack]] of Object.entries(configs)){
 const n=nodes.get(id),r=reg[id],parent=n.source,p=priority.find(x=>x.rank===+rank);
 assert.equal(parent,'ln-ipfr-t_stab-9egy37');assert.equal(r.source_model_id,parent);
 assert.equal(n.pre,'翻前： 你 BTN 開 ，BB 跟');assert.equal(n.key,'對手下注、你跟|對手過、你下注、對手跟|對手過');
 assert.deepEqual([n.facts.root.spot,n.facts.root.pot,n.facts.root.stack],['BTN_BB',5.5,97.5]);
 assert.deepEqual([r.frequency_rank,r.label,r.solver_profile,r.street],[+rank,'APPROX','BTN_BB',2]);assert(p.passes_min_0_2_pct_frequency);
 assert.equal(n.facts.spr,r.assumed_model_node_spr);assert(Math.abs((stack/pot)/n.facts.spr-1)<=.05);
 const routes={flop:{},turn:{},river:{}},sources=new Set();
 for(const tx of textures){
  for(const [sid,html] of sec){if(!sid.startsWith('ln-ipfr-f_')||!html.includes('BTN 開')||!html.includes('BB 跟'))continue;
   cells(sid,tx).slice(0,5).forEach((v,i)=>{const f=first(v);if(f[0]===parent+'-'+tx&&f[1]==='跟'){routes.flop[tx+':'+i]='跟';sources.add(sid);}});
  }
  const t=cells(parent,tx),v=cells(id,tx);
  for(let i=0;i<5;i++){if(!t[i]||!v[i])continue;const te=first(t[i]),k=tx+':'+i;
   if(te[0]===id+'-'+tx){assert.equal(te[1],label);routes.turn[k]=te[1];}
   if(n.allowed.includes(k)){const a=v[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();assert(['過','下注 ½','下注 ¾'].includes(a));routes.river[k]=a;}
  }
 }
 assert.equal(sources.size,1);assert(Object.keys(routes.flop).length&&Object.keys(routes.turn).length);
 assert.deepEqual(Object.keys(routes.turn).sort(),Object.keys(routes.river).sort());
 const facing=[...sources][0];out[rank]={id,parent,facing,spot:'BTN_BB',actor:1,line:'b33 c/x b'+pct+' c/x',flop_pct:33,turn_pct:pct,spr:n.facts.spr,pot,stack,routes,source_header:sec.get(facing).split('<table')[0].replace(/<[^>]*>/g,'')};
}
const prior=JSON.parse(require('node:child_process').execFileSync('node',['tools/hu_b851_rank106_routes.cjs'],{encoding:'utf8'}));
for(const k of ['id','parent','facing','spot','actor','line','spr','pot','stack','routes'])assert.deepEqual(out[106][k],prior[k]);
assert.equal(out[106].facing,out[107].facing);
console.log(JSON.stringify(out));
