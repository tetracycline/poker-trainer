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
 game.version==='gto'?'<p>GTO exploitability：'+fmt(game.gto_gap_pct)+'%</p>':
 '<p>對手頻率鎖定試驗：hero gap '+fmt(game.hero_gap_pct)+'%，初始平衡 gap '+fmt(game.gto_gap_pct)+'%；不代表未匹配節點也被鎖定。</p>',
 '<div class="meta">原始 GitHub Actions：<a href="https://github.com/tetracycline/poker-trainer/actions/runs/'+Number(game.source_run_id)+'" target="_blank" rel="noopener">Run '+Number(game.source_run_id)+'</a>；JSON SHA-256 <code>'+esc(game.source_sha256)+'</code></div>'
 ];
 setHtml('details',info.join(''));
 renderCombos();
}
function renderCombos(){
 if(!current||!game)return;
 const n=current,hand=game.hands_by_seat[n.acting_seat],raw=atob(n.eligible_action_masks_b64),allrows=[];
 if(raw.length!==hand.length){by('combos').textContent='來源資料維度不一致；禁止顯示。';return;}
 for(let i=0;i<raw.length;i++)if(raw.charCodeAt(i)!==0){
   const mask=raw.charCodeAt(i),acts=[];
   for(let j=0;j<n.actions.length;j++)if((mask&(1<<j))!==0)acts.push(n.actions[j]);
   if(acts.length<1||acts.length>2){by('combos').textContent='不符合雙動作可達性規則；禁止顯示。';return;}
   allrows.push([hand[i],acts.join(' / ')]);
 }
 const displayed=by('showall').checked?allrows:allrows.slice(0,100);
 const fragment=document.createDocumentFragment();
 for(const cells of displayed){const tr=document.createElement('tr');for(const value of cells){const td=document.createElement('td');setText(td,value);tr.appendChild(td);}fragment.appendChild(tr);}
 const box=by('combos');box.innerHTML='';box.appendChild(fragment);
}
for(const [el,cb] of [[selS,selectSpot],[selV,selectVersion],[selG,selectGame],[selN,selectNode],[by('showall'),renderCombos]])el.addEventListener('change',cb);
fetch('data/nl2_hu_exact_boards.json',{cache:'no-store'}).then(r=>{
 if(!r.ok)throw Error('真實 CFR 索引尚未由通過驗證的工作流程發布 (HTTP '+r.status+')');return r.json();
}).then(d=>{
 if(d.schema!=='HU_NL2_EXACT_BOARD_CFR_V1'||!Array.isArray(d.subgames))throw Error('無效的來源資料 schema');
 all=d.subgames;const counts={};for(const c of all)counts[c.status]=(counts[c.status]||0)+1;
 setText(by('status'),'已驗證 '+all.length+' 個精確牌面多街子局。泛化 MODEL 升級：'+d.generic_model_upgrades+'。'+JSON.stringify(counts)+'；本頁逐 combo 可達性來自真實 CFR，而非 100bb 假設策略。');
 const spots=[...new Set(all.map(c=>c.spot))].sort();copyOpts(selS,spots.map(s=>[s,s]));selectSpot();
}).catch(e=>setText(by('status'),'尚無可公開的獨立驗證 CFR 資料：'+e.message));
})();