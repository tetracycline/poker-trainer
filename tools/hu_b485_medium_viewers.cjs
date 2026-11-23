const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const zlib=require('node:zlib');
const {webcrypto}=require('node:crypto');
const read=p=>JSON.parse(fs.readFileSync(p));
const unzip=p=>JSON.parse(zlib.gunzipSync(fs.readFileSync(p)));
const helper=fs.readFileSync('nl2_locked_medium.js','utf8');
const viewer=fs.readFileSync('nl2-cfr.js','utf8');
const report=read('data/nl2_hu_b485_locked_medium.json');
const old=read('data/nl2_hu_b483_locked_medium.json');
const registry=JSON.parse(require('node:child_process').execFileSync('git',['show','d0fe026b3cd59b50450f99471bd27c55e7d4b522:data/nl2_hu_multiboard_status_current.json'],{maxBuffer:16*1024*1024}));
const sealed=new Map();
function store(run,item,official){
  sealed.set(run+'/'+item.source_sha256,{game:item,run,official});
}
for(const suffix of ['','_b04','_b05']){
  for(const c of unzip('data/nl2_hu_exact_boards'+suffix+'.json.gz').subgames)store(c.source_run_id,c,true);
}
for(const [run,code] of [[44732810327,'B4_MICRO'],[44736420272,'B5_SBGAPS']]){
  const data=unzip('data/solver_evidence/NL2_MULTIBOARD_'+code+'.json.gz');
  for(const artifact of data.artifacts)for(const c of artifact.cases)store(run,c,false);
}
function reportFor(path){
  if(path==='data/nl2_hu_b483_locked_medium.json')return old;
  if(path==='data/nl2_hu_b485_locked_medium.json')return report;
  return null;
}
const globals={URL,URLSearchParams,crypto:webcrypto,atob,TextEncoder,Response,DecompressionStream,console};
function element(){
  let text='',html='',value='';
  return {children:[],checked:true,addEventListener(){},get options(){return this.children;},
    get value(){return value;},set value(v){value=String(v);},
    get textContent(){return text;},set textContent(v){text=String(v);html='';this.children=[];},
    get innerHTML(){return html;},set innerHTML(v){html=String(v);text='';value='';this.children=[];},
    appendChild(c){if(!this.children.length&&c.value)value=c.value;this.children.push(c);return c;},
    replaceChildren(...children){this.innerHTML='';this.children=children;}};
}
function htmlPage(url,fetch){
  const elements=new Map();
  const by=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  const ctx=vm.createContext({...globals,document:{getElementById:by,createElement:element,createDocumentFragment:element},
    location:new URL(url,'https://test.local/'),fetch});
  vm.runInContext(helper,ctx);
  return {ctx,by};
}
async function officialView(sample,expectZero=false){
  const {row,game,node}=sample;
  const args=new URLSearchParams({spot:row.spot,version:row.version,run:row.source_run_id,sha:row.source_sha256,
                                  board:row.public_board,line:row.line,seat:row.acting_seat});
  const pathKey=[node.board,node.line,node.acting_seat].join('|');
  const maskOld=node.eligible_action_masks_b64;
  const countOld=Array.from(Buffer.from(maskOld,'base64')).filter(Boolean).length;
  const index={schema:'HU_NL2_EXACT_BOARD_CFR_V1',generic_model_upgrades:0,exact_subgame_count:1,subgames:[game]};
  const overlay={schema:'HU_NL2_SEQUENTIAL_REACH_OVERLAY_V1',subgames_by_source_sha256:{
    [game.source_sha256]:{nodes:{[pathKey]:{mask:maskOld,count:countOld}}}}};
  async function fetch(path){
    const medium=reportFor(path);if(medium)return Response.json(medium);
    if(path.includes('offline_manifest'))return Response.json({schema:'HU_NL2_OFFLINE_SHARDS_V1',exact:[],sequential:[]});
    if(path.includes('sequential_reach'))return new Response(zlib.gzipSync(JSON.stringify(overlay)));
    if(path.endsWith('nl2_hu_exact_boards.json.gz'))return new Response(zlib.gzipSync(JSON.stringify(index)));
    if(path.includes('exact_boards_b'))return new Response(zlib.gzipSync(JSON.stringify({...index,exact_subgame_count:0,subgames:[]})));
    throw Error(path);
  }
  const {ctx,by}=htmlPage('nl2-cfr.html?'+args,fetch);
  vm.runInContext(viewer,ctx);
  for(let i=0;i<300&&!by('status').textContent;i++)await new Promise(r=>setTimeout(r,10));
  assert.ok(by('status').textContent.startsWith('已載入'),by('status').textContent);
  assert.ok(by('details').innerHTML.includes(ctx.nl2LockedMedium.describe(row)),by('details').innerHTML);
  if(expectZero){
    assert.match(by('combos').textContent,/沒有相容的雙方私牌/);
    assert.equal(by('combos').children.length,0);return;
  }
  const hands=game.hands_by_seat[row.acting_seat];
  const mask=Buffer.from(row.compatible_action_mask_b64,'base64'),best=Buffer.from(node.best_ev_action_indices_b64,'base64');
  const expected=hands.flatMap((hand,i)=>mask[i]?
    [[hand,node.actions.filter((action,j)=>mask[i]&(1<<j)).join(' / '),node.actions[best[i]]]]:[]);
  const shown=by('combos').children[0].children.map(tr=>tr.children.map(td=>td.textContent));
  assert.deepEqual(shown,expected);
}
async function multiboardView(sample){
  const {row,model,b,game,node}=sample;
  const {ctx,by}=htmlPage('nl2-multiboard.html',async path=>{
    const medium=reportFor(path);
    return medium?Response.json(medium):new Response(fs.readFileSync(path));
  });
  const page=fs.readFileSync('nl2-multiboard.js','utf8');
  vm.runInContext(page.slice(page.indexOf('const el='),page.indexOf("el('model').addEventListener")),ctx);
  Object.assign(ctx,{testModel:model,testBoard:b,testRegistry:registry});
  vm.runInContext('chosenModel=testModel;chosenBoard=testBoard;status=testRegistry;',ctx);
  const version=row.version==='gto'?'gto':row.version+'@'+b.nl2_locked_variants.findIndex(v=>v.sha256===row.source_sha256&&v.run_id===row.source_run_id);
  by('version').value=version;
  await vm.runInContext('selectVersion()',ctx);
  assert.ok(by('locked-medium').textContent.includes(ctx.nl2LockedMedium.describe(row)));
  if(!row.strict_legal_combos){
    assert.equal(by('combo-rows').children.length,0);
    assert.match(by('details').textContent,/沒有相容/);
    return;
  }
  const shown=by('combo-rows').children[0].children.map(tr=>tr.children[0].textContent);
  const mask=Buffer.from(row.compatible_action_mask_b64,'base64');
  const wanted=game.hands_by_seat[row.acting_seat].filter((_,i)=>mask[i]);
  assert.deepEqual(shown,wanted);
  assert.ok(node.strict_legal_best_ev_action_indices_b64);
}
async function main(){
  const ctx=vm.createContext({...globals,fetch:async path=>Response.json(reportFor(path))});
  vm.runInContext(helper,ctx);
  const audit=ctx.nl2LockedMedium,combined=await audit.load(),bound=new Map(),samples=[];
  for(const [key,row] of [...Object.entries(report.references),...Object.entries(report.gto_references)]){
    const [mid,board,line,seat,run,sha]=JSON.parse(key),model=registry.records[mid];
    const b=model.certified_3_to_5_exact_flop_boards.find(x=>x.public_board===board&&x.actual_exact_action_line===line&&x.acting_seat===seat);
    assert.equal(audit.lookup(combined,model,b,{version:row.version,source_run_id:run,source_sha256:sha}).source_sha256,sha);
    const id=run+'/'+sha,source=sealed.get(id);assert.ok(source,id);
    const {game,official}=source;
    if(!bound.has(id))bound.set(id,await audit.bindCase(combined,game,run));
    const node=game.nodes.find(n=>(n.public_board??n.board)===board&&(n.exact_node_line??n.line)===line&&n.acting_seat===seat);
    assert.ok(node);
    const applied=bound.get(id).get(node);
    assert.equal(applied?.row.strict_legal_combos,row.strict_legal_combos);
    assert.equal(applied?.mask,Buffer.from(row.compatible_action_mask_b64,'base64').toString('latin1'));
    samples.push({row,game,node,official,model,b});
  }
  const official=samples.filter(s=>s.official);
  for(const version of ['gto','exp_ip','exp_oop']){
    const selected=official.filter(s=>s.row.version===version);
    const pos=selected.find(s=>s.row.strict_legal_combos>0&&s.row.strict_legal_combos<s.node.reachable_combos);
    const zero=selected.find(s=>s.row.strict_legal_combos===0&&s.node.reachable_combos>0);
    assert.ok(pos&&zero);await officialView(pos);await officialView(zero,true);
  }
  const multi=samples.filter(s=>!s.official);
  for(const version of ['gto','exp_oop']){
    const pos=multi.find(s=>s.row.version===version&&s.row.strict_legal_combos>0);
    const zero=multi.find(s=>s.row.version===version&&s.row.strict_legal_combos===0);
    assert.ok(pos&&zero);await multiboardView(pos);await multiboardView(zero);
  }
  const sample=official[0];
  const changed={...sample.game,hands_by_seat:sample.game.hands_by_seat.map(h=>[...h].reverse())};
  await assert.rejects(audit.bindCase(combined,changed),/SHA/);
  const altered={...sample.node, actions:[...sample.node.actions].reverse()};
  await assert.rejects(audit.bindMask(sample.row,sample.game,altered),/順序/);
  assert.ok(fs.readFileSync('nl2-cfr.html','utf8').includes('src="nl2_locked_medium.js'));
  console.log('Verified',samples.length,'B485 board references in both viewers and six positive/zero official deep links.');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
