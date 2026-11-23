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
    request??=Promise.all(['nl2_hu_b492_half_pot_leads.json','nl2_hu_b493_half_pot_leads.json'].map(readReport))
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
  function showBoard(parent,model,board){
    if(board.exact_node_actions.includes('b50'))return;
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
      }else line.textContent=r.status==='ZERO_JOINT_REACH'?'半池領打重算在這條線沒有合格的雙方配牌。':'本牌面尚缺完整的半池領打對照解。';
    }).catch(()=>{line.textContent='半池領打對照來源暫時無法核對。';});
  }
  globalThis.nl2HalfPotLeads={load,match,reachReport,showBoard,showLock};
})();
