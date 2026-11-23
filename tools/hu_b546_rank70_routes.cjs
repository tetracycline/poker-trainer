const fs=require('fs'),vm=require('vm');
const assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}}, ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('ipfr');
const n=ctx.__HU_MODEL_LAST.nodes.find(n=>n.id==='ln-ipfr-t_model-qcljc6');

const classes=['TPG','TPW','MID','DRAW','WDRAW'];
assert.equal(n.source,'ln-ipfr-f_vs_donk-14oe091');
assert.equal(n.pre,'翻前： 你 BTN 開 ，BB 跟');
assert.equal(n.key,'對手下注、你跟|對手過');
assert.deepEqual([n.facts.root.pot,n.facts.root.stack,n.facts.pot],[5.5,97.5,11]);
function cells(id,texture) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'))[1];
  return [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
function link(cell){
  const a=cell.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
  return a ? [a[1],a[2].replace(/≈$/,'')] : null;
}
const mid='ln-ipfr-r_model-nk1lkm';
const river=ctx.__HU_MODEL_LAST.nodes.find(node=>node.id===mid);
assert.equal(river.source,n.id);
assert.equal(river.key,'對手下注、你跟|對手過、你過|對手過');
const rows={};
for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const linked=(id,target,label)=>cells(id,texture).flatMap((c,i)=>{
    const a=link(c);
    return a && a[0]===target+'-'+texture && a[1]===label ? [classes[i]] : [];
  });
  const terminal=cells(mid,texture).flatMap((c,i)=>/^過(?:\s|<)/.test(c) ? [classes[i]] : []);
  rows[texture]={flop:linked(n.source,n.id,'跟'),turn:linked(n.id,mid,'過'),river:terminal};
  for(const cls of terminal)assert.ok(river.allowed.includes(texture+':'+classes.indexOf(cls)));
}
assert.deepEqual(rows.low,{flop:['TPG','MID','DRAW'],turn:['MID'],river:['MID']});
for(const texture of ['paired','mono','KQ_high']){
  assert.ok(rows[texture].turn.includes('MID') && rows[texture].river.includes('MID'));
}
console.log(JSON.stringify(rows));
