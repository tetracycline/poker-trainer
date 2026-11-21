/* 392 NL2 HU training groups: genuine 3-5-board CERT evidence, otherwise
 * prominently APPROX. A GTO citation is scoped to explicit public cards,
 * exact betting history, actor, 100bb range and corresponding SPR only.
 */
(()=>{
'use strict';
const app=document.getElementById('app');
if(!app)return;
let registry=null,pending=false;
const safe=(x)=>String(x??'');
const approxReasons={
 LOW_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF:'低於依 NL2 池頻率估算的前 24／392 高頻截斷點；保留近似策略',
 NOT_ENOUGH_DISTINCT_AUTHENTIC_FLOPS_WITH_HERO_LOCKED_SOURCE:'尚無三個以上不同代表翻牌，同時符合完整行動歷史、實際 SPR、合法 combo 與英雄節點鎖來源',
 NO_TRUSTED_ACTING_SEAT_IN_PREFLOP:'翻前角色來源不足，不能驗證 OOP／IP 真實動作順序',
 INCOMPLETE_OR_EXTRA_STREET_HISTORY:'翻／轉／河的完整行動歷史不一致',
 UNPARSABLE_ACTION_SEQUENCE:'部分行動或下注尺寸仍是訓練近似，沒有精確 solver 來源',
 REPRESENTATIVE_BOARD_COVERAGE_LACKS_SECOND_TEXTURE:'代表牌面種類不足，不能假裝整類牌面都經驗證'
};
function make(tag,cls,value){
 const x=document.createElement(tag);if(cls)x.className=cls;
 if(value!==undefined)x.textContent=value;
 return x;
}
function render(){
 pending=false;
 if(!registry)return;
 const statuses=app.querySelectorAll('.hu-board-cert-status[data-hu-model]');
 for(const tag of statuses){
   const id=tag.dataset.huModel,item=registry.records[id];
   if(!item){if(!tag.dataset.mbApplied){tag.dataset.mbApplied='missing';tag.textContent='APPROX 近似（無對應來源）';}continue;}
   // DOM label changes themselves fire the MutationObserver. Mark before
   // modifying child nodes to avoid a self-triggered render microtask loop.
   const signature=item.label+':'+item.proven_exact_board_count;
   if(tag.dataset.mbApplied===signature)continue;
   tag.dataset.mbApplied=signature;
   const sec=tag.closest('.sec');
   const note=sec?.querySelector('.hu-board-proof[data-hu-model]');
   if(item.label==='CERT-MULTIBOARD'){
     const cases=item.certified_3_to_5_exact_flop_boards;
     if(cases.length<3||cases.length>5||new Set(cases.map(z=>z.flop)).size!==cases.length||
        cases.some(b=>b.strict_full_street_combo_reachable<=0||!b.nl2_locked_variants?.length)){
       tag.textContent='APPROX 來源驗證失敗';continue;
     }
     tag.textContent='CERT-MULTIBOARD — 限 '+cases.length+' 組具名公牌的真實 GTO';
     tag.style.background='#1b5f41';
     tag.style.color='#d6ffe4';
     tag.style.padding='4px 7px';
     tag.style.borderRadius='5px';
     if(note){
       note.replaceChildren(document.createTextNode(
         'NL2 高頻排名 #'+item.frequency_rank+'；通用六牌面／五手牌格仍為 APPROX。'
         +' 本證據只涵蓋以下實際發牌、行動線與 SPR：'));
       const ul=make('ul','hu-exact-gto-proof');
       for(const b of cases){
         const li=make('li','');
         const flavor=b.flop_texture;
         li.append(document.createTextNode(
           b.public_board+'（'+flavor+'）｜歷史 '+b.actual_exact_action_line
           +'｜SPR '+b.actual_spr+'｜可達 combo '+b.strict_full_street_combo_reachable
           +'｜GTO exploitability '+b.genuine_gto_exploitability_pct.toFixed(3)+'%｜'));
         const link=make('a','', '真實 CFR Run '+b.source_run_id);
         if(b.source_kind.includes('OFFICIAL')){
           link.href='nl2-cfr.html?spot='+encodeURIComponent(item.solver_profile)
              +'&version=gto&sha='+encodeURIComponent(b.source_sha256)
              +'&board='+encodeURIComponent(b.public_board)
              +'&line='+encodeURIComponent(b.actual_exact_action_line);
         }else{
           link.href='nl2-multiboard.html?model='+encodeURIComponent(item.model_id)+
               '&board='+encodeURIComponent(b.public_board)+'&sha='+encodeURIComponent(b.source_sha256);
           link.textContent='本公牌真實 GTO 與 NL2 局部鎖頻逐 combo 檢視（Run '+b.source_run_id+'）';
         }
         li.appendChild(link);
         const countText=(v,k)=>Number.isInteger(v?.[k])&&v[k]>=0?String(v[k]):'來源未記錄';
         const lockLines=b.nl2_locked_variants.map(v=>
           'Run '+v.run_id+
           '：實測聚合節點 '+countText(v,'observed_marginal_source_nodes')+
           '／假設補值 '+countText(v,'assumed_default_source_nodes')+
           '／未匹配 '+countText(v,'unlocked_source_nodes')+
           (String(v.source_scope).includes('TURN_ONLY')?'（僅轉河牌部分鎖定）':'（部分節點鎖）'));
         li.append(document.createTextNode(
          '｜NL2 英雄 lock '+b.nl2_locked_variants.length+' 來源：'+lockLines.join('；')+
          (b.assumed_preflop_ranges?'｜翻前 169 類假設範圍，非實測 LMP 私牌':'')+
          (b.strict_full_street_combo_reachable<10?'｜警示：嚴格可達 combo 少於 10':'')+
          '｜50% pot '+(b.b50_nonpolarized_relative_equity_research_candidate
             ? '具名牌面非極化研究候選':'缺乏足夠非極化證據，不可推薦')+
          '。聚合頻率非逐牌面／逐私牌實測。'));
         ul.appendChild(li);
       }
       note.append(ul);
       const disclosure=make('strong','hu-multiboard-limits',
         '注意：CERT 僅限以上真實公牌。下方一般牌面分類的行動仍顯示 APPROX，不得認為整格已是 GTO。');
       note.append(disclosure);
     }
   }else{
     tag.textContent='APPROX 近似解';
     tag.style.background='#664814';tag.style.color='#ffe0a2';
     tag.style.padding='4px 7px';tag.style.borderRadius='5px';
     if(note)note.textContent='NL2 頻率排名 #'+item.frequency_rank+
       '（前24視為優先研究）；'+(approxReasons[item.blocked_reason]||'需要先取得完整公牌／範圍／SPR 的原始解算')+
       '。此表的下注與牌型行動屬估計值，不能視為 GTO。';
   }
 }
}
function schedule(){if(!pending){pending=true;queueMicrotask(render)}}
new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
function fetchCertifiedRegistry(){
 const open=r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();};
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
 return fetch('data/nl2_hu_multiboard_status_v28_b133_rank69.json',{cache:'no-store'}).then(open).then(v28)
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
   if(!['NL2_HU_392_MULTIBOARD_CERT_STATUS_V1','NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE','NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28','NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50','NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55','NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33','NL2_HU_392_MULTIBOARD_CERT_STATUS_V7_BATCH59','NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61','NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67','NL2_HU_392_MULTIBOARD_CERT_STATUS_V10_BATCH69','NL2_HU_392_MULTIBOARD_CERT_STATUS_V11_BATCH71','NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73','NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75','NL2_HU_392_MULTIBOARD_CERT_STATUS_V14_BATCH77','NL2_HU_392_MULTIBOARD_CERT_STATUS_V15_BATCH80','NL2_HU_392_MULTIBOARD_CERT_STATUS_V16_BATCH82','NL2_HU_392_MULTIBOARD_CERT_STATUS_V17_BATCH84','NL2_HU_392_MULTIBOARD_CERT_STATUS_V18_BATCH86','NL2_HU_392_MULTIBOARD_CERT_STATUS_V19_BATCH88','NL2_HU_392_MULTIBOARD_CERT_STATUS_V20_BATCH90','NL2_HU_392_MULTIBOARD_CERT_STATUS_V21_BATCH92','NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94','NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR','NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43','NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135','NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220'].includes(d.schema)||d.TOTAL!==392||
      d.CERT_MULTIBOARD+d.APPROX!==392||Object.keys(d.records).length!==392){
        throw Error('Certification source register failed independent count check');
   }
   registry=d;
   schedule();
 }).catch(e=>{
   console.warn('Independent model certification ledger unavailable. All unverified rows remain APPROX.',e);
 });
schedule();
})();