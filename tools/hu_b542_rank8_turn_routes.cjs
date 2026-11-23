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
function links(node){
  const sec=app.innerHTML.split('id="'+node+'"')[1].split('<div class="sec"')[0];
  const row=sec.match(new RegExp('<tr[^>]+id="'+node+'-low">([\\s\\S]*?)</tr>'))[1];
  return [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>{
    const a=m[1].match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
    return a ? [a[1],a[2].replace(/≈$/,'')] : null;
  });
}
const flop=links(n.source).flatMap((l,i)=>l && l[0]===n.id+'-low' && l[1]==='跟'?[classes[i]]:[]);
const turn=Object.fromEntries(links(n.id).flatMap((l,i)=>{
  if(!l)return [];
  assert.ok(n.allowed.includes('low:'+i));
  const token={'過':'x','下注 ½':'b50'}[l[1]];
  assert.ok(token);
  return [[classes[i],token]];
}));
assert.deepEqual(flop,['TPG','MID','DRAW']);
assert.deepEqual(turn,{TPG:'b50',MID:'x',DRAW:'b50'});
console.log(JSON.stringify({flop,turn}));
