(()=>{'use strict';
const el=id=>document.getElementById(id);
const text=(id,value)=>{el(id).textContent=String(value??'—');};
const fmt=(x,places=3)=>x!==null&&x!==undefined&&x!==''&&Number.isFinite(Number(x))?Number(x).toLocaleString('zh-TW',{maximumFractionDigits:places}):'—';
const opt=(parent,value,label)=>{const x=document.createElement('option');x.value=value;x.textContent=label;parent.appendChild(x);};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let status=null,models=[],chosenModel=null,chosenBoard=null,caseData=null,proofCache={};
const choices=['model','board','version','node'];
const q=new URLSearchParams(location.search);
const setMessage=s=>{el('details').textContent=s;el('combo-rows').replaceChildren();};
function sourceUrl(run){return 'https://github.com/tetracycline/poker-trainer/actions/runs/'+run;}
function sourceRun(source){return source?.source_run_id??source?.run_id??null;}
function sourceSha(source){return source?.source_sha256??source?.sha256??null;}
function nodeCount(v,field){const n=v?.[field];return Number.isInteger(n)&&n>=0?String(n):'未記錄';}
function buildLinks(caseInfo,actual){
 const base=sourceUrl(sourceRun(caseInfo));
 const src=document.createElement('a');src.href=base;src.target='_blank';src.rel='noopener';
 src.textContent='原始 GitHub Actions run '+sourceRun(caseInfo);
 return src;
}
function selectedModel(){
 chosenModel=models[Number(el('model').value)]||null;
 el('board').replaceChildren();
 if(!chosenModel){setMessage('尚無任何滿足三至五張不同代表翻牌的來源。');return;}
 chosenModel.certified_3_to_5_exact_flop_boards.forEach((b,i)=>{
   opt(el('board'),String(i),b.public_board+' / '+b.actual_exact_action_line+
     '｜SPR '+fmt(b.actual_spr)+'｜'+b.flop_texture);
 });
 if(q.has('board')){
   const i=chosenModel.certified_3_to_5_exact_flop_boards.findIndex(b=>b.public_board===q.get('board'));
   if(i>=0)el('board').value=String(i);
 }
 selectBoard();
}
function selectBoard(){
 chosenBoard=chosenModel?.certified_3_to_5_exact_flop_boards[Number(el('board').value)]||null;
 el('version').replaceChildren();
 opt(el('version'),'gto','本公牌 GTO CERT');
 if(chosenBoard)chosenBoard.nl2_locked_variants.forEach((b,i)=>{
   opt(el('version'),b.version+'@'+i,b.version+'｜Run '+b.run_id+
     '｜觀測聚合節點 '+nodeCount(b,'observed_marginal_source_nodes')+
     '／假設 '+nodeCount(b,'assumed_default_source_nodes')+
     '（局部 NL2 lock，非 GTO）');
 });
 if(q.has('version')){
   const requested=q.get('version');
   const versions=[...el('version').options];
   const selected=versions.find(x=>x.value===requested)||
      versions.find(x=>x.value.startsWith(requested+'@'));
   if(selected)el('version').value=selected.value;
 }
 selectVersion();
}
function sourceCase(version){
 if(!chosenBoard)return null;
 if(version==='gto')return {
   source_run_id:chosenBoard.source_run_id,
   source_sha256:chosenBoard.source_sha256,
   version:'gto',status:'CERT_EXACT_BOARD_GTO'};
 const [kind,index]=String(version).split('@');
 const numeric=(index!==undefined&&/^\d+$/.test(index))?Number(index):-1;
 if(numeric>=0){
   const candidate=chosenBoard.nl2_locked_variants[numeric];
   return candidate?.version===kind?candidate:null;
 }
 return chosenBoard.nl2_locked_variants.find(v=>v.version===kind)||null;
}
async function getProof(run){
 const batch=Object.entries(status.independently_verified_completed_batches||{})
     .find(([name,v])=>v?.run_id===run&&v?.status==='VERIFIED');
 if(!batch)return null;
 const code=batch[0];
 if(proofCache[code])return proofCache[code];
 const path='data/solver_evidence/NL2_MULTIBOARD_'+code+'.json.gz';
 const resp=await fetch(path,{cache:'no-store'});
 if(!resp.ok)throw Error('來源 '+path+' HTTP '+resp.status);
 if(typeof DecompressionStream==='undefined')throw Error('瀏覽器缺少 gzip 檢視支援');
 const blob=new Response(resp.body.pipeThrough(new DecompressionStream('gzip')));
 const raw=await blob.json();
 if(raw.schema!=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'||raw.errors?.length||
    raw.source_run_id!==run||raw.no_generic_texture_certification!==true)
    throw Error('原始 GitHub CFR 來源驗證不一致');
 proofCache[code]=raw;
 return raw;
}
function verifiedCase(source,proof){
 if(!proof)return null;
 const records=proof.artifacts.flatMap(x=>x.cases);
 const digest=sourceSha(source);
 if(!digest||!sourceRun(source))throw Error('來源缺少完整 run id／SHA-256');
 const item=records.find(x=>x.source_sha256===digest &&
    x.spot===chosenModel.solver_profile&&x.pot_family===chosenModel.family);
 if(!item)throw Error('真實 CFR ZIP 缺指定 SHA／位置／底池來源');
 if(item.flop!==chosenBoard.flop||item.turn!==chosenBoard.turn||
    item.flop_line!==chosenBoard.exact_flop_action)
    throw Error('試算來源具體公牌／行動歷史不符');
 return item;
}
async function selectVersion(){
 caseData=null;el('node').replaceChildren();
 const version=el('version').value;const source=sourceCase(version);
 if(!source){setMessage('尚無符合的 source');return;}
 const run=sourceRun(source),digest=sourceSha(source);
 const hasVerifiedBatch=Object.values(status?.independently_verified_completed_batches||{})
    .some(x=>x?.status==='VERIFIED'&&x.run_id===run);
 if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){
   const link=document.createElement('a');
   link.href='nl2-cfr.html?spot='+encodeURIComponent(chosenModel.solver_profile)
      +'&version='+encodeURIComponent(source.version||version)+'&sha='+encodeURIComponent(digest)
      +'&board='+encodeURIComponent(chosenBoard.public_board)
      +'&line='+encodeURIComponent(chosenBoard.actual_exact_action_line);
   link.textContent='開啟已驗證的原始 644 子局逐 combo GTO/EXP 查閱頁（Run '+source.source_run_id+'）';
   el('details').replaceChildren(link);
   el('combo-rows').replaceChildren();
   return;
 }
 const url=sourceUrl(run);
 setMessage('正在檢查真正的 GitHub Rust CFR run '+run+' 與來源 SHA……');
 try{
   const proof=await getProof(run);
   if(!proof){setMessage('來源未由獨立 GitHub Actions 驗證；不可將本頁標示為 CERT。'+url);return;}
   const actual=verifiedCase(source,proof);
   caseData=actual;
   const options=actual.nodes.map((n,i)=>({n,i}))
     .filter(({n})=>n.strictly_reachable_combos>0);
   options.forEach(({n,i})=>opt(el('node'),String(i),
      n.public_board+'｜'+n.exact_node_line+'｜'+(n.acting_seat===0?'OOP':'IP')+
      '｜SPR '+fmt(n.node_spr)));
   const chosen=actual.nodes.findIndex(n=>n.public_board===chosenBoard.public_board &&
     n.exact_node_line===chosenBoard.actual_exact_action_line &&
     n.acting_seat===chosenBoard.acting_seat);
   if(chosen>=0)el('node').value=String(chosen);
   selectNode();
 }catch(e){setMessage('來源稽核錯誤：'+e.message);}
}
function selectNode(){
 if(!caseData)return;
 const node=caseData.nodes[Number(el('node').value)];
 if(!node){setMessage('該真實牌面沒有可達的 solver 決策。');return;}
 const version=el('version').value;
 const cands=node.medium_50pct_strict_evidence||{};
 const lock=caseData.villain_lock_scope||{};
 const origin=sourceCase(version);
 const details=el('details');details.replaceChildren();
 const currentSourceType=chosenBoard.assumed_preflop_ranges?
     'LMP／ISO 假設 169 起手牌類型；如為 50% 單尺寸限制樹，僅是該樹的條件均衡，非完整 NL2 GTO':
     '釘定翻前範圍 CFR；僅此具名公牌及決策歷史通過來源認證';
 const selectedLock=version==='gto'?'本頁為 GTO 基線，沒有套用 NL2 對手鎖頻':
   '本來源為 NL2 部分 node-lock；'+
   '實測聚合來源節點 '+nodeCount(origin,'observed_marginal_source_nodes')+
   '、假設補值 '+nodeCount(origin,'assumed_default_source_nodes')+
   '、未鎖定 '+nodeCount(origin,'unlocked_source_nodes')+
   '；來源範圍 '+String(origin?.source_scope||'未記錄')+
   '。聚合頻率不是該牌面／私有手牌的實測條件頻率。';
 const lines=[
 '具體公牌：'+node.public_board+'；完整動作線 '+node.exact_node_line,
 '認證範圍：'+currentSourceType,
 selectedLock,
 '嚴格可達 combo '+chosenBoard.strict_full_street_combo_reachable+
   '；GTO／鎖頻來源各自 SHA 為 '+chosenBoard.source_sha256+'／'+sourceSha(origin),
 '座位 '+(node.acting_seat?'IP':'OOP')+'；底池 '+fmt(node.pot_bb)+' bb；剩餘有效籌碼 '+fmt(node.remaining_bb)+' bb；SPR '+fmt(node.node_spr),
 'GTO 基線 exploitability：'+fmt(caseData.gto_exploitability_pct)+'%；NL2 模型 hero gap：'+fmt(caseData.locked_hero_gap_pct)+'%',
 '真正跨街可達 combos：'+fmt(node.strictly_reachable_combos,0)+'；合法動作：'+node.source_actions.join('、'),
 '各動作原始來源加權頻率：'+Object.entries(node.action_frequency_weighted_pct||{}).map(([k,v])=>k+' '+fmt(v)+'%').join('；'),
 '50% pot：可達 combos '+(cands.eligible||0)+'；其中 EV 最高動作為 50%：'+(cands.preferred||0)+
   '；中 equity '+(cands.middle_count||0)+' / 低 '+(cands.low_count||0)+' / 高 '+(cands.high_count||0)+
   '；'+(cands.candidate?'僅列去極化研究候選':'沒有足夠非極化證據，不作建議'),
 '對手來源匹配節點 '+fmt(lock.pattern_matched_nodes,0)+'/'+fmt(lock.villain_decision_nodes,0)+
 '；真實 NL2 聚合統計來源 '+fmt(lock.observed_marginal_source_nodes,0)+
 '；以假設補值 '+fmt(lock.imputed_assumption_nodes,0)+
 '；尚未匹配 '+fmt(lock.unmatched_nodes,0)+
 '。這些不是每個 NL2 私有手牌的實測頻率。',
 '來源 SHA-256：'+caseData.source_sha256
 ];
 for(const line of lines){const p=document.createElement('p');p.textContent=line;details.appendChild(p);}
 details.appendChild(buildLinks(origin,caseData));
 fillCombos();
}
function fillCombos(){
 const box=el('combo-rows');box.replaceChildren();
 if(!caseData)return;
 const node=caseData.nodes[Number(el('node').value)];if(!node)return;
 const hands=caseData.hands_by_seat?.[node.acting_seat];
 if(!Array.isArray(hands)){
   const tr=document.createElement('tr');const td=document.createElement('td');
   td.textContent='缺少 Hole cards 的原始順序，不顯示可能誤對應的手牌策略。';
   td.colSpan=3;tr.appendChild(td);box.appendChild(tr);return;
 }
 const masks=atob(node.strictly_reachable_masks_b64);
 const best=node.strict_legal_best_ev_action_indices_b64?atob(node.strict_legal_best_ev_action_indices_b64):null;
 if(masks.length!==hands.length||(best!==null&&best.length!==hands.length)){
   box.textContent='原始 combo/EV 維度不相同，無法安全展示。';return;
 }
 const eligible=[];
 for(let i=0;i<hands.length;i++){
   const mask=masks.charCodeAt(i);
   if(!mask)continue;
   const actions=node.source_actions.filter((_,j)=>mask&(1<<j));
   if(actions.length<1||actions.length>2){
     box.textContent='逐 combo 的 GTO 行動雙分支門檻驗證失敗';return;
   }
   const index=best?.charCodeAt(i);
   if(best&&(index===255||index>=node.source_actions.length)){
     box.textContent='最大 EV 行動來源不相容';return;
   }
   eligible.push([hands[i],actions.join(' / '),best?node.source_actions[index]:'原始未收錄']);
 }
 if(eligible.length!==node.strictly_reachable_combos){
   box.textContent='本條行動線超出原始嚴格可達手牌數，禁止顯示';return;
 }
 const show=el('all-combos').checked?eligible:eligible.slice(0,100);
 const frag=document.createDocumentFragment();
 for(const cols of show){
   const tr=document.createElement('tr');
   for(const v of cols){const td=document.createElement('td');td.textContent=v;tr.appendChild(td);}
   frag.appendChild(tr);
 }
 box.appendChild(frag);
}
el('model').addEventListener('change',selectedModel);
el('board').addEventListener('change',selectBoard);
el('version').addEventListener('change',selectVersion);
el('node').addEventListener('change',selectNode);
el('all-combos').addEventListener('change',fillCombos);
function fetchCertifiedRegistry(){
 const open=r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();};
 const v6=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33'||
      d.CERT_MULTIBOARD!==42||d.APPROX!==350||d.TOTAL!==392||
      d.original_v5_cert!==41||d.original_v5_approx!==351||
      d.original_top24_cutoff_unchanged!==true||d.added_cert_rank!==33||
      d.added_cert_model_id!=='ln-opfr-t_model-1ocorr7'||
      String(d.source_blind_expansion_ranks)!=='33'||Object.keys(d.records||{}).length!==392)
      throw Error('V6 rank33 exact-board certificate missing');
   return d;
 };
 const v5=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55'||
      d.CERT_MULTIBOARD!==41||d.APPROX!==351||d.TOTAL!==392||
      d.original_v4_cert!==33||d.original_v4_approx!==359||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='42,44,49,50,51,53,54,55'||
      d.supplementary_cert_count!==17||Object.keys(d.records||{}).length!==392)
      throw Error('V5 authentic multi-board ledger invalid');
   return d;
 };
 const v4=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50'||
      d.CERT_MULTIBOARD!==33||d.APPROX!==359||d.TOTAL!==392||
      d.original_v3_cert!==27||d.original_v3_approx!==365||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='31,34,36,37,38,39'||
      d.supplementary_cert_count!==9||
      Object.keys(d.records||{}).length!==392)
      throw Error('V4 exact-source CERT ledger failed guard');
   return d;
 };
 const v3=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28'||
      d.CERT_MULTIBOARD!==27||d.APPROX!==365||d.TOTAL!==392||
      d.original_v2_cert!==26||d.original_v2_approx!==366||
      d.original_top24_cutoff_unchanged!==true||
      d.added_cert_rank!==28||d.added_cert_model_id!=='ln-iso-lmp_r_model-1siq45p'||
      String(d.source_blind_next6_prereg_ranks)!=='27,28,29,30,31,32'||
      Object.keys(d.records||{}).length!==392)
      throw Error('V3 rank28 source ledger failed guard');
   return d;
 };
 const v2=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE'||
      d.CERT_MULTIBOARD!==26||d.APPROX!==366||d.TOTAL!==392||
      d.original_top24_cert!==24||d.original_top24_approx!==368||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_tie_ranks)!=='25,26'||
      Object.keys(d.records||{}).length!==392)
      throw Error('V2 tied-score source ledger failed guard');
   return d;
 };
 return fetch('data/nl2_hu_multiboard_status_v6_rank33.json',{cache:'no-store'}).then(open).then(v6)
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v5_batch55.json',{cache:'no-store'}).then(open).then(v5))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v4_batch50.json',{cache:'no-store'}).then(open).then(v4))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v3_rank28.json',{cache:'no-store'}).then(open).then(v3))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v2_tie.json',{cache:'no-store'}).then(open).then(v2))
   .catch(()=>fetch('data/nl2_hu_multiboard_status.json',{cache:'no-store'}).then(open)
     .then(d=>{
       if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V1'||
          d.CERT_MULTIBOARD!==24||d.APPROX!==368||d.TOTAL!==392||
          Object.keys(d.records||{}).length!==392)throw Error('V1 source ledger invalid');
       return d;
     }));
}

fetchCertifiedRegistry()
 .then(d=>{
   if(!['NL2_HU_392_MULTIBOARD_CERT_STATUS_V1','NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE','NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28','NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50','NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55','NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33'].includes(d.schema)||d.CERT_MULTIBOARD+d.APPROX!==392)
      throw Error('模型認證來源驗證失敗');
   status=d;
   models=Object.values(d.records).filter(x=>x.label==='CERT-MULTIBOARD')
      .sort((a,b)=>a.frequency_rank-b.frequency_rank);
   el('model').replaceChildren();
   models.forEach((x,i)=>opt(el('model'),String(i),'#'+x.frequency_rank+' '+x.solver_profile+' '+x.model_id));
   text('summary','CERT-MULTIBOARD '+d.CERT_MULTIBOARD+'／392；APPROX '+d.APPROX+
        '／392。原始頻率優先前'+d.top_N_rank_cutoff+
        '格'+(d.supplementary_cert_count?'；另有經事前登記的補充認證 '+d.supplementary_cert_count+' 格':'')+
        '；CERT 僅限下方 3–5 張具名牌面，其他 '+d.APPROX+' 個模型仍為 APPROX。');
   const id=q.get('model');
   const i=id?models.findIndex(x=>x.model_id===id):-1;
   if(i>=0)el('model').value=String(i);
   selectedModel();
 }).catch(e=>{text('summary','來源無法驗證：'+e.message);setMessage('沒有可安全展示的真實多牌面 CERT。')});
})();