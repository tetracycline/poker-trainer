const fs=require('fs'),vm=require('vm');
const assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}}, ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('ipfr');
function cells(id,texture) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'))[1];
  return [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
function link(cell){
  const a=cell.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
  return a ? [a[1],a[2].replace(/≈$/,'')] : null;
}
const classes=['TPG','TPW','MID','DRAW','WDRAW'];

const mid='ln-ipfr-r_model-1mcb4lz', turn='ln-ipfr-t_vs_barrel-1oknt40', flop='ln-ipfr-f_vs_donk-14oe091';
const model=ctx.__HU_MODEL_LAST.nodes.find(n=>n.id===mid);
assert.equal(model.source,turn);
assert.deepEqual(Array.from(model.allowed),['A_high:1']);
assert.equal(model.facts.root.spot,'BTN_BB');
assert.equal(model.facts.spr,4.083);
const rows={};
for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']) {
  const next=(id,target,label,secondary=false)=>cells(id,texture).flatMap((c,i)=>{
    const primary=link(c);
    const dest=target+'-'+texture;
    const reaches=secondary?c.includes('class="jmp sub" href="#'+dest+'">若面對下注→'):primary?.[0]===dest;
    return primary?.[1]===label && reaches?[classes[i]]:[];
  });
  rows[texture]={flop:next(flop,turn,'跟',true),turn:next(turn,mid,'跟'),river:cells(mid,texture).flatMap((c,i)=>/^過(?:\s|<)/.test(c)?[classes[i]]:[])};
}
assert.deepEqual(rows.A_high.turn,['TPW']);
assert.deepEqual(rows.A_high.river,['TPW']);
console.log(JSON.stringify(rows));
