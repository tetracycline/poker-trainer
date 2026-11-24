const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const args=process.argv.slice(2),option=n=>args.includes(n)?args[args.indexOf(n)+1]:null;
const modelFile=option('--model-file')||'nl2_hu_model.js',uiFile=option('--ui-file')||'nl2.js';
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
 document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
 vm.runInContext(fs.readFileSync(file==='nl2_hu_model.js'?modelFile:file==='nl2.js'?uiFile:file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('3bp');
const id='ln-3bp-3b_t_model-yap927',source='ln-3bp-3b_f_vs_donk-76tzdu',initial='ln-3bp-3b_f_cbet-ke0pam';
const model=ctx.__HU_MODEL_LAST.nodes.find(n=>n.id===id);assert.ok(model);
assert.equal(model.source,source);assert.equal(model.flopCallPct,33);
assert.equal(model.pre,'翻前：BTN 開， 你 BB 3-bet ，BTN 跟');
assert.equal(model.key,'你過、對手下注、你跟|');
assert.deepEqual([model.facts.root.spot,model.facts.root.pot,model.facts.root.stack],['BB3_BTN',20.5,90]);
assert.deepEqual([model.facts.pot,model.facts.stack,model.facts.spr],[34.04,83.23,2.445]);
assert.deepEqual(Array.from(model.allowed).sort(),['KQ_high:2','low:2','mid_high:2']);
function section(name){const s=app.innerHTML.split('id="'+name+'"')[1];assert.ok(s,name);return s.split('<div class="sec"')[0];}
function cells(name,texture){
 const row=section(name).match(new RegExp('<tr[^>]+id="'+name+'-'+texture+'">([\\s\\S]*?)</tr>'));assert.ok(row);
 return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
assert.ok(section(source).includes('BTN 下注 33%（6.8bb），你要跟 6.8bb（底池 27.3bb）'));
const classes=['TPG','TPW','MID','DRAW','WDRAW'],routes={};
for(const texture of ['low','mid_high','KQ_high']){
 const start=cells(initial,texture),facing=cells(source,texture),now=cells(id,texture);
 const parents=[],decisions={};
 for(const [i,cls]of classes.entries()){
  const first=start[i].match(/<a class="jmp" href="#[^"]+">([^<]+)<\/a>/);
  const checks=first?.[1].replace(/≈$/,'')==='過'&&start[i].includes('class="jmp sub" href="#'+source+'-'+texture+'"');
  const calls=[...facing[i].matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)]
    .some(m=>m[1]===id+'-'+texture&&m[2].replace(/≈$/,'')==='跟');
  if(checks&&calls)parents.push(cls);
  if(model.allowed.includes(texture+':'+i)){
   const label=now[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
   assert.equal(label,'過');decisions[cls]=label;
  }
 }
 assert.deepEqual(parents,['MID']);assert.deepEqual(decisions,{MID:'過'});
 routes[texture]={parents,decisions,initial_action:'x',facing_action:'b33',call_action:'c'};
}
const digest=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
console.log(JSON.stringify({rank:121,id,initial,source,spot:'BB3_BTN',seat:0,line:'x b33 c/',
 root_pot:2050,root_stack:9000,flop_bet:677,turn_pot:3404,turn_stack:8323,spr:2.445,routes,
 source_sha256:{model:digest(modelFile),ui:digest(uiFile)}}));

