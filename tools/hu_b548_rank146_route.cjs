const fs=require('fs'),vm=require('vm');
const assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}}, ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('opfr');
const id='ln-opfr-r_model-19h8rla';
const nodes=ctx.__HU_MODEL_LAST.nodes;
const river=nodes.find(n=>n.id===id),turn=nodes.find(n=>n.id===river.source);
assert.equal(river.pre,'翻前： 你 UTG 開 ，CO 跟');
assert.equal(river.key,'你下注、對手跟|你過、對手過|');
assert.equal(turn.source,'ln-opfr-f_cbet-1ihx52e');
assert.deepEqual([river.facts.root.pot,river.facts.root.stack,river.facts.pot,river.facts.stack],[6.5,97.5,13,94.25]);
const classes=['TPG','TPW','MID','DRAW','WDRAW'];
function cells(node,texture){
  const block=app.innerHTML.split('id="'+node+'"')[1].split('<div class="sec"')[0];
  const row=block.match(new RegExp('<tr[^>]+id="'+node+'-'+texture+'">([\\s\\S]*?)</tr>'))[1];
  return [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
const kqFlop = cells(turn.source,'KQ_high');
assert.ok(kqFlop[1].includes('href="#'+turn.id+'-KQ_high">下注 ½'));
const kqTurn = cells(turn.id,'KQ_high');
assert.ok(kqTurn[1].includes('>下注 ⅓'));
assert.ok(kqTurn.every(c=>!c.includes('href="#'+river.id+'-KQ_high"')));
const result={};
for(const texture of ['A_high','KQ_high','mid_high','low','paired','mono']){
 const target=cells(river.id,texture).flatMap((c,i)=>river.allowed.includes(texture+':'+i)&&c.replace(/<[^>]+>/g,'').trim().startsWith('過')?[classes[i]]:[]);
 if(!target.length)continue;
 const linked=(parent,child,txt)=>cells(parent,texture).flatMap((c,i)=>c.includes('href="#'+child+'-'+texture+'">'+txt)?[classes[i]]:[]);
 result[texture]={flop:linked(turn.source,turn.id,'下注 ½'),turn:linked(turn.id,river.id,'過'),river:target};
}
assert.deepEqual(result,{A_high:{flop:['WDRAW'],turn:['WDRAW'],river:['WDRAW']},paired:{flop:['TPG','WDRAW'],turn:['WDRAW'],river:['WDRAW']},mono:{flop:['DRAW','WDRAW'],turn:['WDRAW'],river:['WDRAW']}});
console.log(JSON.stringify(result));
