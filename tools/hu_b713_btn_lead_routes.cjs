// Actual player links after the BB acts first: BTN call, BTN barrel, BTN river decision.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('ipfr');const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sec=new Map(heads.map((h,i)=>[h[1],app.innerHTML.slice(h.index,heads[i+1]?.index??app.innerHTML.length)]));
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const facing='ln-ipfr-f_vs_donk-14oe091',parent='ln-ipfr-t_model-qcljc6';const configs={
 104:['ln-ipfr-r_model-1k916pi',75,'下注 ¾',3.045],105:['ln-ipfr-r_model-1v72njh',50,'下注 ½',3.932]};
const pm=nodes.get(parent);assert.equal(pm.source,facing);assert.equal(pm.pre,'翻前： 你 BTN 開 ，BB 跟');assert.equal(pm.key,'對手下注、你跟|對手過');
assert(sec.get(facing).split('<table')[0].replace(/<[^>]*>/g,'').includes('對手下注，你要怎麼做？'));assert.deepEqual([pm.facts.root.spot,pm.facts.root.pot,pm.facts.root.stack],['BTN_BB',5.5,97.5]);
const cell=(id,tx)=>[...sec.get(id).match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'))[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
const first=v=>{const a=v.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return a?[a[1],a[2].replace(/≈$/,'')]:[];};
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')),out={};
assert.equal(reg.records[parent].label,'CERT-MULTIBOARD');
for(const [rank,[id,pct,label,spr]]of Object.entries(configs)){
 const n=nodes.get(id),r=reg.records[id];assert.equal(n.source,parent);assert.equal(n.key,'對手下注、你跟|對手過、你下注、對手跟|對手過');assert.equal(n.facts.spr,spr);assert.deepEqual([r.frequency_rank,r.solver_profile,r.street,r.assumed_model_node_spr],[+rank,'BTN_BB',2,spr]);
 const routes={flop:{},turn:{},river:{}};for(const tx of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const f=cell(facing,tx),t=cell(parent,tx),v=cell(id,tx);
  for(let i=0;i<5;i++){
   const k=tx+':'+i,fe=first(f[i]),te=first(t[i]);if(fe[0]===parent+'-'+tx&&fe[1]==='跟')routes.flop[k]='跟';
   if(te[0]===id+'-'+tx&&te[1]===label)routes.turn[k]=label;
   if(n.allowed.includes(k)){const x=v[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();assert(['過','下注 ½','下注 ¾'].includes(x));routes.river[k]=x;}
  }
 }
 assert.equal(Object.keys(routes.flop).length,16);if(+rank===104)assert.deepEqual(Object.keys(routes.turn).sort(),['mono:0','paired:0']);
 assert.deepEqual(Object.keys(routes.river).sort(),Object.keys(routes.turn).sort());
 out[rank]={id,parent,facing,pct,spr,spot:'BTN_BB',actor:1,line:`b50 c/x b${pct} c/x`,river_pot:1100+2*(1100*pct/100),river_stack:9475-1100*pct/100,routes};
}console.log(JSON.stringify(out));
