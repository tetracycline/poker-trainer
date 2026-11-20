const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path'),zlib=require('node:zlib');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p));
function element(){
 return {value:'',textContent:'',checked:false,items:[],get options(){return this.items;},listeners:{},get innerHTML(){return this.html??'';},set innerHTML(v){this.html=v;this.items=[];this.value='';},appendChild(n){if(!this.items.length&&n.value)this.value=n.value;this.items.push(n);},addEventListener(n,f){this.listeners[n]=f;}};
}
const data=(p)=>JSON.parse(zlib.gunzipSync(read('data/'+p)));
const manifest=JSON.parse(read('data/nl2_hu_offline_manifest.json'));
const expected=(broken)=>{
 const base=data('nl2_hu_exact_boards.json.gz').subgames;
 const games=[...base,...manifest.exact.filter(x=>!broken||x.batch!=='B05').flatMap(x=>data(x.file).subgames)];
 const unique=[...new Map(games.map(c=>[[c.spot,c.version,c.source_sha256].join(':'),c])).values()];
 return [unique.length,unique.filter(c=>c.status==='CERT_EXACT_BOARD_GTO').length];
};
async function qa(broken,search=""){
 const els=new Map();
 const get=id=>{if(!els.has(id))els.set(id,element());return els.get(id);};
 const document={getElementById:get,createElement:element,createDocumentFragment:element};
 const fetch=async p=>(p.endsWith('_b05_local.json.gz')&&broken)?new Response(null,{status:404}):new Response(read(p));
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
(async()=>{await qa(false);await qa(true);console.log('PASS: verified shard counts, partial fetch, strict B04 reachable and unreachable lines; no MODEL upgrade');})().catch(e=>{console.error(e);process.exitCode=1;});
