(()=>{'use strict';
const by=id=>document.getElementById(id);
const fmt=x=>x==null?'—':typeof x==='number'?x.toLocaleString('en-US',{maximumFractionDigits:4}):String(x);
const setText=(el,s)=>{el.textContent=s;return el;};
const option=(list,k,label)=>{const op=document.createElement('option');op.value=k;op.textContent=label;list.appendChild(op);};
let all=[],subset=[],game=null,current=null,pathReach=Object.create(null);
const selS=by('spot'),selV=by('ver'),selG=by('game'),selN=by('node'),selFocus=by('focus');
const mediumCandidate=n=>!!n.b50_relative_equity_mix?.nonpolarized_medium_bet_candidate;
const setHtml=(id,h)=>{by(id).innerHTML=h;};
const copyOpts=(el,items)=>{el.innerHTML='';for(const [k,l] of items)option(el,k,l);};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function selectSpot(){
 const spot=selS.value,versions=[...new Set(all.filter(c=>c.spot===spot).map(c=>c.version))];
 copyOpts(selV,versions.map(v=>[v,v==='gto'?'GTO 確切牌面 CERT':v==='exp_ip'?'NL2 鎖頻／IP 英雄 (試驗)':'NL2 鎖頻／OOP 英雄 (試驗)']));
 selectVersion();
}
function selectVersion(){
 subset=all.filter(c=>c.spot===selS.value&&c.version===selV.value);
 if(selFocus.value==='b50')subset=subset.filter(c=>c.nodes.some(mediumCandidate));
 else if(selV.value.startsWith('exp'))subset.sort((a,b)=>(b.hero_gain_vs_locked_pool_bb||0)-(a.hero_gain_vs_locked_pool_bb||0));
 copyOpts(selG,subset.map((c,i)=>[String(i),c.flop+c.turn+' ('+c.flop_line+')｜根 SPR '+fmt(c.turn_spr)+
    (c.version.startsWith('exp')?'｜實驗 EV 差 '+fmt(c.hero_gain_vs_locked_pool_bb)+'bb':'')]));
 selectGame();
}
function selectGame(){
 game=subset[Number(selG.value)]||null;
 const nodes=(game?.nodes||[]).map((n,i)=>({n,i})).filter(({n})=>selFocus.value!=='b50'||mediumCandidate(n));
 copyOpts(selN,nodes.map(({n,i})=>[String(i),n.board+'｜'+n.line+'｜'+(n.acting_seat===0?'OOP':'IP')+'｜SPR '+fmt(n.node_spr)+(mediumCandidate(n)?'｜中尺寸合併下注研究候選':'')]));
 selectNode();
}
const sequential=(g,n)=>pathReach[g.source_sha256]?.nodes?.[[n.board,n.line,n.acting_seat].join("|")];
function selectNode(){
 current=game?.nodes[Number(selN.value)]||null;
 if(!current){by('details').textContent='目前沒有符合的真實 CFR 節點。';by('combos').innerHTML='';return;}
 const n=current,eligible=n.medium_50pct_eligible_combos||0;
 const strict=sequential(game,n);
 const run=String(game.source_run_id),source=/^[0-9]+$/.test(run)
  ? '原始 GitHub Actions：<a href="https://github.com/tetracycline/poker-trainer/actions/runs/'+run+'" target="_blank" rel="noopener">Run '+run+'</a>'
  : '原始解算（不經 GitHub Actions）：<code>'+esc(run)+'</code>';
 const info=[
 '<div><span class="tag '+(game.version==='gto'?'':'exp')+'">'+esc(game.status)+'</span>　<b>'+esc(game.spot)+'・'+esc(game.pot_family)+'・'+esc(game.version)+'</b></div>',
 '<p>精確公牌 <strong>'+esc(n.board)+'</strong>；完整動作線 <strong>'+esc(n.line)+'</strong>；動作玩家 '+(n.acting_seat===0?'OOP':'IP')+'；此節點剩餘 SPR <strong>'+fmt(n.node_spr)+'</strong></p>',
 '<p>可選動作：'+n.actions.map(esc).join('、')+'；CFR 權重加總頻率：'+Object.entries(n.reach_weighted_action_pct).map(([k,v])=>esc(k)+':'+v+'%').join('、')+'</p>',
 (strict?'<p><b>跨街可達手牌 '+fmt(strict.count)+'／'+fmt(n.reachable_combos)+'</b>。已按前街最高頻／近混頻及卡牌衝突篩選；原始 EV 未重解。</p>':
 '<p>此來源只驗證當前節點，未驗證跨街最高頻路徑。</p>'),
 '<p>可達 combos × node：'+fmt(n.reachable_combos)+'；接近混合策略：'+fmt(n.near_mixed_combos)+'；50% pot 中等尺寸符合雙門檻的 combos：<strong>'+fmt(eligible)+'</strong>（只適用本公牌／線／角色）</p>',
 n.b50_relative_equity_mix?'<p>50% pot（中等尺寸）合格組合的相對 equity 構成：低／中／高 = '+n.b50_relative_equity_mix.low_count+'／'+n.b50_relative_equity_mix.middle_count+'／'+n.b50_relative_equity_mix.high_count+'；中段權重 '+fmt(n.b50_relative_equity_mix.middle_eligible_weight_share_pct)+'%。'+(n.b50_relative_equity_mix.nonpolarized_medium_bet_candidate?'<strong>存在去極化／合併下注候選</strong>（精確公牌研究用，未跨牌面證實）。':'無足夠去極化下注證據。')+'</p>':'',
 game.version==='gto'?'':('<p>NL2 實際頻率可匹配對手節點：'+fmt(game.nl2_pool_lock_coverage?.matched_nodes)+'／'+fmt(game.nl2_pool_lock_coverage?.villain_nodes)+'（'+fmt(game.nl2_pool_lock_coverage?.coverage_pct)+'%）。未匹配節點未鎖定；本子局模型化鎖頻的英雄 EV 差值 '+fmt(game.hero_gain_vs_locked_pool_bb)+' bb，<b>不能稱為完整 NL2 池最優策略。</b></p>'),
 game.version==='gto'?'<p>GTO exploitability：'+fmt(game.gto_gap_pct)+'%</p>':
 '<p>對手頻率鎖定試驗：hero gap '+fmt(game.hero_gap_pct)+'%，初始平衡 gap '+fmt(game.gto_gap_pct)+'%；不代表未匹配節點也被鎖定。</p>',
 '<div class="meta">'+source+'；JSON SHA-256 <code>'+esc(game.source_sha256)+'</code></div>'
 ];
 setHtml('details',info.join(''));
 renderCombos();
}
function renderCombos(){
 if(!current||!game)return;
 const n=current,strict=sequential(game,n),hand=game.hands_by_seat[n.acting_seat],raw=atob(strict?.mask??n.eligible_action_masks_b64),best=typeof n.best_ev_action_indices_b64==='string'?atob(n.best_ev_action_indices_b64):null,allrows=[];
 if(raw.length!==hand.length||(best!==null&&best.length!==hand.length)){by('combos').textContent='來源頻率或 EV 資料維度不一致；禁止顯示。';return;}
 for(let i=0;i<raw.length;i++)if(raw.charCodeAt(i)!==0){
   const mask=raw.charCodeAt(i),acts=[];
   for(let j=0;j<n.actions.length;j++)if((mask&(1<<j))!==0)acts.push(n.actions[j]);
   if(acts.length<1||acts.length>2){by('combos').textContent='不符合雙動作可達性規則；禁止顯示。';return;}
   const evIndex=best?.charCodeAt(i);if(best!==null&&(evIndex===255||evIndex>=n.actions.length)){by('combos').textContent='EV 行動證據不完整，禁止顯示。';return;}allrows.push([hand[i],acts.join(' / '),best===null?'未收錄':n.actions[evIndex]]);
 }
 if(strict&&allrows.length!==strict.count){by('combos').textContent='跨街可達性證據不一致，禁止顯示。';return;}
 if(strict&&!allrows.length){by('combos').textContent='依指定可達性規則，這條行動線沒有可達手牌。';return;}
 const displayed=by('showall').checked?allrows:allrows.slice(0,100);
 const fragment=document.createDocumentFragment();
 for(const cells of displayed){const tr=document.createElement('tr');for(const value of cells){const td=document.createElement('td');setText(td,value);tr.appendChild(td);}fragment.appendChild(tr);}
 const box=by('combos');box.innerHTML='';box.appendChild(fragment);
}
for(const [el,cb] of [[selS,selectSpot],[selV,selectVersion],[selG,selectGame],[selN,selectNode],[selFocus,selectVersion],[by('showall'),renderCombos]])el.addEventListener('change',cb);
async function loadIndex(path,zipped=false){
 const r=await fetch(path,{cache:'no-store'});
 if(!r.ok)throw Error('CFR 索引無法載入 (HTTP '+r.status+')');
 const raw=zipped?await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text():await r.text();
 // The immutable legacy index ended with a literal backslash-n. Strip only that known suffix.
 const data=JSON.parse(!zipped&&raw.endsWith('\\n')?raw.slice(0,-2):raw);
 if(data.schema!=='HU_NL2_EXACT_BOARD_CFR_V1'||data.generic_model_upgrades!==0||!Array.isArray(data.subgames)||data.exact_subgame_count!==data.subgames.length)
   throw Error('無效的來源資料 schema');
 return data.subgames;
}
async function loadSource(){
 // Independently source-verified batches 01–03 plus 04; do not count
 // any same-source duplicate from later optional local/offline shards.
 let base;
 try {base=await loadIndex('data/nl2_hu_exact_boards.json.gz',true);}
 catch(error){
   console.warn('Compact CFR archive unavailable; validating the full JSON source',error);
   base=await loadIndex('data/nl2_hu_exact_boards.json',false);
 }
 const extra=await Promise.allSettled([
   loadIndex('data/nl2_hu_exact_boards_b04.json.gz',true),
   loadIndex('data/nl2_hu_exact_boards_b05.json.gz',true)
 ]);
 for(const x of extra)if(x.status==='rejected')
   console.warn('Independent new exact-board source batch not available',x.reason);
 return base.concat(...extra.filter(x=>x.status==='fulfilled').map(x=>x.value));
}
async function loadPathOverlay(path){
 const r=await fetch(path,{cache:'no-store'});
 if(!r.ok)throw Error('跨街可達性索引無法載入');
 const d=await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();
 if(d.schema!=='HU_NL2_SEQUENTIAL_REACH_OVERLAY_V1'||!d.subgames_by_source_sha256)
   throw Error('無效的跨街可達性索引');
 return d.subgames_by_source_sha256;
}
async function loadOffline(){
 const r=await fetch('data/nl2_hu_offline_manifest.json',{cache:'no-store'});
 if(!r.ok)throw Error('離線解算批次索引無法載入');
 const d=await r.json();
 if(d.schema!=='HU_NL2_OFFLINE_SHARDS_V1'||!Array.isArray(d.exact)||!Array.isArray(d.sequential))
   throw Error('無效的離線批次索引');
 const check=(entry,pattern)=>pattern.test(entry?.file)&&Number.isSafeInteger(entry.subgames)&&entry.subgames>0;
 const exactName=/^nl2_hu_exact_boards_b[0-9]+_local[.]json[.]gz$/;
 const pathName=/^nl2_hu_sequential_reach_b[0-9]+(?:_b[0-9]+)?[.]json[.]gz$/;
 if(!d.exact.every(e=>check(e,exactName))||!d.sequential.every(e=>check(e,pathName)))
   throw Error('離線子局檔名或計數有誤');
 const guarded=async(e,loader,count)=>{
  const data=await loader('data/'+e.file);
  if(count(data)!==e.subgames)throw Error('離線子局計數不符');
  return data;
 };
 const [exact,paths]=await Promise.all([
   Promise.allSettled(d.exact.map(e=>guarded(e,f=>loadIndex(f,true),a=>a.length))),
   Promise.allSettled(d.sequential.map(e=>guarded(e,loadPathOverlay,o=>Object.keys(o).length)))
 ]);
 for(const x of paths)if(x.status==='fulfilled')Object.assign(pathReach,x.value);
 return {exact,missingPath:paths.some(x=>x.status==='rejected')};
}
Promise.allSettled([loadSource(),loadOffline()]).then(([base,offline])=>{
 const results=[base,...(offline.status==='fulfilled'?offline.value.exact:[offline])];
 if(results.every(x=>x.status==='rejected'))throw results[0].reason;
 const loaded=results.flatMap(x=>x.status==='fulfilled'?x.value:[]);
 const seen=new Set();
 all=loaded.filter(c=>{
  const key=[c.spot,c.version,c.source_sha256].join(':');
  if(seen.has(key))return false;seen.add(key);return true;
 });
 const counts={};for(const c of all)counts[c.status]=(counts[c.status]||0)+1;
 const candidateNodes=all.reduce((k,c)=>k+c.nodes.filter(mediumCandidate).length,0);
 const msg='已載入 '+all.length+' 個實際公牌多街子局'+(results.some(x=>x.status==='rejected')||offline.value?.missingPath?'（有一批未能載入）':'')+'；50% pot 去極化研究候選節點 '+candidateNodes+'；GTO 精確公牌 CERT：'+(counts['CERT_EXACT_BOARD_GTO']||0)
   +'；對手頻率鎖定試驗：'+(counts['EXPERIMENTAL_POOL_LOCKED']||0)
   +'；392 張通用 MODEL 仍不是 CERT（0/392）。只在同一公牌、同一完整下注歷史及節點 SPR 有效。';
 setText(by('status'),msg);
 const spots=[...new Set(all.map(c=>c.spot))].sort();
 copyOpts(selS,spots.map(spot=>[spot,spot]));
 const url=new URL(location.href);
 const chosen=url.searchParams.get('spot');
 if(chosen&&spots.includes(chosen))selS.value=chosen;
 selectSpot();
 const version=url.searchParams.get('version');
 if(version&&[...selV.options].some(o=>o.value===version)){
   selV.value=version;selectVersion();
 }
 const sha=url.searchParams.get('sha');
 if(sha){
   const target=subset.findIndex(c=>c.source_sha256===sha);
   if(target>=0){selG.value=String(target);selectGame();}
 }
}).catch(e=>setText(by('status'),'真實 CFR 索引不可用：'+e.message));
})();