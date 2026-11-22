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
 let batch=Object.entries(status.independently_verified_completed_batches||{})
     .find(([name,v])=>v?.run_id===run&&v?.status==='VERIFIED');
 if(!batch){
   const rank96=status?.B364_rank96_three_true_original_GTO_NL2_OOP_flops?.genuine_sources
     ?.find(x=>x.run_id===run);
   if(rank96)batch=[`B${rank96.pin.batch}_R96_VERIFIED`,{run_id:run,status:'VERIFIED'}];
 }
 if(!batch && chosenModel?.model_id==='ln-ipfr-r_model-ujl14x' &&
    ['NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'].includes(status?.schema)){
   const verifiedOriginalRuns={
     45017142943:'B392_R107_B374',
     45023132316:'B392_R107_B387',
     45025076333:'B392_R107_B388'
   };
   const code=verifiedOriginalRuns[run];
   if(code)batch=[code,{run_id:run,status:'VERIFIED'}];
 }
 if(!batch && ['ln-ipfr-r_model-1t7q0mn','ln-ipfr-r_model-kp19if'].includes(chosenModel?.model_id) &&
   status?.schema==='NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'){
   const verifiedOriginalRuns={45026396521:'B414_COBB_B393',45027557999:'B414_COBB_B396'};
   const code=verifiedOriginalRuns[run];
   if(code)batch=[code,{run_id:run,status:'VERIFIED'}];
 }
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
 if(chosenModel?.model_id==='ln-opfr-t_model-1hmsxaw'&&version!=='gto'&&
    Object.values(status?.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.real_NL2_actor_OOP_lock_runs||{})
      .includes(run)&&sourceSha(source)?.length===64){
   setMessage('此具名牌面的真正 Rust NL2 轉牌／河牌局部鎖頻已由獨立 GitHub Actions 與來源 SHA 驗證；尚非逐私牌實測頻率，也不是整類牌面的 GTO。此檢視器不把部分鎖頻 raw Rust 檔案冒充原始 GTO proof 包。');
   const link=document.createElement('a');
   link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
   link.textContent='查看真實 NL2 部分 node-lock GitHub Actions Run '+run;
   el('details').appendChild(link);el('combo-rows').replaceChildren();return;
 }
 if(chosenModel?.model_id==='ln-iso-lmp_r_model-wpg493'&&
    chosenBoard?.flop==='6s5h3d'&&chosenBoard?.turn==='Qs'&&
    chosenBoard?.actual_exact_action_line==='b75 r c/x b50 c/x'&&
    ((version==='gto'&&run===44901784001)||
     (version!=='gto'&&run===44903333583))&&
    sourceSha(source)?.length===64){
   setMessage(version==='gto'
     ?'此具名牌面原始 100bb Rust GTO 已經來源 SHA/座位/前街合法 combo 驗證；其 LMP 169 類翻前範圍是假設，非觀測到的私有手牌。原始證據詳見 GitHub Actions；不將 EXP source 當 GTO。'
     :'此具名牌面是真實 Rust NL2 部分 node-lock（限後續轉河牌），觀測的 NL2 來源僅為街別/下注尺寸玩家池聚合；未知及預設頻率未視為實測逐私牌條件。');
   const link=document.createElement('a');
   link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
   link.textContent='檢視本具名公牌的真實 GTO／NL2 source GitHub Actions Run '+run;
   el('details').appendChild(link);
   el('combo-rows').replaceChildren();return;
 }
  if(chosenModel?.model_id==='ln-ipfr-t_model-qpx6tn'&&
     chosenBoard?.actual_exact_action_line==='x b100 c/x'&&
     sourceSha(source)?.length===64){
   const z=status?.B271_rank61_three_authentic_GTO_NL2_CO_IP_flops?.
     original_GTO_and_NL2_actor_locked_source_pins?.find(x=>
       x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);
   if(z&&((version==='gto'&&run===z.original_GTO_run)||
          (version!=='gto'&&run===z.source_lock_run))){
     setMessage(version==='gto'
       ?'這是固定翻前 CFR 的真實 100bb Rust GTO 具名公牌；僅限此動作歷史、actor、SPR，非逐私牌實測 NL2 策略。來源 SHA 與嚴格前街 reach 在 GitHub Actions 可核。'
       :'此來源是真實 Rust 後續轉河牌 NL2 局部 node-lock，與 GTO 分開求解。NL2 玩家池只具備街別／尺寸邊際統計，來源分母未知不等於零、不得稱為逐私牌實測。');
     const link=document.createElement('a');
     link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
     link.textContent='檢視精確具名公牌的原始 GitHub Actions Run '+run;
     el('details').appendChild(link);el('combo-rows').replaceChildren();return;
   }
 }
  if(chosenModel?.model_id==='ln-iso-lmp_t_model-17z0wyl'&&
    chosenBoard?.actual_exact_action_line==='x b50 c/x'&&
    sourceSha(source)?.length===64){
    const v=status?.B289_rank46_three_true_GTO_NL2_CO_IP_flops?.
       GTO_and_NL2_source_shas?.find(x=>
         x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);
    if(v&&((version==='gto'&&run===v.GTO_run)||
          (version!=='gto'&&run===v.NL2_run))){
      setMessage(version==='gto'
        ?'此精確公牌為原生 100bb Rust GTO，CO-IP 座位與 x b50 c/x 前街完整可達性經 SHA 驗證；LMP 169 類翻前範圍是假設，非實際逐私牌 NL2 觀測。'
        :'此公牌為真正 Rust NL2 部分轉河牌鎖頻證據，玩家池實測只限街別與下注尺寸邊際；未知來源分母不等於零或逐私牌實測。');
      const l=document.createElement('a');
      l.href=sourceUrl(run);l.rel='noopener';l.target='_blank';
      l.textContent='檢視精確公牌的 GTO 或 NL2 原生 Rust Actions Run '+run;
      el('details').appendChild(l);el('combo-rows').replaceChildren();return;
    }
 }
  if(chosenModel?.model_id==='ln-ipfr-t_model-hxdit'&&
    chosenBoard?.actual_exact_action_line==='x b50 c/x'&&
    sourceSha(source)?.length===64){
    const extra=status?.B331_rank60_four_true_GTO_NL2_actor_lock_boards?.fourth_original_GTO_and_NL2_source;
    const proof=status?.B319_rank60_three_true_GTO_NL2_CO_IP_flops?.
      GTO_and_NL2_source_shas?.find(x=>
        x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn)||
       (extra?.flop===chosenBoard?.flop&&extra?.turn===chosenBoard?.turn?
        {GTO_run:extra.original_GTO_run,NL2_run:extra.true_partial_Rust_NL2_run}:null);
    if(proof&&((version==='gto'&&run===proof.GTO_run)||
              (version!=='gto'&&run===proof.NL2_run))){
      setMessage(version==='gto'
        ?'此精確牌面為原生 100bb CO-IP Rust GTO，x b50 c/x 前街與逐 combo 40%/70% 可達性均經 SHA 驗證；不可類推至其他牌面。'
        :'此精確牌面另有真正 Rust NL2 局部轉牌及河牌鎖頻來源；實測玩家池資料只限街別與下注尺寸邊際，並非逐私牌條件頻率。');
      const link=document.createElement('a');
      link.href=sourceUrl(run);link.rel='noopener';link.target='_blank';
      link.textContent='檢視此精確牌面的 GTO／NL2 原始 Actions Run '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
    }
 }
  if(chosenModel?.model_id==='ln-iso-lmp_r_model-vlgh2t'&&
     chosenBoard?.actual_exact_action_line==='b50 c/x b50 c/'&&
     sourceSha(source)?.length===64){
    const origin=status?.B345_rank71_true_3_flop_GTO_NL2_OOP_evidence?.
      original_archive_provenance?.find(x=>x.flop===chosenBoard.flop&&x.turn===chosenBoard.turn);
    if(origin&&run===origin.original_GTO_run&&
       ((version==='gto'&&digest===origin.original_gto_case_sha256)||
        (version!=='gto'&&digest===origin.real_NL2_actor_partial_case_sha256))){
      setMessage(version==='gto'
       ?'此具名公牌為原始 100bb 50%-only 限定下注樹真實 Rust GTO，嚴格 40%／70% 前街合法且 BB-OOP SPR 相符；非不限尺寸的 GTO。'
       :'此具名公牌有獨立 Rust 局部 NL2 BB-OOP 鎖頻來源，僅街別與下注尺寸玩家池邊際頻率；不是逐私牌條件式實測資料。');
      const link=document.createElement('a');
      link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
      link.textContent='檢視此 GTO／NL2 具名牌面原始 Rust Actions Run '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
    }
  }
 if(chosenModel?.model_id==='ln-ipc-t_model-1cla93g'&&
    chosenBoard?.actual_exact_action_line==='b50 c/x'&&sourceSha(source)?.length===64){
   const p=status?.B354_rank79_three_true_original_GTO_NL2_CO_IP_flops?.
      source_run_shas?.find(x=>x.flop===chosenBoard.flop&&x.turn===chosenBoard.turn);
   if(p&&run===p.run&&((version==='gto'&&digest===p.GTO_SHA)||
      (version!=='gto'&&digest===p.NL2_SHA))){
      setMessage(version==='gto'
       ?'此具名公牌有原始 100bb UTGCO Rust GTO，CO-IP b50 c/x 嚴格前街 40%／70% 及 SPR 已查核；不能推廣到其他牌面。'
       :'此具名公牌有獨立真正 Rust NL2 CO-IP 局部鎖頻來源；只有街別及下注尺寸玩家池邊際頻率，不是逐私牌條件式實測策略。');
      const link=document.createElement('a');link.href=sourceUrl(run);
      link.target='_blank';link.rel='noopener';
      link.textContent='檢視 rank79 精確具名牌面原始 GTO／NL2 Rust Actions '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
   }
 }
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
 const v49b405=d=>{
 const q=d.B405_r214219_three_true_original_GTO_NL2_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219'||
  d.CERT_MULTIBOARD!==162||d.APPROX!==230||d.EST!==0||d.TOTAL!==392||
  !q||q.ranks?.join(',')!=='214,219'||
  q.spot!=='CO_BB'||q.actor!=='CO_IP'||q.line!=='x b100 c/x b50 c/x'||
  q.authenticated_sources_by_rank?.length!==2||
  q.authenticated_sources_by_rank.some(item=>
    ![214,219].includes(item.rank)||item.pins?.length!==3||
    item.pins.some(pin=>pin.GTO_strict_combos<=0||pin.NL2_strict_combos<=0||
      pin.original_GTO_SHA256?.length!==64||pin.actual_NL2_SHA256?.length!==64))||
  [214,219].some(rank=>{
    const r=Object.values(d.records||{}).find(x=>x.frequency_rank===rank);
    return !r||r.label!=='CERT-MULTIBOARD'||r.proven_exact_board_count!==3||
      r.solver_profile!=='CO_BB'||r.certified_3_to_5_exact_flop_boards?.length!==3||
      r.certified_3_to_5_exact_flop_boards.some(z=>
        z.acting_seat!==1||z.strict_full_street_combo_reachable<=0||
        z.actual_exact_action_line!=='x b100 c/x b50 c/x'||
        z.relative_spr_error_pct>5||
        !z.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64));
  })||
  d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
   throw Error('B405 exact 3-flop original GTO/NL2 IP source failclosed');
 return d;
};
const v48b390=d=>{
 const r=d.records?.['ln-ipfr-r_model-ujl14x'];
 const q=d.B390_rank107_three_true_original_GTO_NL2_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107'||
  d.CERT_MULTIBOARD!==160||d.APPROX!==232||d.EST!==0||d.TOTAL!==392||
  q?.rank!==107||q?.spot!=='BTN_BB'||q?.actor!=='BTN_IP'||
  q?.flops?.join(',')!=='Jh9d6s,7s5h3d,QsJh4d'||
  q?.source_blind_first10_preregistered!==true||q?.pins?.length!==3||
  q.pins.some(z=>z.GTO_strict_combos<=0||z.NL2_strict_combos<=0||
   z.original_GTO_SHA256?.length!==64||z.actual_NL2_SHA256?.length!==64)||
  r?.label!=='CERT-MULTIBOARD'||r?.frequency_rank!==107||
  r?.proven_exact_board_count!==3||
  r.certified_3_to_5_exact_flop_boards?.length!==3||
  r.certified_3_to_5_exact_flop_boards.some(z=>
    z.acting_seat!==1||z.actual_exact_action_line!=='b33 c/x b50 c/x'||
    z.strict_full_street_combo_reachable<=0||z.relative_spr_error_pct>5||
    !z.nl2_locked_variants?.some(v=>v.version==='exp_ip'&&v.sha256?.length===64))||
  d.no_generic_texture_GTO!==true||d.PR2_remains_draft_never_merge!==true)
  throw Error('B390 original 3-board GTO/NL2 source fails closed');
 return d;
};
const v48=d=>{
 const q=d.B369_rank27_three_new_true_original_GTO_NL2_OOP_flops;
 const r=d.records?.['ln-iso-lmp_r_model-1aov4pd'];
 const pins=q?.genuine_sources||[];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27'||
    d.CERT_MULTIBOARD!==160||d.APPROX!==232||d.EST!==0||d.TOTAL!==392||
    d.parent_v47_sha256?.length!==64||
    q?.rank!==27||q?.model_id!=='ln-iso-lmp_r_model-1aov4pd'||
    q?.spot!=='LMP_CO_BB'||q?.actor!=='BB_OOP'||q?.exact_line!=='b33 c/b50 c/'||
    q?.model_SPR!==11.53||
    q?.flops?.join(',')!=='KsQh4d,7s5h3d,9s6h3d'||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.original_flop_size_menu_all_33_50_75_100!==true||
    q?.preflop_169_class_assumed_not_observed_NL2!==true||
    q?.source_blind_expansion_preregistered!==true||
    q?.original_top24_high_frequency_preregistered!==false||
    q?.no_observed_private_combo_NL2_frequencies!==true||
    q?.exact_named_boards_only_no_texture_generalization!==true||
    pins.length!==3||pins.some(p=>p.run_id<=0||
      p.original_GTO_turn_sha256?.length!==64||p.true_NL2_OOP_turn_sha256?.length!==64||
      p.strict_GTO_actor_combos<=0||p.strict_NL2_OOP_actor_combos<=0||
      p.observed_marginal_source_nodes<=0||
      p.pin?.archive_index_sha256?.length!==64||p.pin?.archive_gzip_sha256?.length!==64||
      p.pin?.source_proof_sha256?.length!==64||p.pin?.solve_partition_sha256?.length!==64)||
    r?.label!=='CERT-MULTIBOARD'||r?.frequency_rank!==27||r?.solver_profile!=='LMP_CO_BB'||
    r?.proven_exact_board_count!==3||r?.high_frequency_preregistered!==true||
    r?.source_blind_expansion_rank!==27||r?.original_top24_high_frequency_preregistered!==false||
    r.certified_3_to_5_exact_flop_boards?.length!==3||
    r.certified_3_to_5_exact_flop_boards.some(p=>
      p.acting_seat!==0||p.actual_exact_action_line!=='b33 c/b50 c/'||
      p.strict_full_street_combo_reachable<=0||p.relative_spr_error_pct>5||
      p.genuine_gto_exploitability_pct>.5||p.assumed_preflop_ranges!==true||
      !p.source_kind?.startsWith('ASSUMED')||
      p.nl2_locked_variants?.[0]?.version!=='exp_oop'||
      p.nl2_locked_variants?.[0]?.sha256?.length!==64||
      p.nl2_locked_variants?.[0]?.observed_marginal_source_nodes<=0||
      !Number.isInteger(p.nl2_locked_variants?.[0]?.assumed_default_source_nodes)||
      !Number.isInteger(p.nl2_locked_variants?.[0]?.unlocked_source_nodes))||
    d.source_blind_expansion_ranks?.includes(27)!==true||
    d.supplementary_cert_count!==136||d.original_top24_cutoff_unchanged!==true||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
   throw Error('V48 rank27 source-blind three original 100bb GTO + NL2 OOP paired flops failclosed');
 return d;
};
const v47=d=>{
 const q=d.B364_rank96_three_true_original_GTO_NL2_OOP_flops;
 const r=d.records?.['ln-opfr-r_model-18g2rvt'];
 const pins=q?.genuine_sources||[];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96'||
    d.CERT_MULTIBOARD!==159||d.APPROX!==233||d.EST!==0||d.TOTAL!==392||
    d.parent_v46_sha256?.length!==64||
    q?.rank!==96||q?.model_id!=='ln-opfr-r_model-18g2rvt'||
    q?.spot!=='UTG_CO'||q?.actor!=='UTG_OOP'||q?.exact_line!=='b33 c/b50 c/'||
    q?.model_SPR!==4.15||
    q?.flops?.join(',')!=='As9h2d,Qs8h2d,Qs7h3d'||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.original_flop_size_menu_all_33_50_75_100!==true||
    q?.no_observed_private_combo_NL2_frequencies!==true||
    q?.exact_named_boards_only_no_texture_generalization!==true||
    q?.excluded_failed_historic_stage2_Ks7h2d_sha256?.length!==64||
    pins.length!==3||pins.some(p=>p.run_id<=0||
      p.original_GTO_turn_sha256?.length!==64||p.true_NL2_OOP_turn_sha256?.length!==64||
      p.strictly_reachable_GTO_actor_combos<=0||p.strictly_reachable_NL2_actor_combos<=0||
      p.pin?.archive_index_sha256?.length!==64||p.pin?.archive_gzip_sha256?.length!==64)||
    r?.label!=='CERT-MULTIBOARD'||r?.proven_exact_board_count!==3||
    r.certified_3_to_5_exact_flop_boards?.length!==3||
    r.certified_3_to_5_exact_flop_boards.some(p=>
      p.acting_seat!==0||p.actual_exact_action_line!=='b33 c/b50 c/'||
      p.strict_full_street_combo_reachable<=0||p.relative_spr_error_pct>5||
      p.assumed_preflop_ranges!==false||
      p.nl2_locked_variants?.[0]?.version!=='exp_oop'||
      p.nl2_locked_variants?.[0]?.sha256?.length!==64||
      !Number.isInteger(p.nl2_locked_variants?.[0]?.observed_marginal_source_nodes)||
      !Number.isInteger(p.nl2_locked_variants?.[0]?.assumed_default_source_nodes)||
      !Number.isInteger(p.nl2_locked_variants?.[0]?.unlocked_source_nodes))||
    d.records?.['ln-ipc-t_model-1cla93g']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='CERT-MULTIBOARD'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
   throw Error('V47 rank96 three NEW original 100bb GTO plus real NL2 OOP actor SHA/40-70 source failclosed');
 return d;
};
const v46=d=>{
 const q=d.B354_rank79_three_true_original_GTO_NL2_CO_IP_flops;
 const r=d.records?.['ln-ipc-t_model-1cla93g'];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79'||
    d.CERT_MULTIBOARD!==158||d.APPROX!==234||d.EST!==0||d.TOTAL!==392||
    d.parent_v45_sha256?.length!==64||
    q?.rank!==79||q?.model_id!=='ln-ipc-t_model-1cla93g'||
    q?.actor!=='CO_IP'||q?.spot!=='UTG_CO'||q?.exact_line!=='b50 c/x'||q?.SPR!==7||
    q?.flops?.join(',')!=='Ks7h2d,8s8h3d,Js9h4d'||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.source_run_shas?.length!==3||q?.historic_source_original_run!==44654973894||
    q?.genuine_source_GTO_3_and_actor_NL2_3!==true||
    q?.no_observed_private_card_conditional_NL2_villain_rates!==true||
    q.source_run_shas.some(p=>p.run<=0||p.GTO_SHA?.length!==64||p.NL2_SHA?.length!==64)||
    r?.label!=='CERT-MULTIBOARD'||r?.proven_exact_board_count!==3||
    r.certified_3_to_5_exact_flop_boards?.length!==3||
    r.certified_3_to_5_exact_flop_boards.some(p=>
       p.acting_seat!==1||p.actual_exact_action_line!=='b50 c/x'||
       p.strict_full_street_combo_reachable<=0||p.relative_spr_error_pct>5||
       p.nl2_locked_variants?.[0]?.version!=='exp_ip')||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='CERT-MULTIBOARD'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V46 rank79 3 real UTGCO original GTO plus genuine NL2 COIP actor source SHA failclosed');
 return d;
};
const v45=d=>{
 const q=d.B345_rank71_true_3_flop_GTO_NL2_OOP_evidence;
 const b=d.records?.['ln-iso-lmp_r_model-vlgh2t'];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71'||
    d.CERT_MULTIBOARD!==157||d.APPROX!==235||d.EST!==0||d.TOTAL!==392||
    d.parent_v44_sha256?.length!==64||
    q?.third_flop!=='3s3h2d'||q?.third_turn!=='7d'||
    q?.flops?.join(',')!=='4s4h2d,7s5h3d,3s3h2d'||
    q?.textures?.length<2||!['PAIRED','LOW'].every(t=>q.textures.includes(t))||
    q?.source_tree!=='RESTRICTED_LMP_50_ONLY_100BB_ASSUMED_PREFLOP'||
    q?.never_claim_unrestricted_game_or_private_hand_NL2_observation!==true||
    q?.original_archive_provenance?.length!==3||
    q.original_archive_provenance.some(p=>
       p.original_GTO_run<=0||p.original_gto_case_sha256?.length!==64||
       p.real_NL2_actor_partial_case_sha256?.length!==64||
       p.index_sha256?.length!==64||p.archive_sha256?.length!==64)||
    b?.label!=='CERT-MULTIBOARD'||b?.proven_exact_board_count!==3||
    b.certified_3_to_5_exact_flop_boards?.length!==3||
    b.certified_3_to_5_exact_flop_boards.some(p=>
       p.acting_seat!==0||p.actual_exact_action_line!=='b50 c/x b50 c/'||
       p.relative_spr_error_pct>5||p.strict_full_street_combo_reachable<=0||
       p.nl2_locked_variants?.[0]?.version!=='exp_oop')||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V45 rank71 3 genuine 100bb original restricted LMP50 GTO and real NL2 actor BB OOP SHA source failclosed');
 return d;
};
const v44=d=>{
 const q=d.B331_rank60_four_true_GTO_NL2_actor_lock_boards;
 const f=q?.fourth_original_GTO_and_NL2_source;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR'||
    d.CERT_MULTIBOARD!==156||d.APPROX!==236||d.EST!==0||d.TOTAL!==392||
    d.parent_v43_sha256?.length!==64||
    q?.model_id!=='ln-ipfr-t_model-hxdit'||q?.rank!==60||
    q?.actor!=='CO_IP'||q?.exact_line!=='x b50 c/x'||q?.model_SPR!==8.614||
    q?.board_count!==4||q.flops?.length!==4||new Set(q.flops).size!==4||
    !['9s7h4d','Js9h4d','Js9h5d','Js9s4s'].every(p=>q.flops.includes(p))||
    q.textures?.length<3||!['LOW','JT_HIGH','MONOTONE'].every(p=>q.textures.includes(p))||
    f?.flop!=='9s7h4d'||f?.turn!=='Ad'||
    f?.original_GTO_run!==44960100932||f?.true_partial_Rust_NL2_run!==44960924477||
    f?.strict_GTO_actor_combos!==6||f?.strict_real_NL2_actor_combos!==6||
    f?.NL2_actor_matching_SPR_combos!==6||
    f?.original_GTO_case_sha256?.length!==64||f?.authentic_real_NL2_source_sha256?.length!==64||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-hxdit']?.proven_exact_board_count!==4||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V44 rank60 fourth LOW exact original GTO and true NL2 actor IP SHA source failclosed');
 return d;
};
const v43=d=>{
 const q=d.B319_rank60_three_true_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60'||
    d.CERT_MULTIBOARD!==156||d.APPROX!==236||d.EST!==0||d.TOTAL!==392||
    d.parent_v42_sha256?.length!==64||
    q?.rank!==60||q?.model_id!=='ln-ipfr-t_model-hxdit'||
    q?.actor!=='CO_IP'||q?.exact_line!=='x b50 c/x'||q?.model_SPR!==8.614||
    !['B314','B315','B322','B323'].includes(q?.prereg_third_batch)||
    q?.flops?.length!==3||new Set(q.flops).size!==3||
    !q.flops.includes('Js9h4d')||!q.flops.includes('Js9h5d')||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.GTO_and_NL2_source_shas?.length!==3||
    q?.GTO_and_NL2_source_shas?.some(p=>
      !q.flops.includes(p.flop)||p.GTO_run<=0||p.NL2_run<=0||
      p.GTO_case_sha?.length!==64||p.NL2_raw_case_sha?.length!==64||
      p.strict_GTO_actor_combos<=0)!==false||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-hxdit']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
      throw Error('V43 rank60 original GTO plus genuine actor-IP Rust NL2 exact 3 flop SHA + multiple-texture failclosed');
 return d;
};
const v42=d=>{
 const z=d.B289_rank46_three_true_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'||
    d.CERT_MULTIBOARD!==155||d.APPROX!==237||d.EST!==0||d.TOTAL!==392||
    d.parent_v41_sha256?.length!==64||
    z?.rank!==46||z?.model_id!=='ln-iso-lmp_t_model-17z0wyl'||
    z?.flops?.join(',')!=='7s7h2d,8s8h3d,9s6h3d'||
    z?.exact_line!=='x b50 c/x'||z?.actor!=='CO_IP'||
    z?.assumed_limped_169class_preflop_not_observed_NL2_private_cards!==true||
    z?.third_B286_original_GTO_strict_combos!==12||
    z?.third_B288_actual_NL2_actor_SPR_strict_combos!==12||
    z?.genuine_GTO_runs?.['7s7h2d']!==44939456600||
    z?.genuine_GTO_runs?.['8s8h3d']!==44666294821||
    z?.genuine_GTO_runs?.['9s6h3d']!==44666294821||
    z?.real_NL2_actor_lock_runs?.['9s6h3d']!==44882669727||
    z?.real_NL2_actor_lock_runs?.['8s8h3d']!==44666294821||
    z?.real_NL2_actor_lock_runs?.['7s7h2d']!==44947726457||
    z?.GTO_and_NL2_source_shas?.length!==3||
    z?.GTO_and_NL2_source_shas?.some(p=>
       !['7s7h2d','8s8h3d','9s6h3d'].includes(p.flop)||
       p.GTO_case_sha?.length!==64||p.NL2_raw_case_sha?.length!==64||
       p.strict_GTO_actor_combos<=0)!==false||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.proven_exact_board_count!==3||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
     throw Error('V42 rank46 exact original 3 GTO plus actual CO-IP NL2 Rust SHA evidence gate failed');
 return d;
};
 const v41=d=>{
 const z=d.B271_rank61_three_authentic_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'||
    d.CERT_MULTIBOARD!==154||d.APPROX!==238||d.EST!==0||d.TOTAL!==392||
    d.parent_v40_sha256?.length!==64||
    z?.rank!==61||z?.model_id!=='ln-ipfr-t_model-qpx6tn'||
    z?.flops?.join(',')!=='Js9h5d,KsQh4d,QsJh4d'||
    z?.exact_line!=='x b100 c/x'||z?.actor!=='CO_IP'||
    z?.true_100bb_preflop_CFR_source_frozen_not_observed_NL2_private_card!==true||
    z?.only_exact_public_board_actions_actor_SPR_certified!==true||
    z?.original_GTO_and_NL2_actor_locked_source_pins?.length!==3||
    z?.original_GTO_and_NL2_actor_locked_source_pins?.some(p=>
      !['KsQh4d','Js9h5d','QsJh4d'].includes(p.flop)||
      ![44902146101,44902831383,44934430727].includes(p.original_GTO_run)||
      ![44902973337,44903478906,44935281174].includes(p.source_lock_run)||
      p.pin_sha256?.length!==64||p.gto_archive_sha256?.length!==64||
      p.NL2_archive_sha256?.length!==64||
      p.GTO_strict_actor_combos<=0||p.NL2_SPR_eligible_combos<=0)!==false||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
    throw Error('V41 exact source-rank61 three original CO-IP GTO + true NL2 Rust source gate failed');
 return d;
};
 const v40=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'||
    d.CERT_MULTIBOARD!==153||d.APPROX!==239||d.EST!==0||d.TOTAL!==392||
    d.parent_v39_sha256?.length!==64||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.rank!==313||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.model_id!=='ln-iso-lmp_r_model-wpg493'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.flops?.join(',')!=='6s5h3d,9s6h3d,KsQh4d'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.exact_line!=='b75 r c/x b50 c/x'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.actor!=='CO_IP'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['9s6h3d']!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.KsQh4d!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['6s5h3d']!==44901784001||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.genuine_B263_real_NL2_IP_lock_run!==44903333583||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.B263_strict_CO_IP_river_combos!==73||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.LMP_explicit_169class_preflop_ASSUMED_not_observed_NL2_hand!==true||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.no_observed_NL2_private_card_conditionals!==true||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.proven_exact_board_count!==3||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
    throw Error('V40 exact original three named GTO and true CO-IP NL2 Rust SHA gate failed');
 return d;
};
 const v39=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30'||
    d.CERT_MULTIBOARD!==152||d.APPROX!==240||d.EST!==0||d.TOTAL!==392||
    d.parent_v38_sha256?.length!==64||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.rank!==30||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.model_id!=='ln-opfr-t_model-1hmsxaw'||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.flops?.join(',')!=='Js9h4d,KsQh4d,QsJh4d'||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.exact_line!=='b50 c/'||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.actor!=='UTG_OOP'||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.original_GTO_runs?.KsQh4d!==44894369547||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.original_GTO_runs?.Js9h4d!==44895186652||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.original_GTO_runs?.QsJh4d!==44900567417||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.real_NL2_actor_OOP_lock_runs?.KsQh4d!==44895095589||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.real_NL2_actor_OOP_lock_runs?.Js9h4d!==44900532333||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.real_NL2_actor_OOP_lock_runs?.QsJh4d!==44900938891||
    d.B247_rank30_three_genuine_GTO_NL2_UTG_OOP_flops?.preflop_CFR_pinned_not_observed_NL2_private_hand!==true||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.proven_exact_board_count!==3||
    d.records?.['ln-ipc-r_model-dfikbd']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
    throw Error('V39 rank30 exact three original GTO and real actor-OOP NL2 source gate failed');
 return d;
};
 const v38=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V38_B206_RANK190'||
    d.CERT_MULTIBOARD!==151||d.APPROX!==241||d.EST!==0||d.TOTAL!==392||
    d.parent_v37_sha256?.length!==64||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.rank!==190||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.flops?.join(',')!=='8s8h3d,Js9h4d,Ks7h2d'||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.exact_line!=='x b75 c/x b100 c/x'||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.actor!=='BB_IP'||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.['8s8h3d']!==44666285424||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.['Js9h4d']!==44666285424||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.Ks7h2d!==44654973894||
    d.B206_rank190_three_genuine_GTO_NL2_BB_IP_flops?.preflop_CFR_pinned_not_observed_NL2_private_hand!==true||
    d.records?.['ln-ipc-r_model-dfikbd']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipc-r_model-dfikbd']?.proven_exact_board_count!==3||
    d.records?.['ln-ipc-r_model-1s0a4ds']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipc-r_model-vvxn9n']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-qsgdjf']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
     throw Error('V38 rank190 3 named original GTO and actual BB-IP NL2 source gate failed');
 return d;
};
 const v37=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V37_B205_RANK188'||
    d.CERT_MULTIBOARD!==150||d.APPROX!==242||d.EST!==0||d.TOTAL!==392||
    d.parent_v36_sha256?.length!==64||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.rank!==188||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.flops?.join(',')!=='8s8h3d,9s6h3d,Ks7h2d'||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.exact_line!=='x b50 c/x b100 c/x'||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.actor!=='BB_IP'||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.['8s8h3d']!==44666285424||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.['9s6h3d']!==44732810327||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_runs?.Ks7h2d!==44654973894||
    d.B205_rank188_three_genuine_GTO_NL2_BB_IP_flops?.preflop_CFR_pinned_not_observed_NL2_private_hand!==true||
    d.records?.['ln-ipc-r_model-1s0a4ds']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipc-r_model-1s0a4ds']?.proven_exact_board_count!==3||
    d.records?.['ln-ipc-r_model-vvxn9n']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-qsgdjf']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
     throw Error('V37 rank188 3 named original GTO and actual BB-IP NL2 source gate failed');
 return d;
};
 const v36=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159'||
    d.CERT_MULTIBOARD!==149||d.APPROX!==243||d.EST!==0||d.TOTAL!==392||
    d.parent_v35_sha256?.length!==64||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.rank!==159||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.flops?.join(',')!=='9s6h3d,Js9h4d,KsQh4d'||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.exact_line!=='x b100 c/x x/x'||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.actor!=='BB_IP'||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_B1_B5_B4_runs?.Js9h4d!==44666285424||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_B1_B5_B4_runs?.KsQh4d!==44736420272||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.original_GTO_B1_B5_B4_runs?.['9s6h3d']!==44732810327||
    d.B201_rank159_three_genuine_GTO_NL2_BB_IP_flops?.preflop_CFR_pinned_not_observed_private_hand!==true||
    d.records?.['ln-ipc-r_model-vvxn9n']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipc-r_model-vvxn9n']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-qsgdjf']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||
    d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
      throw Error('V36 rank159 three original GTO plus true BB-IP NL2 source gate failed');
 return d;
};
 const v35=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201'||
    d.CERT_MULTIBOARD!==148||d.APPROX!==244||d.EST!==0||d.TOTAL!==392||
    d.parent_v34_sha256?.length!==64||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.rank!==201||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.flops?.join(',')!=='8s8h3d,9s6h3d,KsQh4d'||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.exact_line!=='x b33 c/x b100 c/x'||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.actor!=='CO_IP'||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.original_GTO_B3_run!==44666294821||
    d.B193_rank201_three_original_GTO_NL2_named_flops?.preflop_169class_ASSUMED_not_observed!==true||
    d.records?.['ln-iso-lmp_r_model-qsgdjf']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-qsgdjf']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-r_model-hqu5je']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
     throw Error('V35 rank201 strict original GTO/NL2 three-board source check failed');
 return d;
};
 const v34=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202'||
    d.CERT_MULTIBOARD!==147||d.APPROX!==245||d.EST!==0||d.TOTAL!==392||
    d.parent_v33_sha256?.length!==64||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['199']?.flops?.join(',')!=='8s8h3d,9s6h3d,KsQh4d'||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['202']?.flops?.join(',')!=='8s8h3d,9s6h3d,KsQh4d'||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['199']?.actor!=='CO_IP'||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['202']?.actor!=='CO_IP'||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['199']?.original_gto_run!==44666294821||
    d.B190_rank199_202_three_real_GTO_NL2_pairing?.['202']?.original_gto_run!==44666294821||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-10l8t7i']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-yh8124']?.proven_exact_board_count!==3||
    d.records?.['ln-ipfr-r_model-hqu5je']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||
    d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
      throw Error('V34 two ranks full sourceblind GTO+NL2 3-flop gate failed');
 return d;
};
 const v33=d=>{
  if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138'||
     d.CERT_MULTIBOARD!==145||d.APPROX!==247||d.EST!==0||d.TOTAL!==392||
     d.original_v32_cert!==144||d.original_v32_approx!==248||
     d.original_top24_cutoff_unchanged!==true||
     d.B179_rank138_three_genuine_flops?.rank!==138||
     d.B179_rank138_three_genuine_flops?.flops?.join(',')!=='8s8h3d,As9h2d,Js9h4d'||
     d.B179_rank138_three_genuine_flops?.exact_action_line!=='x x/x x/x'||
     d.B179_rank138_three_genuine_flops?.actor!=='CO_IP'||
     d.B179_rank138_three_genuine_flops?.original_B04_historical_restricted_GTO_tree_explicit!==true||
     d.records?.['ln-ipfr-r_model-hqu5je']?.label!=='CERT-MULTIBOARD'||
     d.records?.['ln-ipfr-r_model-hqu5je']?.proven_exact_board_count!==3||
     d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
     d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
     d.no_generic_texture_GTO!==true||
     d.no_observed_private_card_NL2_rates!==true||
     d.PR2_remains_draft_never_merge!==true||
     Object.keys(d.records||{}).length!==392)
       throw Error('V33 rank138 3 real GTO+NL2 named boards source gate invalid');
  return d;
};
 const v32=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80'||
    d.CERT_MULTIBOARD!==144||d.APPROX!==248||d.EST!==0||d.TOTAL!==392||
    d.original_v31_cert!==143||d.original_v31_approx!==249||
    d.original_top24_cutoff_unchanged!==true||
    d.B168_rank80_true_third_flop?.rank!==80||
    d.B168_rank80_true_third_flop?.flops?.join(',')!=='4s4h2d,7s5h3d,KsQh4d'||
    d.B168_rank80_true_third_flop?.exact_action_line!=='b33 c/x x/x'||
    d.B168_rank80_true_third_flop?.preflop_169class_assumed!==true||
    Object.keys(d.records||{}).length!==392||
    d.records?.['ln-iso-lmp_r_model-17pklmg']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-17pklmg']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||
    d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true)
      throw Error('V32 not genuinely verified 3-board rank80 CERT');
 return d;
};
 const v31=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150'||
      d.CERT_MULTIBOARD!==143||d.APPROX!==249||d.EST!==0||d.TOTAL!==392||
      d.original_v30_cert!==142||d.original_v30_approx!==250||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='41,47,69,88,150,236'||
      d.supplementary_cert_count!==119||
      d.B161_rank150_original_two_gaps_now_true_locked?.rank!==150||
      d.B161_rank150_original_two_gaps_now_true_locked?.flops?.join(',')!=='8s8h3d,9s6h3d,KsQh4d'||
      d.B161_rank150_original_two_gaps_now_true_locked?.exact_action_line!=='x b33 c/x x/x'||
      d.B161_rank150_original_two_gaps_now_true_locked?.limped_preflop_169class_assumed!==true||
      Object.keys(d.records||{}).length!==392||
      d.records?.['ln-iso-lmp_r_model-4ys53a']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-iso-lmp_t_model-1oaypnl']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-3bp-3b_r_model-8uwbze']?.label!=='CERT-MULTIBOARD')
      throw Error('B161 V31 frozen rank150 three named original GTO/true NL2 actor IP sources invalid');
   return d;
};
 const v30=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47'||
      d.CERT_MULTIBOARD!==142||d.APPROX!==250||d.EST!==0||d.TOTAL!==392||
      d.original_v29_cert!==141||d.original_v29_approx!==251||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='41,47,69,88,236'||
      d.supplementary_cert_count!==118||
      d.B145_rank47_true_two_missing_flops?.rank!==47||
      d.B145_rank47_true_two_missing_flops?.flops?.join(',')!=='8s8h3d,9s6h3d,KsQh4d'||
      d.B145_rank47_true_two_missing_flops?.limped_preflop_169class_assumed!==true||
      d.B145_rank47_true_two_missing_flops?.exact_action_line!=='x b33 c/x'||
      Object.keys(d.records||{}).length!==392||
      d.records?.['ln-iso-lmp_t_model-1oaypnl']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-3bp-3b_r_model-8uwbze']?.label!=='CERT-MULTIBOARD')
      throw Error('B145 V30 original B3 actor-IP rank47 3-flop certificate invalid');
   return d;
 };
 const v29=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88'||
      d.CERT_MULTIBOARD!==141||d.APPROX!==251||d.EST!==0||
      d.TOTAL!==392||d.original_v28_cert!==140||
      d.original_v28_approx!==252||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='41,69,88,236'||
      d.supplementary_cert_count!==117||
      d.B142_rank88_true_third_flop?.rank!==88||
      d.B142_rank88_true_third_flop?.flops?.join(',')!=='As7h3d,Jh9d6s,Ks7h2d'||
      Object.keys(d.records||{}).length!==392||
      d.records?.['ln-3bp-3b_r_model-8uwbze']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipfr-r_model-159a6z6']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipfr-t_model-sxr0qa']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipc-r_model-1nz4lt1']?.label!=='CERT-MULTIBOARD')
      throw Error('B142 V29 original B117 GTO and true NL2 hero-OOP source-blind certificate invalid');
   return d;
 };
 const v28=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69'||
      d.CERT_MULTIBOARD!==140||d.APPROX!==252||d.EST!==0||
      d.TOTAL!==392||d.original_v27_cert!==139||
      d.original_v27_approx!==253||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='41,69,236'||
      d.supplementary_cert_count!==116||
      d.B133_rank69_true_third_flop?.rank!==69||
      d.B133_rank69_true_third_flop?.flops?.join(',')!=='As7h3d,Jh9d6s,KsQh4d'||
      Object.keys(d.records||{}).length!==392||
      d.records?.['ln-ipfr-r_model-159a6z6']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipfr-t_model-sxr0qa']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipc-r_model-1nz4lt1']?.label!=='CERT-MULTIBOARD')
      throw Error('B133 V28 genuine original GTO+actor-IP and immutable B112 cohort gate failed');
   return d;
 };
 const v27=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_236'||
      d.CERT_MULTIBOARD!==139||d.APPROX!==253||d.EST!==0||
      d.TOTAL!==392||d.original_v26_cert!==137||
      d.original_v26_approx!==255||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='41,236'||
      d.supplementary_cert_count!==115||
      d.b123_true_rank_proofs?.length!==2||
      Object.keys(d.records||{}).length!==392||
      d.records?.['ln-ipfr-r_model-159a6z6']?.label!=='APPROX'||
      d.records?.['ln-ipfr-t_model-sxr0qa']?.label!=='CERT-MULTIBOARD'||
      d.records?.['ln-ipc-r_model-1nz4lt1']?.label!=='CERT-MULTIBOARD')
      throw Error('B123 V27 exact genuine actor source gate invalid');
   return d;
 };
 const v26=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220'||
      d.CERT_MULTIBOARD!==137||d.APPROX!==255||d.TOTAL!==392||
      d.original_v25_cert!==135||d.original_v25_approx!==257||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='215,220'||
      d.supplementary_cert_count!==113||
      d.B2_failed_SB3_source_excluded!==true||
      d.B108_reused_original_B2_GTO_flop_not_recomputed!==true||
      Object.keys(d.records||{}).length!==392)
      throw Error('V26 original B2 GTO and B108 Rust actor-IP paired source certificate invalid');
   return d;
 };
 const v25=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135'||
      d.CERT_MULTIBOARD!==135||d.APPROX!==257||d.TOTAL!==392||
      d.original_v24_cert!==134||d.original_v24_approx!==258||
      d.original_top24_cutoff_unchanged!==true||
      d.added_cert_rank!==135||d.added_cert_model_id!=='ln-ipfr-r_model-3lq5u6'||
      String(d.source_blind_expansion_ranks)!=='135'||
      d.B105_only_turn_river_NL2_IP_lock!==true||
      d.supplementary_cert_count!==111||Object.keys(d.records||{}).length!==392)
      throw Error('V25 genuine B1 GTO and authenticated B105 IP actor river source invalid');
   return d;
 };
 const v24=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43'||
      d.CERT_MULTIBOARD!==134||d.APPROX!==258||d.TOTAL!==392||
      d.original_v23_cert!==133||d.original_v23_approx!==259||
      d.original_top24_cutoff_unchanged!==true||
      d.added_cert_rank!==43||d.added_cert_model_id!=='ln-opfr-r_model-1e6gydx'||
      String(d.source_blind_expansion_ranks)!=='43'||
      d.B102_only_turn_river_NL2_lock_from_original_full_flop_GTO!==true||
      d.supplementary_cert_count!==110||Object.keys(d.records||{}).length!==392)
      throw Error('V24 rank43 original B5 GTO and B102 real OOP lock unverified');
   return d;
 };
 const v23=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR'||
      d.CERT_MULTIBOARD!==133||d.APPROX!==259||d.TOTAL!==392||
      d.original_v22_cert!==131||d.original_v22_approx!==261||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='77,78'||
      d.B99_only_turn_river_pool_lock_not_locked_flop!==true||
      d.supplementary_cert_count!==109||
      Object.keys(d.records||{}).length!==392)
      throw Error('V23 pinned true LMP GTO plus real OOP local NL2 actor source invalid');
   return d;
 };
 const v22=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94'||
      d.CERT_MULTIBOARD!==131||d.APPROX!==261||d.TOTAL!==392||
      d.original_v21_cert!==126||d.original_v21_approx!==266||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='338,341,344,349,351'||
      d.supplementary_cert_count!==107||Object.keys(d.records||{}).length!==392)
      throw Error('V22 5 original source-blind true GTO/actor hero locked models invalid');
   return d;
 };
 const v21=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V21_BATCH92'||
      d.CERT_MULTIBOARD!==126||d.APPROX!==266||d.TOTAL!==392||
      d.original_v20_cert!==122||d.original_v20_approx!==270||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='316,322,323,335'||
      d.supplementary_cert_count!==102||Object.keys(d.records||{}).length!==392)
      throw Error('V21 4 genuine 3-5-board GTO/hero lock source proofs invalid');
   return d;
 };
 const v20=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V20_BATCH90'||
      d.CERT_MULTIBOARD!==122||d.APPROX!==270||d.TOTAL!==392||
      d.original_v19_cert!==116||d.original_v19_approx!==276||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='297,298,301,303,304,310'||
      d.supplementary_cert_count!==98||Object.keys(d.records||{}).length!==392)
      throw Error('V20 six source-blind GTO and hero NL2 locks invalid');
   return d;
 };
 const v19=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V19_BATCH88'||
      d.CERT_MULTIBOARD!==116||d.APPROX!==276||d.TOTAL!==392||
      d.original_v18_cert!==114||d.original_v18_approx!==278||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='286,294'||
      d.supplementary_cert_count!==92||Object.keys(d.records||{}).length!==392)
      throw Error('V19 exact two model GTO plus hero-lock certificate invalid');
   return d;
 };
 const v18=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V18_BATCH86'||
      d.CERT_MULTIBOARD!==114||d.APPROX!==278||d.TOTAL!==392||
      d.original_v17_cert!==108||d.original_v17_approx!==284||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='256,263,264,268,269,273'||
      d.supplementary_cert_count!==90||Object.keys(d.records||{}).length!==392)
      throw Error('V18 six authentic 3–5-board model certification proof missing');
   return d;
 };
 const v17=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V17_BATCH84'||
      d.CERT_MULTIBOARD!==108||d.APPROX!==284||d.TOTAL!==392||
      d.original_v16_cert!==107||d.original_v16_approx!==285||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='239'||
      d.supplementary_cert_count!==84||Object.keys(d.records||{}).length!==392)
      throw Error('V17 one exact 5-board GTO/hero-lock model invalid');
   return d;
 };
 const v16=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V16_BATCH82'||
      d.CERT_MULTIBOARD!==107||d.APPROX!==285||d.TOTAL!==392||
      d.original_v15_cert!==104||d.original_v15_approx!==288||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='217,229,230'||
      d.supplementary_cert_count!==83||Object.keys(d.records||{}).length!==392)
      throw Error('V16 three authentic 3-5-flop CERT source records invalid');
   return d;
 };
 const v15=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V15_BATCH80'||
      d.CERT_MULTIBOARD!==104||d.APPROX!==288||d.TOTAL!==392||
      d.original_v14_cert!==101||d.original_v14_approx!==291||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='203,206,207'||
      d.supplementary_cert_count!==80||Object.keys(d.records||{}).length!==392)
      throw Error('V15 authentic three model 3-5 named flop CERT source ledger failed');
   return d;
 };
 const v14=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V14_BATCH77'||
      d.CERT_MULTIBOARD!==101||d.APPROX!==291||d.TOTAL!==392||
      d.original_v13_cert!==89||d.original_v13_approx!==303||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='177,178,181,182,183,184,185,186,187,189,191,195'||
      d.supplementary_cert_count!==77||Object.keys(d.records||{}).length!==392)
      throw Error('V14 real 12-model named-board certificate invalid');
   return d;
 };
 const v13=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75'||
      d.CERT_MULTIBOARD!==89||d.APPROX!==303||d.TOTAL!==392||
      d.original_v12_cert!==86||d.original_v12_approx!==306||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='156,170,172'||
      d.supplementary_cert_count!==65||Object.keys(d.records||{}).length!==392)
      throw Error('V13 authentic 3 model real-board source ledger invalid');
   return d;
 };
 const v12=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73'||
      d.CERT_MULTIBOARD!==86||d.APPROX!==306||d.TOTAL!==392||
      d.original_v11_cert!==77||d.original_v11_approx!==315||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='136,137,143,144,145,149,152,153,155'||
      d.supplementary_cert_count!==62||Object.keys(d.records||{}).length!==392)
      throw Error('V12 nine true board CERT sources invalid');
   return d;
 };
 const v11=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V11_BATCH71'||
      d.CERT_MULTIBOARD!==77||d.APPROX!==315||d.TOTAL!==392||
      d.original_v10_cert!==66||d.original_v10_approx!==326||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='117,118,119,120,126,127,128,129,130,132,134'||
      d.supplementary_cert_count!==53||Object.keys(d.records||{}).length!==392)
      throw Error('V11 eleven authentic source-blind CERT models invalid');
   return d;
 };
 const v10=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V10_BATCH69'||
      d.CERT_MULTIBOARD!==66||d.APPROX!==326||d.TOTAL!==392||
      d.original_v9_cert!==57||d.original_v9_approx!==335||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='98,100,101,102,104,105,106,112,113'||
      d.supplementary_cert_count!==42||Object.keys(d.records||{}).length!==392)
      throw Error('V10 authentic source-blind nine-model cert ledger invalid');
   return d;
 };
 const v9=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67'||
      d.CERT_MULTIBOARD!==57||d.APPROX!==335||d.TOTAL!==392||
      d.original_v8_cert!==56||d.original_v8_approx!==336||
      d.original_top24_cutoff_unchanged!==true||
      d.added_cert_rank!==40||d.added_cert_model_id!=='ln-ipc-t_model-188b2d5'||
      String(d.source_blind_expansion_ranks)!=='40'||
      d.rank41_CO_BB_still_APPROX!==true||
      d.supplementary_cert_count!==33||Object.keys(d.records||{}).length!==392)
      throw Error('V9 B67 SB_BB rank40 original GTO and hero-IP source ledger invalid');
   return d;
 };
 const v8=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61'||
      d.CERT_MULTIBOARD!==56||d.APPROX!==336||d.TOTAL!==392||
      d.original_v7_cert!==48||d.original_v7_approx!==344||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='81,82,85,86,87,90,91,95'||
      d.supplementary_cert_count!==32||Object.keys(d.records||{}).length!==392)
      throw Error('V8 authentic model source proofs invalid');
   return d;
 };
 const v7=d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V7_BATCH59'||
      d.CERT_MULTIBOARD!==48||d.APPROX!==344||d.TOTAL!==392||
      d.original_v6_cert!==42||d.original_v6_approx!==350||
      d.original_top24_cutoff_unchanged!==true||
      String(d.source_blind_expansion_ranks)!=='59,63,64,65,66,70'||
      d.supplementary_cert_count!==24||Object.keys(d.records||{}).length!==392)
      throw Error('V7 frozen source-blind source proof invalid');
   return d;
 };
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
 return fetch('data/nl2_hu_multiboard_status_v49_b405_rank214_219.json',{cache:'no-store'}).then(open).then(v49b405)
    .catch(()=>fetch('data/nl2_hu_multiboard_status_v48_b390_rank107.json',{cache:'no-store'}).then(open).then(v48b390))
    .catch(()=>fetch('data/nl2_hu_multiboard_status_v48_b369_rank27.json',{cache:'no-store'}).then(open).then(v48))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v47_b364_rank96.json',{cache:'no-store'}).then(open).then(v47))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v46_b354_rank79.json',{cache:'no-store'}).then(open).then(v46))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v45_b345_rank71.json',{cache:'no-store'}).then(open).then(v45))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json',{cache:'no-store'}).then(open).then(v44))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v43_b319_rank60.json',{cache:'no-store'}).then(open).then(v43))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v42_b289_rank46.json',{cache:'no-store'}).then(open).then(v42))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v41_b271_rank61.json',{cache:'no-store'}).then(open).then(v41))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v40_b265_rank313.json',{cache:'no-store'}).then(open).then(v40))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v39_b247_rank30.json',{cache:'no-store'}).then(open).then(v39))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v38_b206_rank190.json',{cache:'no-store'}).then(open).then(v38))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v37_b205_rank188.json',{cache:'no-store'}).then(open).then(v37))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v36_b201_rank159.json',{cache:'no-store'}).then(open).then(v36))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v35_b193_rank201.json',{cache:'no-store'}).then(open).then(v35))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v34_b190_rank199_202.json',{cache:'no-store'}).then(open).then(v34))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v33_b179_rank138.json',{cache:'no-store'}).then(open).then(v33))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v32_b168_rank80.json',{cache:'no-store'}).then(open).then(v32))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v31_b161_rank150.json',{cache:'no-store'}).then(open).then(v31))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v30_b145_rank47.json',{cache:'no-store'}).then(open).then(v30))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v29_b142_rank88.json',{cache:'no-store'}).then(open).then(v29))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v28_b133_rank69.json',{cache:'no-store'}).then(open).then(v28))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v27_b123_r41_236.json',{cache:'no-store'}).then(open).then(v27))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v26_b111_rank215_220.json',{cache:'no-store'}).then(open).then(v26))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v25_b106_rank135.json',{cache:'no-store'}).then(open).then(v25))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v24_b103_rank43.json',{cache:'no-store'}).then(open).then(v24))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v23_b100_lmp_pair.json',{cache:'no-store'}).then(open).then(v23))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v22_batch94.json',{cache:'no-store'}).then(open).then(v22))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v21_batch92.json',{cache:'no-store'}).then(open).then(v21))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v20_batch90.json',{cache:'no-store'}).then(open).then(v20))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v19_batch88.json',{cache:'no-store'}).then(open).then(v19))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v18_batch86.json',{cache:'no-store'}).then(open).then(v18))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v17_batch84.json',{cache:'no-store'}).then(open).then(v17))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v16_batch82.json',{cache:'no-store'}).then(open).then(v16))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v15_batch80.json',{cache:'no-store'}).then(open).then(v15))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v14_batch77.json',{cache:'no-store'}).then(open).then(v14))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v13_batch75.json',{cache:'no-store'}).then(open).then(v13))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v12_batch73.json',{cache:'no-store'}).then(open).then(v12))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v11_batch71.json',{cache:'no-store'}).then(open).then(v11))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v10_batch69.json',{cache:'no-store'}).then(open).then(v10))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v9_rank40_b67.json',{cache:'no-store'}).then(open).then(v9))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v8_batch61.json',{cache:'no-store'}).then(open).then(v8))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v7_batch59.json',{cache:'no-store'}).then(open).then(v7))
   .catch(()=>fetch('data/nl2_hu_multiboard_status_v6_rank33.json',{cache:'no-store'}).then(open).then(v6))
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
   if(!['NL2_HU_392_MULTIBOARD_CERT_STATUS_V1','NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE','NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28','NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50','NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55','NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33','NL2_HU_392_MULTIBOARD_CERT_STATUS_V7_BATCH59','NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61','NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67','NL2_HU_392_MULTIBOARD_CERT_STATUS_V10_BATCH69','NL2_HU_392_MULTIBOARD_CERT_STATUS_V11_BATCH71','NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73','NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75','NL2_HU_392_MULTIBOARD_CERT_STATUS_V14_BATCH77','NL2_HU_392_MULTIBOARD_CERT_STATUS_V15_BATCH80','NL2_HU_392_MULTIBOARD_CERT_STATUS_V16_BATCH82','NL2_HU_392_MULTIBOARD_CERT_STATUS_V17_BATCH84','NL2_HU_392_MULTIBOARD_CERT_STATUS_V18_BATCH86','NL2_HU_392_MULTIBOARD_CERT_STATUS_V19_BATCH88','NL2_HU_392_MULTIBOARD_CERT_STATUS_V20_BATCH90','NL2_HU_392_MULTIBOARD_CERT_STATUS_V21_BATCH92','NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94','NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR','NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43','NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135','NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220','NL2_HU_392_MULTIBOARD_CERT_STATUS_V49_B405_R214_R219','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27','NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96','NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79','NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71','NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR','NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60','NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46','NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61','NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313','NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30','NL2_HU_392_MULTIBOARD_CERT_STATUS_V38_B206_RANK190','NL2_HU_392_MULTIBOARD_CERT_STATUS_V37_B205_RANK188','NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159','NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201','NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202','NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138','NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80','NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150','NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47','NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88','NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69','NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_236','NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'].includes(d.schema)||d.CERT_MULTIBOARD+d.APPROX!==392)
      throw Error('模型認證來源驗證失敗');
   status=d;
   models=Object.values(d.records).filter(x=>x.label==='CERT-MULTIBOARD')
      .sort((a,b)=>a.frequency_rank-b.frequency_rank);
   el('model').replaceChildren();
   models.forEach((x,i)=>opt(el('model'),String(i),'#'+x.frequency_rank+' '+x.solver_profile+' '+x.model_id));
   const summaryBase='CERT-MULTIBOARD '+d.CERT_MULTIBOARD+'／392；APPROX '+d.APPROX+
        '／392。原始頻率優先前'+d.top_N_rank_cutoff+
        '格'+(d.supplementary_cert_count?'；另有經事前登記的補充認證 '+d.supplementary_cert_count+' 格':'')+
        '；CERT 僅限下方 3–5 張具名牌面，其他 '+d.APPROX+' 個模型仍為 APPROX。';
   text('summary',summaryBase);
   fetch('data/nl2_hu_cert_lock_medium_matrix_v49_b405.json',{cache:'no-store'}).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b390.json',{cache:'no-store'})).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v48_b369.json',{cache:'no-store'})).catch(()=>fetch('data/nl2_hu_cert_lock_medium_matrix_v47_b364.json',{cache:'no-store'}))
    .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
    .then(m=>{
      const locks=(m.boards||[]).flatMap(b=>b.hero_lock_proofs||[]);
      const unknown=locks.filter(x=>x.node_rate_data_status==='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN').length;
      const a=m.strict_aggregate||{};
      text('summary',summaryBase+'；具名來源牌面 '+fmt(a.named_board_proofs,0)+
        '；部分 NL2 node-lock '+fmt(a.hero_lock_variants,0)+
        '（實測聚合節點 '+fmt(a.observed_marginal_pattern_nodes,0)+
        '／假設 '+fmt(a.assumed_pattern_nodes,0)+'／未匹配 '+fmt(a.unmatched_opponent_nodes,0)+
        '）；分母 UNKNOWN '+unknown+
        '；50% 非極化精確牌面研究候選 '+fmt(a.b50_research_candidate_boards,0)+
        '。UNKNOWN 不當作零；50% 標記只限具名牌面研究。');
    }).catch(()=>{});
   const id=q.get('model');
   const i=id?models.findIndex(x=>x.model_id===id):-1;
   if(i>=0)el('model').value=String(i);
   selectedModel();
 }).catch(e=>{text('summary','來源無法驗證：'+e.message);setMessage('沒有可安全展示的真實多牌面 CERT。')});
})();