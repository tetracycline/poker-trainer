// Read actual primary UI paths for three CO/BB river decisions after a turn lead.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const CONFIG={
  92:{id:'ln-bb-r_model-1t7cwh6',pct:33,spr:4.818},
  93:{id:'ln-bb-r_model-d919qu',pct:50,spr:3.932},
  94:{id:'ln-bb-r_model-lf823j',pct:75,spr:3.045}
};
const parent='ln-bb-t_model-cge9jz',facing='ln-bb-f_vs_cbet-m7k2cp';
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,
 location:{hash:'#lines'},scrollTo(){},addEventListener(){},
 document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const path of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
 vm.runInContext(fs.readFileSync(path,'utf8'),c,{filename:path});
c.__linesQA.render('bb');
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id,texture){
 const section=app.innerHTML.split('id="'+id+'"')[1]?.split('<div class="sec"')[0];assert.ok(section,id);
 const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));assert.ok(row,id+texture);
 return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
function first(html){const m=html.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return m?[m[1],m[2].replace(/≈$/,'')]:null;}
const original=nodes.get(parent);
assert.equal(original.source,facing);assert.equal(original.key,'你過、對手下注、你跟|');
assert.deepEqual([original.facts.root.spot,original.facts.root.pot,original.facts.root.stack,original.facts.pot],['CO_BB',5.5,97.5,11]);
// The exact 50% source agrees with the existing parent's genuinely solved boards.
const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json','utf8'));
const oldParent=registry.records[parent];assert.equal(oldParent.label,'CERT-MULTIBOARD');
assert.ok(oldParent.certified_3_to_5_exact_flop_boards.filter(b=>b.actual_exact_action_line==='x b50 c/'&&b.actual_pot_bb===11&&b.actual_effective_stack_bb===94.75).length>=3);
const contracts=JSON.parse(fs.readFileSync('data/nl2_hu_verified_extensions.json','utf8')).trainer_route_contract.routes;
const out={};
for(const[rank,k]of Object.entries(CONFIG)){
 const n=nodes.get(k.id);assert.equal(n.source,parent);assert.equal(n.key,'你過、對手下注、你跟|你下注、對手跟|');
 assert.equal(n.facts.root.spot,'CO_BB');assert.equal(n.facts.spr,k.spr);
 assert.deepEqual(contracts[k.id].streets,['x bet c','b'+k.pct+' c','']);assert.equal(contracts[k.id].seat,0);
 const bet=Math.floor((1100*k.pct+50)/100),riverPot=1100+2*bet,riverStack=9475-bet;
 assert.ok(Math.abs(riverStack/riverPot/k.spr-1)<=.05,'Retain the existing exact-audit SPR limit');
 const route={flop:{},turn:{},river:{}};
 for(const texture of textures){
  const f=cells(facing,texture),t=cells(parent,texture),r=cells(k.id,texture);
  for(let i=0;i<5;i++){
   const key=texture+':'+i,flop=first(f[i]),turn=first(t[i]);
   if(flop?.[0]===parent+'-'+texture&&flop[1]==='跟')route.flop[key]='跟';
   if(turn?.[0]===k.id+'-'+texture)route.turn[key]=turn[1];
   if(n.allowed.includes(key)){
    const action=r[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    assert.ok(['過','下注 ⅓','下注 ½','下注 ¾'].includes(action));route.river[key]=action;
   }
  }
 }
 assert.deepEqual(Object.keys(route.turn).sort(),[...n.allowed].sort());
 const label={33:'下注 ⅓',50:'下注 ½',75:'下注 ¾'}[k.pct];assert.ok(Object.values(route.turn).every(x=>x===label));
 out[rank]={...k,rank:Number(rank),spot:'CO_BB',actor:0,source:parent,flop_line:'x b50 c',
  line:'x b50 c/b'+k.pct+' c/',root_pot:550,root_stack:9750,turn_pot:1100,turn_stack:9475,
  river_pot:riverPot,river_stack:riverStack,actual_spr:riverStack/riverPot,routes:route};
}
console.log(JSON.stringify(out));
