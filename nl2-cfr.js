(()=>{'use strict';
const by=id=>document.getElementById(id);
const fmt=x=>x==null?'—':typeof x==='number'?x.toLocaleString('en-US',{maximumFractionDigits:4}):String(x);
const setText=(el,s)=>{el.textContent=s;return el;};
const option=(list,k,label)=>{const op=document.createElement('option');op.value=k;op.textContent=label;list.appendChild(op);};
let all=[],subset=[],game=null,current=null;
const selS=by('spot'),selV=by('ver'),selG=by('game'),selN=by('node');
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
 copyOpts(selG,subset.map((c,i)=>[String(i),c.flop+c.turn+' ('+c.flop_line+')｜根 SPR '+fmt(c.turn_spr)]));
 selectGame();
}
function selectGame(){
 game=subset[Number(selG.value)]||null;
 const nodes=game?.nodes||[];
 copyOpts(selN,nodes.map((n,i)=>[String(i),n.board+'｜'+n.line+'｜'+(n.acting_seat===0?'OOP':'IP')+'｜SPR '+fmt(n.node_spr)]));
 selectNode();
}
function selectNode(){
 current=game?.nodes[Number(selN.value)]||null;
 if(!current){by('details').textContent='目前沒有符合的真實 CFR 節點。';by('combos').innerHTML='';return;}
 const n=current,eligible=n.medium_50pct_eligible_combos||0;
 const info=[
 '<div><span class="tag '+(game.version==='gto'?'':'exp')+'">'+esc(game.status)+'</span>　<b>'+esc(game.spot)+'・'+esc(game.pot_family)+'・'+esc(game.version)+'</b></div>',
 '<p>精確公牌 <strong>'+esc(n.board)+'</strong>；完整動作線 <strong>'+esc(n.line)+'</strong>；動作玩家 '+(n.acting_seat===0?'OOP':'IP')+'；此節點剩餘 SPR <strong>'+fmt(n.node_spr)+'</strong></p>',
 '<p>可選動作：'+n.actions.map(esc).join('、')+'；CFR 權重加總頻率：'+Object.entries(n.reach_weighted_action_pct).map(([k,v])=>esc(k)+':'+v+'%').join('、')+'</p>',
 '<p>可達 combos × node：'+fmt(n.reachable_combos)+'；接近混合策略：'+fmt(n.near_mixed_combos)+'；50% pot 中等尺寸符合雙門檻的 combos：<strong>'+fmt(eligible)+'</strong>（只適用本公牌／線／角色）</p>',
 n.b50_relative_equity_mix?'<p>50% pot（中等尺寸）合格組合的相對 equity 構成：低／中／高 = '+n.b50_relative_equity_mix.low_count+'／'+n.b50_relative_equity_mix.middle_count+'／'+n.b50_relative_equity_mix.high_count+'；中段權重 '+fmt(n.b50_relative_equity_mix.middle_eligible_weight_share_pct)+'%。'+(n.b50_relative_equity_mix.nonpolarized_medium_bet_candidate?'<strong>存在去極化／合併下注候選</strong>（精確公牌研究用，未跨牌面證實）。':'無足夠去極化下注證據。')+'</p>':'',
 game.version==='gto'?'':('<p>NL2 實際頻率可匹配對手節點：'+fmt(game.nl2_pool_lock_coverage?.matched_nodes)+'／'+fmt(game.nl2_pool_lock_coverage?.villain_nodes)+'（'+fmt(game.nl2_pool_lock_coverage?.coverage_pct)+'%）。未匹配節點未鎖定；本子局模型化鎖頻的英雄 EV 差值 '+fmt(game.hero_gain_vs_locked_pool_bb)+' bb，<b>不能稱為完整 NL2 池最優策略。</b></p>'),
 game.version==='gto'?'<p>GTO exploitability：'+fmt(game.gto_gap_pct)+'%</p>':
 '<p>對手頻率鎖定試驗：hero gap '+fmt(game.hero_gap_pct)+'%，初始平衡 gap '+fmt(game.gto_gap_pct)+'%；不代表未匹配節點也被鎖定。</p>',
 '<div class="meta">原始 GitHub Actions：<a href="https://github.com/tetracycline/poker-trainer/actions/runs/'+Number(game.source_run_id)+'" target="_blank" rel="noopener">Run '+Number(game.source_run_id)+'</a>；JSON SHA-256 <code>'+esc(game.source_sha256)+'</code></div>'
 ];
 setHtml('details',info.join(''));
 renderCombos();
}
function renderCombos(){
 if(!current||!game)return;
 const n=current,hand=game.hands_by_seat[n.acting_seat],raw=atob(n.eligible_action_masks_b64),best=typeof n.best_ev_action_indices_b64==='string'?atob(n.best_ev_action_indices_b64):null,allrows=[];
 if(raw.length!==hand.length||(best!==null&&best.length!==hand.length)){by('combos').textContent='來源頻率或 EV 資料維度不一致；禁止顯示。';return;}
 for(let i=0;i<raw.length;i++)if(raw.charCodeAt(i)!==0){
   const mask=raw.charCodeAt(i),acts=[];
   for(let j=0;j<n.actions.length;j++)if((mask&(1<<j))!==0)acts.push(n.actions[j]);
   if(acts.length<1||acts.length>2){by('combos').textContent='不符合雙動作可達性規則；禁止顯示。';return;}
   const evIndex=best?.charCodeAt(i);if(best!==null&&(evIndex===255||evIndex>=n.actions.length)){by('combos').textContent='EV 行動證據不完整，禁止顯示。';return;}allrows.push([hand[i],acts.join(' / '),best===null?'未收錄':n.actions[evIndex]]);
 }
 const displayed=by('showall').checked?allrows:allrows.slice(0,100);
 const fragment=document.createDocumentFragment();
 for(const cells of displayed){const tr=document.createElement('tr');for(const value of cells){const td=document.createElement('td');setText(td,value);tr.appendChild(td);}fragment.appendChild(tr);}
 const box=by('combos');box.innerHTML='';box.appendChild(fragment);
}
for(const [el,cb] of [[selS,selectSpot],[selV,selectVersion],[selG,selectGame],[selN,selectNode],[by('showall'),renderCombos]])el.addEventListener('change',cb);
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
 // Prefer the independently hashed, deterministic compact 347-case archive.
 // Do not load the old 266-case file plus the 81-case extension twice.
 try {return await loadIndex('data/nl2_hu_exact_boards.json.gz',true);}
 catch(error){
   console.warn('Compact CFR archive unavailable; validating the full JSON source',error);
   return await loadIndex('data/nl2_hu_exact_boards.json',false);
 }
}
loadSource().then(loaded=>{
 const seen=new Set();
 all=loaded.filter(c=>{
  const key=[c.spot,c.version,c.source_sha256].join(':');
  if(seen.has(key))return false;seen.add(key);return true;
 });
 const counts={};for(const c of all)counts[c.status]=(counts[c.status]||0)+1;
 const msg='已載入 '+all.length+' 個實際公牌多街子局；GTO 精確公牌 CERT：'+(counts['CERT_EXACT_BOARD_GTO']||0)
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