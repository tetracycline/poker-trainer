const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const args=process.argv.slice(2),opt=n=>args.includes(n)?args[args.indexOf(n)+1]:null;
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={
  console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}
};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
  vm.runInContext(fs.readFileSync(f==='nl2_hu_model.js'?(opt('--model-file')||f):f==='nl2.js'?(opt('--ui-file')||f):f,'utf8'),c,{filename:f});
c.__linesQA.render('3bp');
const id='ln-3bp-3c_t_model-owdwy',source='ln-3bp-3c_f_vs_cbet-1pj8rrc';
const model=c.__HU_MODEL_LAST.nodes.find(n=>n.id===id);
assert.equal(model.source,source);assert.equal(model.key,'對手下注、你跟|對手過');
assert.equal(model.flopCallPct,33);assert.equal(model.facts.root.spot,'BB3_BTN');
assert.deepEqual([model.facts.root.pot,model.facts.root.stack],[20.5,90]);
assert.deepEqual([model.facts.pot,model.facts.stack,model.facts.spr],[34.04,83.23,2.445]);
const section=key=>app.innerHTML.split('id="'+key+'"')[1].split('<div class="sec"')[0];
const face=section(source).split('<table')[0];
assert.ok(face.includes('你（BTN） 開池 2.5bb，BB 3-bet 到 10bb，你（BTN） 跟（底池 20.5bb）'));
assert.ok(face.includes('BB 下注 33%（6.8bb），你要跟 6.8bb（底池 27.3bb）'));
function cells(key,texture){
  const row=section(key).match(new RegExp('<tr[^>]+id="'+key+'-'+texture+'">([\\s\\S]*?)</tr>'));
  return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];
}
const classes=['TPG','TPW','MID','DRAW','WDRAW'],routes={};
for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const prior=cells(source,texture),now=cells(id,texture),parents=[],decisions={};
  for(const [i,name] of classes.entries()){
    if(prior[i]&&[...prior[i].matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)]
      .some(m=>m[1]===id+'-'+texture&&m[2].replace(/≈$/,'')==='跟'))parents.push(name);
    if(model.allowed.includes(texture+':'+i))decisions[name]=now[i].split('<small')[0].split('<a class="jmp sub"')[0]
      .replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  }
  if(parents.length)routes[texture]={parents,decisions};
}
for(const texture of ['low','mid_high','KQ_high']){
  assert.deepEqual(routes[texture].parents,['TPG','TPW','MID','DRAW']);
  assert.deepEqual(routes[texture].decisions,{TPG:'下注 ½',TPW:'下注 ⅓',MID:'過',DRAW:'下注 ½'});
}
console.log(JSON.stringify({id,source,spot:'BB3_BTN',seat:1,line:'b33 c/x',history:model.key,
  root_pot:2050,root_stack:9000,flop_bet:677,turn_pot:3404,turn_stack:8323,spr:model.facts.spr,routes}));
