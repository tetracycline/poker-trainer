const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const args=process.argv.slice(2),option=n=>args.includes(n)?args[args.indexOf(n)+1]:null;
const config={
  75:{id:'ln-3bp-3b_t_model-10ve86c',source:'ln-3bp-3b_f_vs_donk-1vxcsw1',spot:'CO3_BTN',seat:1,pot:1650,stack:9250,line:'b33 c/x'},
  84:{id:'ln-3bp-3b_t_model-ciziut',source:'ln-3bp-3b_f_vs_donk-12vwqfc',spot:'SB3_BTN',seat:0,pot:2100,stack:9000,line:'x b33 c/'},
  103:{id:'ln-3bp-3c_t_model-owdwy',source:'ln-3bp-3c_f_vs_cbet-1pj8rrc',spot:'BB3_BTN',seat:1,pot:2050,stack:9000,line:'b33 c/x'},
  121:{id:'ln-3bp-3b_t_model-yap927',source:'ln-3bp-3b_f_vs_donk-76tzdu',spot:'BB3_BTN',seat:0,pot:2050,stack:9000,line:'x b33 c/'}
};
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},context={
  console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}
};
context.window=context;vm.createContext(context);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
  vm.runInContext(fs.readFileSync(file==='nl2_hu_model.js'?(option('--model-file')||file):file==='nl2.js'?(option('--ui-file')||file):file,'utf8'),context,{filename:file});
const nodes={};let html='';
for(const section of ['bb','ipfr','opfr','ipc','3bp','iso']){
  context.__linesQA.render(section);
  for(const n of context.__HU_MODEL_LAST.nodes)
    nodes[n.id]=JSON.parse(JSON.stringify({id:n.id,source:n.source,key:n.key,allowed:n.allowed,facts:n.facts,flopCallPct:n.flopCallPct}));
  if(section==='3bp')html=app.innerHTML;
}
const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json','utf8'));
assert.equal(Object.keys(nodes).length,392);
if(option('--snapshot')){
  const certs=Object.entries(registry.records).filter(([,m])=>m.label==='CERT-MULTIBOARD').map(([id])=>id).sort();
  assert(certs.length>=146);
  fs.writeFileSync(option('--snapshot'),JSON.stringify({nodes,certs,counts:[registry.CERT_MULTIBOARD,registry.APPROX]}));
  process.exit(0);
}
if(option('--compare')){
  const before=JSON.parse(fs.readFileSync(option('--compare'),'utf8'));
  assert.deepEqual(Object.keys(nodes).sort(),Object.keys(before.nodes).sort());
  for(const [id,old]of Object.entries(before.nodes)){
    assert.equal(nodes[id].key,old.key,id);
    assert.equal(nodes[id].source,old.source,id);
    assert.deepEqual(nodes[id].allowed,old.allowed,id);
    if(before.certs.includes(id))assert.deepEqual(nodes[id].facts,old.facts,id);
  }
}
const classes=['TPG','TPW','MID','DRAW','WDRAW'];
function cells(id,texture){
  const section=html.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
  return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];
}
const out={};
for(const [rank,c]of Object.entries(config)){
  const model=nodes[c.id],bet=Math.floor((c.pot*33+50)/100),pot=c.pot+2*bet,stack=c.stack-bet;
  assert.equal(model.source,c.source);assert.equal(model.flopCallPct,33);
  assert.deepEqual([model.facts.pot,model.facts.stack],[pot/100,stack/100]);
  assert.equal(model.facts.spr,Math.round(stack/pot*1000)/1000);
  const routes={};
  for(const tx of ['low','mid_high','KQ_high','A_high','paired','mono']){
    const prior=cells(c.source,tx),now=cells(c.id,tx),parents=[],decisions={};
    for(const [i,name]of classes.entries()){
      if(prior[i]&&[...prior[i].matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)].some(m=>m[1]===c.id+'-'+tx&&m[2].replace(/≈$/,'')==='跟'))parents.push(name);
      if(model.allowed.includes(tx+':'+i))decisions[name]=now[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    }
    if(parents.length)routes[tx]={parents,decisions};
  }
  out[rank]={...c,turn_pot:pot,turn_stack:stack,spr:model.facts.spr,routes};
}
console.log(JSON.stringify(out));
