const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p));
function element(){
 return {value:'',textContent:'',checked:false,items:[],get options(){return this.items;},listeners:{},get innerHTML(){return this.html??'';},set innerHTML(v){this.html=v;this.items=[];this.value='';},appendChild(n){if(!this.items.length&&n.value)this.value=n.value;this.items.push(n);},addEventListener(n,f){this.listeners[n]=f;}};
}
async function qa(broken,search=""){
 const els=new Map();
 const get=id=>{if(!els.has(id))els.set(id,element());return els.get(id);};
 const document={getElementById:get,createElement:element,createDocumentFragment:element};
 const fetch=async p=>(p.endsWith('_b04_local.json.gz')&&broken)?new Response(null,{status:404}):new Response(read(p));
 vm.runInNewContext(read('nl2-cfr.js').toString('utf8'),{document,fetch,Response,DecompressionStream,atob,URLSearchParams,URL,location:{search,href:'https://test.invalid/nl2-cfr.html'+search}});
 for(let i=0;i<40&&!get('status').textContent;i++)await new Promise(r=>setTimeout(r,25));
 assert.match(get('status').textContent,broken?/347.*有一批未能載入/:/354/);
 assert.match(get('status').textContent,/MODEL .*0\/392/);
 assert.match(get('details').innerHTML,/SPR/);
 const boxes=get('combos').items[0]?.items??[];
 assert.ok(boxes.length,'legacy populated even without EV');
 assert.notEqual(boxes[0].items[2].textContent,'未收錄');
 if(!broken){
  assert.match(get('status').textContent,/CERT：121/);
  get('ver').value='gto';get('ver').listeners.change();
  const games=get('game').items;assert.ok(games.length);
  get('game').value=games.at(-1).value;
  get('game').listeners.change();
  assert.match(get('details').innerHTML,/LOCAL_20261120_B04_BB3_BTN_QsJh4d_GTO/);
  const newer=get('combos').items[0]?.items??[];
  assert.ok(newer.length);assert.notEqual(newer[0].items[2].textContent,'未收錄');
 }
}
(async()=>{await qa(false);await qa(true);console.log('PASS: 354 full, 347 partial, both render combo rows; no MODEL upgrade');})().catch(e=>{console.error(e);process.exitCode=1;});
