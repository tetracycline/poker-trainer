// Bind a conditional turn subgame to the specific baseline board and original pair of sources.
(() => {
  let request;
  const sha=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
  async function readReport(file){
    const response=await fetch('data/'+file,{cache:'no-store'});
    if(response.status===404)return [];
    if(!response.ok)throw Error('HTTP '+response.status);
    const report=await response.json();
    if(report.schema!=='NL2_HU_B492_CONDITIONAL_HALF_POT_LEADS_V1'||!Array.isArray(report.records))
      throw Error('半池領打對照資料格式不符');
    return report.records;
  }
  function load(){
    request??=Promise.all(['nl2_hu_b492_half_pot_leads.json','nl2_hu_b493_half_pot_leads.json','nl2_hu_b500_half_pot_leads.json'].map(readReport))
      .then(groups=>groups.flat()).catch(error=>{request=undefined;throw error;});
    return request;
  }
  function match(rows,model,original){
    const hits=rows.filter(r=>r.model_id===model.model_id && r.public_board===original.public_board &&
      r.line===original.actual_exact_action_line && r.seat===original.acting_seat &&
      r.original_gto_run===original.source_run_id && r.original_gto_sha256===original.source_sha256 &&
      original.nl2_locked_variants.some(v=>v.run_id===r.original_lock_run && v.sha256===r.original_lock_sha256));
    if(hits.length>1)throw Error('同一具名決策有重複的領打對照');
    if(!hits.length)return null;
    const row=hits[0];
    if(row.status!=='BOTH_POSITIVE'){
      if(!['ZERO_JOINT_REACH','UNAVAILABLE'].includes(row.status))throw Error('未知的對照解算結果');
      return row;
    }
    const b=row.board,p=row.pin,g=row.gto,e=row.exp_oop;
    if(!b || !p || !g || !e || g.version!=='gto' || e.version!=='exp_oop' ||
       b.flop!==original.flop || b.turn!==original.turn || b.public_board!==original.public_board ||
       b.actual_exact_action_line!==original.actual_exact_action_line || b.exact_flop_action!==original.exact_flop_action ||
       b.acting_seat!==0 || b.actual_spr!==original.actual_spr || !b.exact_node_actions.includes('b50') ||
       b.actual_pot_bb!==original.actual_pot_bb || b.actual_effective_stack_bb!==original.actual_effective_stack_bb ||
       g.original_run_id!==row.original_gto_run || e.original_run_id!==row.original_lock_run ||
       g.original_source_sha256!==row.original_gto_sha256 || e.original_source_sha256!==row.original_lock_sha256 ||
       row.source_run_id!==g.source_run_id || e.source_run_id!==g.source_run_id ||
       b.source_run_id!==g.source_run_id || b.source_sha256!==g.source_sha256 || !sha(b.source_sha256) ||
       b.nl2_locked_variants?.length!==1 || b.nl2_locked_variants[0].sha256!==e.source_sha256 ||
       b.nl2_locked_variants[0].run_id!==e.source_run_id || b.nl2_locked_variants[0].version!=='exp_oop' ||
       !sha(e.source_sha256) || p.original_GTO_SHA256!==g.source_sha256 || p.actual_NL2_SHA256!==e.source_sha256 ||
       p.source_run_id!==b.source_run_id || p.public_board!==b.public_board || !sha(p.viewer_sha256) ||
       p.archive_sha256!==g.raw_sha256 || p.locked_original_archive_sha256!==e.raw_sha256 ||
       p.GTO_strict_combos!==g.strict_legal_combos || p.NL2_strict_combos!==e.strict_legal_combos ||
       p.GTO_compatible_hole_card_pairs!==g.compatible_hole_card_pairs || p.NL2_compatible_hole_card_pairs!==e.compatible_hole_card_pairs ||
       !/^[A-Za-z0-9_]+$/.test(p.viewer_archive_code||'') ||
       [g,e].some(v=>v.status!=='POSITIVE_JOINT_REACH'||v.public_board!==b.public_board||v.line!==b.actual_exact_action_line||
          v.acting_seat!==0|| !v.source_actions.includes('b50')||!Number.isSafeInteger(v.strict_legal_combos)||
          v.strict_legal_combos<=0||v.compatible_hole_card_pairs<v.strict_legal_combos))
      throw Error('半池領打對照與原始牌面、座位或求解來源不符');
    return row;
  }
  function reachReport(model,row){
    const key=v=>JSON.stringify([model.model_id,row.public_board,row.line,row.seat,v.source_run_id,v.source_sha256]);
    return {references:{[key(row.exp_oop)]:row.exp_oop},gto_references:{[key(row.gto)]:row.gto}};
  }
  function showLock(parent,row){
    const lock=row.exp_oop;
    const rates=lock.checked_lock_patterns?.marginal_targets;
    if(!rates)return;
    const details=document.createElement('details'), title=document.createElement('summary');
    title.textContent='子局實際套用的 NL2 玩家池鎖頻';
    details.appendChild(title);
    const pct=n=>(100*n).toLocaleString('zh-TW',{maximumFractionDigits:2})+'%';
    for(const [pattern,target] of Object.entries(rates)){
      const applied=lock.applied_rust_rates?.[pattern];
      if(!applied?.nodes)continue;
      const bucket=/by_size\[([^\]]+)\]$/.exec(target.source)?.[1];
      const action=bucket?'面對 '+bucket+' 底池下注':'下注後面對加注';
      const item=document.createElement('p');
      item.textContent=['翻牌','轉牌','河牌'][target.street-1]+' '+action+'，'+target.n.toLocaleString('zh-TW')+
        ' 次池決策。棄牌／加注的實測目標為 '+pct(target.fold_target)+'／'+pct(target.raise_target)+
        '，求解器在 '+applied.nodes+' 個節點實際套用 '+pct(applied.actual_fold)+'／'+pct(applied.actual_aggression)+'。';
      details.appendChild(item);
    }
    parent.appendChild(details);
  }
  function matchFrozenRiver(report,model,board,prior){
    if(report.model_id!==model.model_id || report.public_board!==board.public_board ||
       report.line!==board.actual_exact_action_line || report.seat!==board.acting_seat ||
       report.original_run!==board.source_run_id || report.policies?.gto?.original.original_source_sha256!==board.source_sha256 ||
       !board.nl2_locked_variants.some(v=>v.run_id===report.original_run && v.version==='exp_oop' &&
         v.sha256===report.policies?.exp_oop?.original.original_source_sha256))return null;
    const {gto,exp_oop:locked}=report.policies;
    if(report.schema!=='NL2_HU_B561_FROZEN_RIVER_V1' || report.scope!=='CONDITIONAL_RIVER_WITH_ROUNDED_ORIGINAL_TURN_POLICIES' ||
       !prior || prior.status!==report.full_turn_status || prior.status!=='ZERO_JOINT_REACH' ||
       prior.source_run_id!==report.full_turn_alternative_run || prior.exp_oop.compatible_hole_card_pairs!==0 ||
       report.pot_bb!==board.actual_pot_bb || report.stack_bb!==board.actual_effective_stack_bb ||
       !Number.isSafeInteger(report.run) || report.run<=0 || !sha(report.driver_patch_sha256) ||
       report.pool?.source!=='NL2.HU_facing_bet[3].by_size[34-55%]' || !sha(report.pool.sha256) ||
       report.pool.n!==64272 || locked.river_reply?.nodes!==1 ||
       !Number.isFinite(locked.river_reply.fold) || !Number.isFinite(locked.river_reply.agg) ||
       !(locked.hero_gap_pct>=0 && locked.hero_gap_pct<=.1) ||
       Math.abs(locked.river_reply.fold-report.pool.fold/100)>0.00001 ||
       Math.abs(locked.river_reply.agg-report.pool.raise/100)>0.00001)
      throw Error('河牌子局來源或對手回應不符');
    for(const v of [gto,locked]){
      if(!sha(v.output_sha256) || !sha(v.input_sha256) || v.actions.join()!=='x,b50' ||
         !(v.compatible_pairs>=v.half_pot_pairs && v.half_pot_pairs>0 && v.gto_gap_pct>=0 && v.gto_gap_pct<=.1) ||
         v.hands.length!==v.strict_legal_combos || v.hands.reduce((n,h)=>n+h.compatible_pairs,0)!==v.compatible_pairs ||
         v.hands.reduce((n,h)=>n+((h.accepted_mask&2)?h.compatible_pairs:0),0)!==v.half_pot_pairs ||
         v.hands.filter(h=>h.accepted_mask&2).length!==v.b50.eligible || v.b50.candidate ||
         v.hands.some(h=>!Number.isFinite(h.frequencies.b50) || h.frequencies.b50<0 || h.frequencies.b50>1))
        throw Error('河牌半池逐手策略與配牌不符');
    }
    return report;
  }
  async function showFrozenRiver(parent,model,board,prior){
    const response=await fetch('data/nl2_hu_b561_frozen_river.json',{cache:'no-store'});
    if(response.status===404)return;
    if(!response.ok)throw Error('HTTP '+response.status);
    const row=matchFrozenRiver(await response.json(),model,board,prior);
    if(!row)return;
    const details=document.createElement('details'),title=document.createElement('summary');
    title.textContent='固定原轉牌策略後的河牌半池領打';
    details.appendChild(title);
    const text=s=>{const p=document.createElement('p');p.textContent=s;details.appendChild(p);};
    text('此子局沿用原翻牌範圍，以及原始檔保留至小數四位的逐手轉牌行動頻率。河牌先手可過牌或下注 50% 底池。');
    for(const [label,v] of [['GTO',row.policies.gto],['NL2',row.policies.exp_oop]]){
      text(label+' 在 '+v.strict_legal_combos+' 個合格手牌組合中，有 '+v.b50.eligible+' 個接受半池，涵蓋 '+v.half_pot_pairs+' 組雙方配牌。'+
        '符合半池的手牌數低於非極化研究門檻。');
      text(label+' 逐手半池頻率　'+v.hands.map(h=>h.hand+' '+(100*h.frequencies.b50).toFixed(1)+'%').join('、'));
    }
    const l=row.policies.exp_oop.river_reply;
    text('對手面對河牌 34–55% 底池下注的 NL2 樣本共 '+row.pool.n.toLocaleString('zh-TW')+
      ' 次。此子局鎖定的棄牌率為 '+(100*l.fold).toFixed(1)+'%，加注率為 '+(100*l.agg).toFixed(1)+'%。可用加注尺寸為全下。');
    const reply=row.policies.exp_oop.strict_reply_frequencies;
    text('按可達手牌與半池領打頻率加權後，對手棄牌 '+(100*reply.f).toFixed(1)+'%、跟注 '+
      (100*reply.c).toFixed(1)+'%、全下 '+(100*reply.a).toFixed(1)+'%。');
    const link=document.createElement('a');
    link.href='https://github.com/tetracycline/poker-trainer/actions/runs/'+row.run;
    link.textContent='河牌子局的原始解、輸入與稽核';
    details.appendChild(link);
    parent.appendChild(details);
  }
  function matchRestrictedTurn(report,model,board,source){
    if(report.model_id!==model.model_id || report.public_board!==board.public_board ||
       report.line!==board.actual_exact_action_line || report.seat!==board.acting_seat)return false;
    const version=report.seat?'exp_ip':'exp_oop';
    const g=report.policies.gto,e=report.policies[version];
    const originalLock=report.original_locked_sha256||e.parent.source_sha256;
    const lockRun=report.original_locked_run??report.source_run;
    const frozen=e.parent_version==='gto';
    if(g.parent.source_sha256!==board.source_sha256 || report.source_run!==board.source_run_id ||
       e.parent.source_sha256!==(frozen?g.parent.source_sha256:originalLock) ||
       !board.nl2_locked_variants.some(l=>l.run_id===lockRun && l.sha256===originalLock && l.version===version))return false;
    if(source && source!==g.parent.source_sha256 && source!==originalLock)return false;
    return [g,e].every(p=>sha(p.source_sha256) && Number.isSafeInteger(p.half_pot.eligible) && p.half_pot.eligible>=0 &&
      Number.isSafeInteger(p.half_pot_reply_pairs) && p.half_pot_reply_pairs>=0 && p.legal_combos>0 &&
      p.half_pot_reply_pairs<=p.compatible_pairs && (p.half_pot_reply_pairs>0)===(p.half_pot.eligible>0) &&
      p.original_half_pot_eligible===0 && p.actions.join(' ')==='x b50' && p.half_pot.eligible<=p.legal_combos);
  }
  const frozenRiverBoards=new Map([
    ['ln-opfr-r_model-1e6gydx','3d7hAsKd3s'],['ln-iso-lmp_r_model-vlgh2t','2d4h4s8s5c'],
    ['ln-3bp-3b_r_model-1bgfa05','2d7hKs9d5s'],['ln-ipfr-r_model-1cbkgix','8dQhAsKh9s'],
    ['ln-ipc-r_model-vvxn9n','4dQhKsTc4c']
  ]);
  function recoveredPolicy(previous,row,extra){
    if(!extra || previous.status!=='UNRESOLVED_ROUNDED_BOUNDARY')return previous;
    if(extra.schema!=='NL2_HU_B587_RAW_RIVER_RANGE_RECOVERY_V1')throw Error('河牌權重來源格式不符');
    const recovered=extra.records.find(x=>x.model_id===row.model_id && x.public_board===row.public_board &&
      x.line===row.line && x.seat===row.seat && x.policy.original.source_sha256===previous.original.source_sha256);
    if(!recovered)return previous;
    const p=recovered.policy;
    if(p.original.version!==previous.original.version || p.original.run!==previous.original.run ||
       p.original.archive_sha256!==previous.original.archive_sha256 || p.status!=='VERIFIED' ||
       p.prior_unresolved_output_sha256!==previous.output_sha256 || !sha(p.raw_weights_sha256) ||
       !sha(p.raw_turn_output_sha256) || !(p.original_node_count>0) ||
       !p.range_errors.every(e=>e.max_abs===0 && e.relative_sum===0))throw Error('原始河牌範圍來源不符');
    return p;
  }
  function matchingFrozenPolicies(report,model,board,source,extra){
    const row=report.records.find(r=>r.model_id===model.model_id && r.public_board===board.public_board &&
      r.line===board.actual_exact_action_line && r.seat===board.acting_seat &&
      r.pot_bb===board.actual_pot_bb && r.stack_bb===board.actual_effective_stack_bb);
    if(!row || report.schema!=='NL2_HU_B583_ORIGINAL_POLICY_FROZEN_RIVERS_V1')return [];
    const originals=[{version:'gto',run_id:board.source_run_id,sha256:board.source_sha256},...board.nl2_locked_variants];
    return row.policies.map(p=>recoveredPolicy(p,row,extra)).filter(p=>(!source || p.original.source_sha256===source) &&
      originals.some(o=>o.version===p.original.version && o.run_id===p.original.run && o.sha256===p.original.source_sha256));
  }
  function showFrozenPolicies(parent,model,board,source){
    if(frozenRiverBoards.get(model.model_id)!==board.public_board)return;
    const slot=document.createElement('div');
    parent.appendChild(slot);
    const read=name=>fetch('data/'+name,{cache:'no-store'}).then(r=>{
      if(!r.ok)throw Error('HTTP '+r.status);
      return r.json();
    });
    const hasRecovery=model.frequency_rank===71 || model.frequency_rank===159;
    Promise.all([read('nl2_hu_b583_frozen_rivers.json'),hasRecovery?read('nl2_hu_b587_raw_river_weights.json'):null])
    .then(([report,extra])=>{
      const policies=matchingFrozenPolicies(report,model,board,source,extra);
      if(!policies.length)return;
      const details=document.createElement('details'),summary=document.createElement('summary');
      summary.textContent='沿用原策略抵達河牌後的半池對照';
      details.appendChild(summary);
      const add=text=>{const p=document.createElement('p');p.textContent=text;details.appendChild(p);};
      add(board.acting_seat?'沿用原翻牌、轉牌與河牌先手過牌頻率，重算後手決策。':'沿用原翻牌與轉牌頻率，重算河牌先手決策。');
      for(const p of policies){
        const label=p.original.version==='gto'?'GTO':'NL2 鎖 '+p.original.run;
        if(p.status==='UNRESOLVED_ROUNDED_BOUNDARY'){
          add(label+' 的原始頻率取位誤差超出範圍核對門檻。');continue;
        }
        if(p.status!=='VERIFIED' || !sha(p.output_sha256) || p.hands.length!==p.legal_combos ||
           p.hands.filter(h=>h.accepted_mask&2).length!==p.b50.eligible ||
           p.hands.reduce((n,h)=>n+h.compatible_pairs,0)!==p.compatible_pairs ||
           p.hands.reduce((n,h)=>n+((h.accepted_mask&2)?h.compatible_pairs:0),0)!==p.half_pot_pairs)
          throw Error('河牌逐手結果與配牌數不符');
        if(p.raw_weights_sha256)add(label+' 的 '+p.original_node_count+' 個原始節點已完整重現。重新匯出的雙方逐手範圍均與原解吻合。');
        const menu=p.actions.includes('a')?'過牌、半池或全下':'過牌或半池';
        add(label+' 可選'+menu+'。'+p.b50.eligible+' / '+p.legal_combos+' 組手牌可以下半池，涵蓋 '+
          p.half_pot_pairs.toLocaleString('zh-TW')+' 組雙方配牌。'+(p.b50.candidate?'符合非極化研究門檻。':'未達非極化研究門檻。'));
        if(p.b50.eligible){
          const hands=p.hands.filter(h=>h.accepted_mask&2).map(h=>h.hand+' '+(100*h.b50).toFixed(1)+'%');
          add(label+' 逐手半池頻率　'+hands.join('、'));
        }
        if(p.applied_reply){
          add('單挑河牌面對 34% 至 55% 底池下注的樣本共 '+report.response.n.toLocaleString('zh-TW')+
            ' 次。本子局對手面對半池時，實際鎖定棄牌 '+(100*p.applied_reply.fold).toFixed(1)+'%、加注 '+
            (100*p.applied_reply.agg).toFixed(1)+'%。');
        }
      }
      slot.appendChild(details);
    }).catch(()=>{slot.textContent='目前無法核對河牌半池對照來源。';});
  }
  async function showMatchedBarrels(parent,model,board,source){
    const name={
      'ln-ipfr-t_model-1ktwuv7':'nl2_hu_b640_rank36_barrels.json',
      'ln-ipfr-t_model-1u5hox2':'nl2_hu_b640_rank37_barrels.json',
      'ln-ipfr-t_model-1xz5oyp':'nl2_hu_b640_rank38_barrels.json',
      'ln-ipfr-t_model-dzbacd':'nl2_hu_b640_rank39_barrels.json',
      'ln-ipfr-t_model-1h05w49':'nl2_hu_b640_rank59_barrels.json',
      'ln-ipfr-t_model-hxdit':'nl2_hu_b640_rank60_barrels.json',
      'ln-ipfr-t_model-qpx6tn':'nl2_hu_b640_rank61_barrels.json',
      'ln-iso-lmp_t_model-19hfq8v':'nl2_hu_b638_rank1_barrels.json',
      'ln-iso-lmp_t_model-1e9jvm0':'nl2_hu_b638_rank7_barrels.json',
      'ln-opfr-t_model-19esov6':'nl2_hu_b594_rank2_barrels.json',
      'ln-opfr-t_model-1wej9w5':'nl2_hu_b590_rank3_barrels.json',
      'ln-opfr-t_model-trdt3w':'nl2_hu_b594_rank4_barrels.json',
      'ln-opfr-t_model-id38uf':'nl2_hu_b596_rank5_barrels.json',
      'ln-3bp-3c_t_model-1oebhk7':'nl2_hu_b632_rank131_barrels.json',
      'ln-3bp-3b_t_model-6vpmec':'nl2_hu_b632_rank82_barrels.json',
      'ln-3bp-3b_t_model-n5cvfv':'nl2_hu_b632_rank120_barrels.json',
      'ln-3bp-3b_t_model-1fvksvd':'nl2_hu_b630_rank42_barrels.json',
      'ln-3bp-3b_t_model-1gg0bw':'nl2_hu_b628_rank19_barrels.json',
      'ln-bb-t_model-1n6d5u3':'nl2_hu_b609_rank6_barrels.json',
      'ln-opfr-t_model-1hmsxaw':'nl2_hu_b603_rank30_barrels.json',
      'ln-opfr-t_model-1xzqrwx':'nl2_hu_b606_rank31_barrels.json',
      'ln-opfr-t_model-qx9t0u':'nl2_hu_b606_rank32_barrels.json',
      'ln-opfr-t_model-1ocorr7':'nl2_hu_b606_rank33_barrels.json'
    }[model.model_id];
    if(!name || (source && source!==board.source_sha256))return;
    const slot=document.createElement('div');
    parent.appendChild(slot);
    try{
      const response=await fetch('data/'+name,{cache:'no-store'});
      if(!response.ok)throw Error('HTTP '+response.status);
      const report=await response.json();
      const probe=['BTN_BB','CO3_BTN'].includes(model.solver_profile);
      const threeBet=model.family==='3BP';
      const ipBarrel=board.acting_seat===1;
      const limped=model.solver_profile==='LMP_CO_BB';
      if(report.schema!==(ipBarrel?'NL2_HU_B640_IP_TURN_BARRELS_V1':limped?'NL2_HU_B638_LIMPED_TURN_RESPONSES_V1':threeBet?'NL2_HU_B628_3BP_TURN_BARREL_RESPONSES_V1':probe?'NL2_HU_B609_BB_PROBE_RESPONSES_V1':'NL2_HU_B590_SB_BB_BARREL_REPLIES_V1'))throw Error('來源格式不符');
      const row=report.records.find(r=>r.model_id===model.model_id && r.public_board===board.public_board &&
        r.line===board.actual_exact_action_line && r.seat===board.acting_seat && r.original.version==='gto' &&
        r.original.run===board.source_run_id && r.original.source_sha256===board.source_sha256 &&
        r.pot_bb===board.actual_pot_bb && r.stack_bb===board.actual_effective_stack_bb);
      if(!row)return;
      const checked=row.line==='x x/';
      const fullPot=board.exact_node_actions.includes('b100');
      const ruleCount=ipBarrel?2:checked||limped?1:threeBet?(fullPot?2:1):4;
      const rateTable=limped?'HU_facing_bet[2].by_pot[limped]':probe?'vs_probe':'vs_delayed_cbet';
      if(!sha(row.output_sha256) || !sha(row.job_sha256) || !sha(report.archive_sha256) ||
         !(row.locked.legal_combos>0 && row.locked.compatible_pairs>=row.locked.legal_combos) ||
         row.locked.legal_combos!==row.gto.legal_combos || row.locked.compatible_pairs!==row.gto.compatible_pairs ||
         row.rules.length!==ruleCount || ((checked||limped) && row.rules[0].table!==rateTable) || !row.rules.every(r=>r.n>0 && r.applied_nodes>0))throw Error('來源核對失敗');
      const details=document.createElement('details');
      const summary=document.createElement('summary');
      const blindOrCO={BB3_BTN:'大盲',SB3_BTN:'小盲',CO3_BTN:'CO'};
      const actors=threeBet?[blindOrCO[model.solver_profile],'按鈕位']:probe?['大盲','按鈕位']:model.solver_profile==='UTG_CO'?['UTG','CO']:['小盲','大盲'];
      const ipName=model.solver_profile==='CO_BB'?'CO':'按鈕位';
      summary.textContent=ipBarrel?ipName+' 轉牌再次下注的大盲尺寸回應鎖':limped?'單挑未加注底池的大盲轉牌下注與 CO 回應鎖':threeBet?actors[0]+'三次加注底池的轉牌'+(probe?'探測下注':checked?'延遲持續下注':'下注')+'與按鈕位回應鎖':probe?'大盲轉牌探測下注的按鈕位回應鎖':checked?actors[0]+' 延遲持續下注的 '+actors[1]+' 回應鎖':actors[0]+' 連續下注的轉牌及河牌尺寸鎖';
      details.appendChild(summary);
      const add=text=>{const p=document.createElement('p');p.textContent=text;details.appendChild(p);};
      const turnChoices=fullPot?'半池、滿池或全下':'半池或全下';
      const lockedSizes=fullPot?'半池或滿池':'半池';
      add(threeBet&&!checked?'沿用原 GTO 翻牌範圍。轉牌可過牌、下'+turnChoices+'。只在對手面對轉牌'+lockedSizes+'時套用實測回應。':'沿用原 GTO 翻牌範圍。轉牌可過牌、下半池或滿池。');
      for(const [name,p] of [['原 GTO',row.gto],['實測回應鎖',row.locked]]){
        const mid=p.half_pot.middle_count??0;
        add(name+' 的半池合格手牌有 '+p.half_pot.eligible+' / '+p.legal_combos+
          ' 組，其中 '+mid+' 組屬中段勝率。'+(p.half_pot.candidate?'符合非極化研究門檻。':'未達非極化研究門檻。'));
        const hands=Object.entries(p.eligible_hand_frequencies);
        if(hands.length!==p.half_pot.eligible || hands.some(([h,f])=>!/^([2-9TJQKA][cdhs]){2}$/.test(h) ||
            !Number.isFinite(f) || f<0 || f>1))throw Error('逐手半池頻率核對失敗');
        if(hands.length){
          const group=document.createElement('details'),title=document.createElement('summary'),list=document.createElement('p');
          title.textContent=name+' 的逐手半池頻率';
          list.textContent=hands.map(([h,f])=>h+' '+(100*f).toFixed(1)+'%').join('、');
          group.appendChild(title);group.appendChild(list);details.appendChild(group);
        }
      }
      for(const r of row.rules){
        const street=r.table==='vs_turn_barrel_by_size'?'轉牌':'河牌';
        const scope=limped?'單挑未加注底池面對轉牌下注，各位置和尺寸合計':checked?actors[1]+' 面對'+(probe?'探測下注':'延遲持續下注')+'，各下注尺寸合計':street+'面對 '+r.size+' 底池的下注';
        add(scope+'，共 '+r.n.toLocaleString('zh-TW')+' 次。棄牌 '+r.fold+
          '%、跟注 '+r.call+'%、加注 '+r.raise+'%。');
      }
      if(ipBarrel)add('翻牌持續下注獲跟注，轉牌由大盲過牌。實測樣本涵蓋單挑、單次加注底池中，面對位置內翻前加注者轉牌再次下注的回應。鎖定轉牌半池與滿池的回應，河牌自由求解。');
      else if(limped)add('此模型沿用 CO 跛入、大盲過牌的假設翻前範圍。實測回應的樣本涵蓋所有單挑未加注底池。');
      else add('實測樣本合併單挑、'+(threeBet?'三次加注':'單次加注')+'底池中翻前加注者在位置'+(probe?'內':'外')+'的對局。');
      if(checked||limped)add('此子局將同一組合併樣本頻率分別套用到半池與滿池回應。河牌保留自由求解。');
      slot.appendChild(details);
    }catch{slot.textContent='目前無法核對連續下注的鎖頻資料。';}
  }
  function showRestrictedTurn(parent,model,board,source){
    showMatchedBarrels(parent,model,board,source);
    showFrozenPolicies(parent,model,board,source);
    const sb=model.model_id==='ln-opfr-t_model-19esov6' && board.public_board==='2d9hAsKd';
    const utg=model.model_id==='ln-opfr-t_model-1ocorr7' && ['3d6h9sTs','3dKhAsQh'].includes(board.public_board);
    const barrel=model.model_id==='ln-opfr-t_model-1hmsxaw' && board.public_board==='4dQhKsTc';
    const limp=model.model_id==='ln-iso-lmp_t_model-17z0wyl' && board.public_board==='3d6h9sTs';
    if(!sb && !utg && !barrel && !limp)return;
    const slot=document.createElement('div');
    parent.appendChild(slot);
    const file=sb?'nl2_hu_b573_restricted_turn.json':utg?'nl2_hu_b575_delayed_cbet.json':'nl2_hu_b578_conditional_turns.json';
    fetch('data/'+file,{cache:'no-store'}).then(response=>{
      if(!response.ok)throw Error('HTTP '+response.status);
      return response.json();
    }).then(data=>{
      const report=sb?data:data.records.find(r=>r.public_board===board.public_board);
      if(!report || !matchRestrictedTurn(report,model,board,source))return;
      const g=report.policies.gto,e=report.policies[report.seat?'exp_ip':'exp_oop'];
      const details=document.createElement('details'),title=document.createElement('summary');
      title.textContent='比較轉牌只開放過牌或半池下注的解';details.appendChild(title);
      if(e.parent_version==='gto'){
        const note=document.createElement('p');
        note.textContent='兩個限尺寸子局均沿用原 GTO 翻牌範圍。NL2 鎖從轉牌開始。';
        details.appendChild(note);
      }
      for(const [name,p] of [['GTO',g],['NL2',e]]){
        const para=document.createElement('p');
        para.textContent=name+' 原樹半池合格手牌 '+p.original_half_pot_eligible+' 組。限尺寸子局有 '+p.half_pot.eligible+' / '+p.legal_combos+
          ' 組可下半池，其中 '+(p.half_pot.middle_count??0)+' 組屬中段勝率。'+(p.half_pot.candidate?'符合非極化研究門檻。':'未達非極化研究門檻。');
        const hands=Object.entries(p.eligible_hand_frequencies??{});
        if(hands.length)para.textContent+=' 合格手牌及下注頻率為 '+hands.map(([h,f])=>h+' '+(f*100).toFixed(1)+'%').join('、')+'。';
        details.appendChild(para);
      }
      const para=document.createElement('p'),rate=e.response;
      const scope=utg?'CO 面對延遲持續下注（樣本涵蓋各尺寸）':limp?'單挑玩家池面對 34% 至 55% 底池的轉牌下注':
        (sb?'大盲':'CO')+' 面對 34% 至 55% 底池的轉牌再下注';
      para.textContent=scope+'共 '+rate.n.toLocaleString('zh-TW')+' 次。半池回應鎖定棄牌 '+rate.fold_pct+
        '%、跟注 '+rate.call_pct+'%、加注 '+rate.raise_pct+'%。';
      details.appendChild(para);slot.appendChild(details);
    }).catch(()=>{slot.textContent='目前無法讀取轉牌限尺寸對照解。';});
  }
  function showBoard(parent,model,board){
    if(board.exact_node_actions.includes('b50'))return showRestrictedTurn(parent,model,board);
    const line=document.createElement('div');parent.appendChild(line);
    if(board.actual_spr<.5){
      line.textContent='剩餘有效籌碼不足半個底池。';return;
    }
    showFrozenPolicies(parent,model,board);
    load().then(rows=>{
      const r=match(rows,model,board);
      if(!r)return;
      if(r.status==='BOTH_POSITIVE'){
        const link=document.createElement('a');
        link.href='nl2-multiboard.html?'+new URLSearchParams({model:model.model_id,board:board.public_board,tree:'half-pot',version:'gto',sha:r.gto.source_sha256});
        link.textContent='比較開放半池領打後的 GTO 與 NL2 鎖頻逐手解';
        line.appendChild(link);
      }else line.textContent=r.status==='ZERO_JOINT_REACH'?'從轉牌重新求解時，這條線沒有合格的雙方配牌。':'本牌面尚缺完整的半池領打對照解。';
      if(r.status==='ZERO_JOINT_REACH' && r.rank===71)
        return showFrozenRiver(parent,model,board,r);
    }).catch(()=>{line.textContent='半池領打對照來源暫時無法核對。';});
  }
  globalThis.nl2HalfPotLeads={load,match,matchFrozenRiver,matchRestrictedTurn,showRestrictedTurn,showMatchedBarrels,matchingFrozenPolicies,showFrozenPolicies,reachReport,showBoard,showLock};
})();
