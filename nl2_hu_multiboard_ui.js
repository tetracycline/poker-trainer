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
 return fetch('data/nl2_hu_multiboard_status_v48_b390_rank107.json',{cache:'no-store'}).then(open).then(v48b390)
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
   if(!['NL2_HU_392_MULTIBOARD_CERT_STATUS_V1','NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE','NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28','NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50','NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55','NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33','NL2_HU_392_MULTIBOARD_CERT_STATUS_V7_BATCH59','NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61','NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67','NL2_HU_392_MULTIBOARD_CERT_STATUS_V10_BATCH69','NL2_HU_392_MULTIBOARD_CERT_STATUS_V11_BATCH71','NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73','NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75','NL2_HU_392_MULTIBOARD_CERT_STATUS_V14_BATCH77','NL2_HU_392_MULTIBOARD_CERT_STATUS_V15_BATCH80','NL2_HU_392_MULTIBOARD_CERT_STATUS_V16_BATCH82','NL2_HU_392_MULTIBOARD_CERT_STATUS_V17_BATCH84','NL2_HU_392_MULTIBOARD_CERT_STATUS_V18_BATCH86','NL2_HU_392_MULTIBOARD_CERT_STATUS_V19_BATCH88','NL2_HU_392_MULTIBOARD_CERT_STATUS_V20_BATCH90','NL2_HU_392_MULTIBOARD_CERT_STATUS_V21_BATCH92','NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94','NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR','NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43','NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135','NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B390_RANK107','NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27','NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96','NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79','NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71','NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR','NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60','NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46','NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61','NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313','NL2_HU_392_MULTIBOARD_CERT_STATUS_V39_B247_RANK30','NL2_HU_392_MULTIBOARD_CERT_STATUS_V38_B206_RANK190','NL2_HU_392_MULTIBOARD_CERT_STATUS_V37_B205_RANK188','NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159','NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201','NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202','NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138','NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80','NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150','NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47','NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88','NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69','NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_236'].includes(d.schema)||d.TOTAL!==392||
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