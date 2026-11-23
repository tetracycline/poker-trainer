const fs=require('fs'),vm=require('vm');
const assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}}, ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('opfr');
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

const mid='ln-opfr-r_model-1ixkq7a', turn='ln-opfr-t_first-ozcx7m';
const facing='ln-opfr-f_vs_donk-1wk9say', start='ln-opfr-f_cbet-milqtu';
const model=ctx.__HU_MODEL_LAST.nodes.find(n=>n.id===mid);
const parentSection=app.innerHTML.split('id="'+turn+'"')[1].split('<div class="sec"')[0];
assert.ok(parentSection.includes('BB 下注 33%（2bb），你（SB） 跟 2bb'));
assert.equal(model.source,turn);
assert.equal(model.facts.root.spot,'SB_BB');
assert.equal(model.facts.spr,9.5);
const rows={};
for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const opens=cells(start,texture), faced=cells(facing,texture);
  const flop=opens.flatMap((v,i)=>{
    const c=link(faced[i]);
    return link(v)?.[1]==='過' && v.includes('class="jmp sub" href="#'+facing+'-'+texture+'"') &&
      c?.[0]===turn+'-'+texture && c[1]==='跟'?[classes[i]]:[];
  });
  const checked=cells(turn,texture).flatMap((v,i)=>{
    const c=link(v);
    return c?.[0]===mid+'-'+texture && c[1]==='過'?[classes[i]]:[];
  });
  const river=Object.fromEntries(cells(mid,texture).flatMap((v,i)=>{
    const label=v.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    return label&&label!=='—'?[[classes[i],label]]:[];
  }));
  rows[texture]={flop,turn:checked,river};
}
console.log(JSON.stringify(rows));
