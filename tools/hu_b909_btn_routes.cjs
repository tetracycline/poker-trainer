// B909: exact rendered routes for the next frozen BTN_BB ranks, not a solve.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('ipfr');const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sec=new Map(heads.map((h,i)=>[h[1],app.innerHTML.slice(h.index,heads[i+1]?.index??app.innerHTML.length)]));
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')).records;
const priority=JSON.parse(fs.readFileSync('data/nl2_hu_b838_234_approx_frequency_priority.json')).rows;
const cell=(id,tx)=>[...sec.get(id).match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'))[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
const first=v=>{const a=v.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return a?[a[1],a[2].replace(/≈$/,'')]:[];};
const result={};
for(const rank of [106,107]){
 const p=priority.find(x=>x.rank===rank),id=p.model_id,n=nodes.get(id),r=reg[id];
 assert.equal(r.label,'APPROX');assert.equal(r.frequency_rank,rank);assert.equal(r.solver_profile,'BTN_BB');assert(p.passes_min_0_2_pct_frequency);
 const parent=n.source,pm=nodes.get(parent),facing=pm.source;
 assert.equal(n.key,'對手下注、你跟|對手過、你下注、對手跟|對手過');
 assert.equal(pm.key,'對手下注、你跟|對手過');assert.equal(pm.facts.root.spot,'BTN_BB');
 const routes={flop:{},turn:{},river:{}};
 for(const tx of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const f=cell(facing,tx),t=cell(parent,tx),v=cell(id,tx);
  for(let i=0;i<5;i++){
   const k=tx+':'+i,fe=first(f[i]),te=first(t[i]);
   if(fe[0]===parent+'-'+tx&&fe[1]==='跟')routes.flop[k]='跟';
   if(te[0]===id+'-'+tx)routes.turn[k]=te[1];
   if(n.allowed.includes(k))routes.river[k]=v[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();
  }
 }
 assert(Object.keys(routes.turn).length>0);assert.deepEqual(Object.keys(routes.river).sort(),Object.keys(routes.turn).sort());
 const sizes=[...new Set(Object.values(routes.turn))];assert.equal(sizes.length,1);
 const pct={'下注 ⅓':33,'下注 ½':50,'下注 ¾':75,'下注 1':100,'下注 滿池':100,'下注 1池':100,'超池下注':150,'下注 1½':150}[sizes[0]]??n.turnCallPct??null;
 result[rank]={id,parent,facing,pct,label:sizes[0],facts:n.facts,parent_facts:pm.facts,flopCallPct:pm.flopCallPct??null,turnCallPct:n.turnCallPct??null,routes};
}
console.log(JSON.stringify(result));
