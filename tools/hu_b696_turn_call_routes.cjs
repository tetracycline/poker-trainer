const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const args=process.argv.slice(2),opt=n=>args.includes(n)?args[args.indexOf(n)+1]:null;
const CONFIG={
  76:{id:'ln-opfr-r_model-1phsqr4',source:'ln-opfr-t_vs_probe-8xl9mh',start:'ln-opfr-f_cbet-milqtu',
      turnFirst:'ln-opfr-t_delay-124de8m',section:'opfr',spot:'SB_BB',actor:0,pot:600,stack:9700,
      history:'你過、對手過|你過、對手下注、你跟|',turn_line:'x b50 c',line:'x x/x b50 c/',river_pot:1200,river_stack:9400,spr:7.833},
  89:{id:'ln-ipfr-r_model-bqgbuq',source:'ln-ipfr-t_vs_probe-1993kni',start:'ln-ipfr-f_cbet-vwe0c6',
      section:'ipfr',spot:'BTN_BB',actor:1,pot:550,stack:9750,
      history:'對手過、你過|對手下注、你跟|對手過',turn_line:'b50 c',line:'x x/b50 c/x',river_pot:1100,river_stack:9475,spr:8.614}
};
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={
 console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
 document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}
};c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
 vm.runInContext(fs.readFileSync(f==='nl2_hu_model.js'?(opt('--model-file')||f):f,'utf8'),c,{filename:f});
const targets=new Set(Object.values(CONFIG).map(x=>x.id)),nodes={},html={},otherHtml={};
const full=opt('--snapshot')||opt('--compare');
for(const section of full?['bb','ipfr','opfr','ipc','3bp','iso']:['opfr','ipfr']){
 c.__linesQA.render(section);html[section]=app.innerHTML;
 for(const n of c.__HU_MODEL_LAST.nodes)nodes[n.id]=JSON.parse(JSON.stringify(n));
 const headings=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
 otherHtml[section]=app.innerHTML.slice(0,headings[0]?.index||0)+headings.map((h,i)=>
  targets.has(h[1])?'':app.innerHTML.slice(h.index,headings[i+1]?.index??app.innerHTML.length)).join('');
}
if(opt('--snapshot')){
 assert.equal(Object.keys(nodes).length,392);
 const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json','utf8'));
 const certs=Object.entries(registry.records).filter(([,v])=>v.label==='CERT-MULTIBOARD').map(([id])=>id);
 assert(certs.length>=148);assert([...targets].every(id=>registry.records[id].label==='APPROX'));
 fs.writeFileSync(opt('--snapshot'),JSON.stringify({nodes,otherHtml,certs}));process.exit(0);
}
if(opt('--compare')){
 const before=JSON.parse(fs.readFileSync(opt('--compare'),'utf8'));
 assert.deepEqual(Object.keys(nodes).sort(),Object.keys(before.nodes).sort());
 assert.ok(JSON.stringify(otherHtml)===JSON.stringify(before.otherHtml),'Any UI change beyond the two priced river leaves is rejected');
 for(const[id,n]of Object.entries(nodes)){
  if(!targets.has(id))assert.deepEqual(n,before.nodes[id],id);
  else {
   const stripped=v=>{const out=JSON.parse(JSON.stringify(v));delete out.turnCallPct;delete out.facts.pot;delete out.facts.stack;delete out.facts.spr;return out;};
   assert.deepEqual(stripped(n),stripped(before.nodes[id]),id);
  }
 }
 for(const id of before.certs)assert.deepEqual(nodes[id],before.nodes[id],id);
}
const out={},textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function sectionHTML(section,id){
 const part=html[section].split('id="'+id+'"')[1];assert.ok(part,id);return part.split('<div class="sec"')[0];
}
function cells(section,id,texture){
 const row=sectionHTML(section,id).match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
 return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];
}
const first=cell=>{const m=cell?.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return m?[m[1],m[2].replace(/≈$/,'')]:null;};
for(const[rank,k]of Object.entries(CONFIG)){
 const model=nodes[k.id];assert.ok(model);assert.equal(model.source,k.source);assert.equal(model.key,k.history);
 assert.equal(model.turnCallPct,50);assert.equal(model.facts.root.spot,k.spot);
 assert.deepEqual([model.facts.root.pot,model.facts.root.stack],[k.pot/100,k.stack/100]);
 assert.deepEqual([model.facts.pot,model.facts.stack,model.facts.spr],[k.river_pot/100,k.river_stack/100,k.spr]);
 const face=sectionHTML(k.section,k.source).split('<table')[0];
 if(rank==='76'){
  assert.ok(face.includes('你（SB） 開池 3bb，BB 跟（底池 6bb）'));
  assert.ok(face.includes('BB 下注 50%（3bb），你要跟 3bb（底池 9bb）'));
 }else{
  assert.ok(face.includes('你（BTN） 開池 2.5bb，BB 跟（底池 5.5bb）'));
  assert.ok(face.includes('BB 下注 50%（2.8bb），你要跟 2.8bb（底池 8.3bb）'));
 }
 const route={flop:{},turn:{},river:{}};
 for(const tx of textures){
  const f=cells(k.section,k.start,tx),facing=cells(k.section,k.source,tx),river=cells(k.section,k.id,tx);
  const before=k.turnFirst?cells(k.section,k.turnFirst,tx):[];
  for(let i=0;i<5;i++){
   const key=tx+':'+i,a=first(f[i]),call=first(facing[i]);
   if(a?.[1]==='過' && (k.turnFirst?a[0]===k.turnFirst+'-'+tx:f[i].includes('class="jmp sub" href="#'+k.source+'-'+tx+'"')))
    route.flop[key]='過';
   const ownCheck=!k.turnFirst || (first(before[i])?.[1]==='過' &&
    before[i].includes('class="jmp sub" href="#'+k.source+'-'+tx+'"'));
   if(ownCheck && call?.[0]===k.id+'-'+tx && call[1]==='跟')route.turn[key]='跟';
   if(model.allowed.includes(key)){
    const label=river[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    assert(['過','下注 ⅓','下注 ½','下注 ¾'].includes(label));route.river[key]=label;
   }
  }
 }
 assert(Object.keys(route.flop).length && Object.keys(route.turn).length && Object.keys(route.river).length);
 if(rank==='89')assert.deepEqual(Object.keys(route.flop).sort(),['A_high:2','KQ_high:2','mid_high:2']);
 out[rank]={...k,routes:route,turn_call_pct:50};
}
console.log(JSON.stringify(out));

