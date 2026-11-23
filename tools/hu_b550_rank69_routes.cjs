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
const mid='ln-ipfr-r_model-159a6z6', turn='ln-ipfr-t_stab-9egy37', root='ln-ipfr-f_vs_donk-14oe091';
const r=ctx.__HU_MODEL_LAST.nodes.find(n=>n.id===mid);
assert.equal(r.source,turn);
assert.equal(r.pre,'翻前： 你 BTN 開 ，BB 跟');
const rows={};
for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']){
  const links=(id,to,action)=>cells(id,texture).flatMap((c,i)=>{const a=link(c);return a&&a[0]===to+'-'+texture&&a[1]===action?[classes[i]]:[]});
  rows[texture]={flop:links(root,turn,'跟'),turn:links(turn,mid,'過'),river:cells(mid,texture).flatMap((c,i)=>/^過(?:\s|<)/.test(c)?[classes[i]]:[])};
}
assert.deepEqual(rows.low,{flop:['TPW','WDRAW'],turn:['TPW'],river:['TPW']});
assert.deepEqual(rows.mid_high.turn,['MID']);
assert.deepEqual(rows.mid_high.river,['MID']);
console.log(JSON.stringify(rows));
