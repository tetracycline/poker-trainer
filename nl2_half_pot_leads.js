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
    const g=report.policies.gto,e=report.policies.exp_oop;
    const originalLock=report.original_locked_sha256||e.parent.source_sha256;
    const frozen=e.parent_version==='gto';
    if(g.parent.source_sha256!==board.source_sha256 || report.source_run!==board.source_run_id ||
       e.parent.source_sha256!==(frozen?g.parent.source_sha256:originalLock) ||
       !board.nl2_locked_variants.some(l=>l.run_id===report.source_run && l.sha256===originalLock))return false;
    if(source && source!==g.parent.source_sha256 && source!==originalLock)return false;
    return [g,e].every(p=>sha(p.source_sha256) && p.half_pot.eligible>0 && p.half_pot_reply_pairs>0 &&
      p.original_half_pot_eligible===0 && p.actions.join(' ')==='x b50' && p.half_pot.eligible<=p.legal_combos);
  }
  function showRestrictedTurn(parent,model,board,source){
    const sb=model.model_id==='ln-opfr-t_model-19esov6' && board.public_board==='2d9hAsKd';
    const utg=model.model_id==='ln-opfr-t_model-1ocorr7' && ['3d6h9sTs','3dKhAsQh'].includes(board.public_board);
    if(!sb && !utg)return;
    const slot=document.createElement('div');
    parent.appendChild(slot);
    const file=sb?'nl2_hu_b573_restricted_turn.json':'nl2_hu_b575_delayed_cbet.json';
    fetch('data/'+file,{cache:'no-store'}).then(response=>{
      if(!response.ok)throw Error('HTTP '+response.status);
      return response.json();
    }).then(data=>{
      const report=sb?data:data.records.find(r=>r.public_board===board.public_board);
      if(!report || !matchRestrictedTurn(report,model,board,source))return;
      const g=report.policies.gto,e=report.policies.exp_oop;
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
          ' 組可下半池，其中 '+p.half_pot.middle_count+' 組屬中段勝率。'+(p.half_pot.candidate?'符合非極化研究門檻。':'未達非極化研究門檻。');
        details.appendChild(para);
      }
      const para=document.createElement('p'),rate=e.response;
      const scope=sb?'大盲面對 34% 至 55% 底池的轉牌再下注':'CO 面對延遲持續下注（樣本涵蓋各尺寸）';
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
  globalThis.nl2HalfPotLeads={load,match,matchFrozenRiver,matchRestrictedTurn,showRestrictedTurn,reachReport,showBoard,showLock};
})();
