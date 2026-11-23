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

const parent='ln-opfr-t_model-4t8fsk', source='ln-opfr-f_vs_donk-1wk9say';
const panels={57:'ln-opfr-r_model-8ze7gv',58:'ln-opfr-r_model-aumml6'};
const models=new Map(ctx.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const sets={};
for(const [rank,mid] of Object.entries(panels)){
  const m=models.get(mid);
  assert.equal(m.source,parent);assert.equal(models.get(parent).source,source);
  assert.equal(m.facts.root.spot,'SB_BB');assert.equal(m.facts.spr,rank==='57'?2.733:4.35);
  const rows={};
  for(const texture of ['low','mid_high','KQ_high','A_high','paired','mono']){
    const keys=(id,target,label)=>cells(id,texture).flatMap((c,i)=>{
      const next=link(c);return next?.[0]===target+'-'+texture&&next[1]===label?[classes[i]]:[];
    });
    rows[texture]={flop:keys(source,parent,'跟'),turn:keys(parent,mid,rank==='57'?'下注 ¾':'下注 ⅓'),
      river:Object.fromEntries(cells(mid,texture).flatMap((c,i)=>{
        const label=c.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
        return label&&label!=='—'?[[classes[i],label]]:[];
      }))};
  }
  sets[rank]=rows;
}
console.log(JSON.stringify(sets));
