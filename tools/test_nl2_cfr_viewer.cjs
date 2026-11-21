const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path'),zlib=require('node:zlib');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p));
function element(){
 return {value:'',textContent:'',checked:false,items:[],get options(){return this.items;},listeners:{},get innerHTML(){return this.html??'';},set innerHTML(v){this.html=v;this.items=[];this.value='';},appendChild(n){if(!this.items.length&&n.value)this.value=n.value;this.items.push(n);},addEventListener(n,f){this.listeners[n]=f;}};
}
const data=(p)=>JSON.parse(zlib.gunzipSync(read('data/'+p)));
const manifest=JSON.parse(read('data/nl2_hu_offline_manifest.json'));
const expected=(broken)=>{
 const files=['nl2_hu_exact_boards.json.gz','nl2_hu_exact_boards_b04.json.gz','nl2_hu_exact_boards_b05.json.gz',...manifest.exact.map(x=>x.file)];
 const games=files.filter(x=>x!==broken).flatMap(x=>data(x).subgames);
 const unique=[...new Map(games.map(c=>[[c.spot,c.version,c.source_sha256].join(':'),c])).values()];
 return [unique.length,unique.filter(c=>c.status==='CERT_EXACT_BOARD_GTO').length];
};
async function qa(broken,search=""){
 const els=new Map();
 const get=id=>{if(!els.has(id))els.set(id,element());return els.get(id);};
 const document={getElementById:get,createElement:element,createDocumentFragment:element};
 const fetch=async p=>(broken&&p.endsWith('/'+broken))?new Response(null,{status:404}):new Response(read(p));
 vm.runInNewContext(read('nl2-cfr.js').toString('utf8'),{document,fetch,Response,DecompressionStream,atob,URLSearchParams,URL,location:{search,href:'https://test.invalid/nl2-cfr.html'+search}});
 for(let i=0;i<40&&!get('status').textContent;i++)await new Promise(r=>setTimeout(r,25));
 const [total,cert]=expected(broken);
 assert.match(get('status').textContent,new RegExp('已載入 '+total+' 個'));
 if(broken)assert.match(get('status').textContent,/有一批未能載入/);
 assert.match(get('status').textContent,/MODEL .*0\/392/);
 assert.match(get('details').innerHTML,/SPR/);
 const boxes=get('combos').items[0]?.items??[];
 assert.ok(boxes.length,'legacy populated even without EV');
 assert.notEqual(boxes[0].items[2].textContent,'未收錄');
 if(search){
  assert.match(get('details').innerHTML,/3d6h8s5c7d.*x b50 c\/x b50 r c\/x/);
  assert.match(get('details').innerHTML,/限制下注選單/);
  assert.match(get('details').innerHTML,/跨街可達手牌 63／/);
  return;
 }
 if(!broken){
  assert.match(get('status').textContent,new RegExp('CERT：'+cert+'；'));
  get('ver').value='gto';get('ver').listeners.change();
  const games=get('game').items;assert.ok(games.length);
  get('game').value=games.find(x=>x.textContent.includes('QsJh4d7s (x x)')).value;
  get('game').listeners.change();
  assert.match(get('details').innerHTML,/LOCAL_20261120_B04_BB3_BTN_QsJh4d_GTO/);
  assert.match(get('details').innerHTML,/跨街可達手牌 28／/);
  const newer=get('combos').items[0]?.items??[];
  assert.equal(newer.length,28);assert.notEqual(newer[0].items[2].textContent,'未收錄');
  get('game').value=games.find(x=>x.textContent.includes('QsJh4d7s (b75 r c)')).value;
  get('game').listeners.change();
  assert.match(get('combos').textContent,/沒有可達手牌/);
 }
}
(async()=>{await qa(null);await qa('nl2_hu_exact_boards_b05_local.json.gz');await qa('nl2_hu_exact_boards_b04.json.gz');await qa('nl2_hu_exact_boards_b05.json.gz');await qa(null,'?spot=SB_BB&version=gto&sha=076978568f1610131e757eacf176b1a710995ff9fbd332d143fac9d1896e7d68&board=3d6h8s5c7d&line=x%20b50%20c%2Fx%20b50%20r%20c%2Fx');console.log('PASS: verified shard counts, partial fetch, strict B04 reachable and unreachable lines; no MODEL upgrade');})().catch(e=>{console.error(e);process.exitCode=1;});
