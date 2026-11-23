// Source-paired evidence required by both NL2 training views.
globalThis.nl2ValidateRank45 = function validateRank45(registry) {
  const records = Object.values(registry.records || {});
  const model = registry.records?.['ln-iso-iso_t_model-1x553s3'];
  const evidence = registry.B463_rank45_three_true_original_GTO_NL2_OOP_flops;
  const boards = model?.certified_3_to_5_exact_flop_boards || [];
  const sha = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
  if (registry.schema !== 'NL2_HU_392_MULTIBOARD_CERT_STATUS_V52_B463_R45' ||
      records.length !== 392 || registry.TOTAL !== 392 || registry.EST !== 0 ||
      registry.CERT_MULTIBOARD !== 165 || registry.APPROX !== 227 ||
      records.filter(r => r.label === 'CERT-MULTIBOARD').length !== 165 ||
      records.filter(r => r.label === 'APPROX').length !== 227 ||
      model?.frequency_rank !== 45 || model.solver_profile !== 'ISO_BTN_CO' ||
      model.label !== 'CERT-MULTIBOARD' || model.proven_exact_board_count !== 3 ||
      registry.records['ln-opfr-t_model-qx9t0u']?.label !== 'CERT-MULTIBOARD' ||
      registry.no_generic_texture_GTO !== true || registry.PR2_remains_draft_never_merge !== true ||
      evidence?.rank !== 45 || evidence.actor !== 'CO_OOP' || evidence.spot !== model.solver_profile ||
      evidence.line !== 'x x/' || evidence.pins?.length !== 3 || boards.length !== 3 ||
      boards.map(b => b.flop).sort().join(',') !== '7s5h3d,8s8h3d,AsKh3d') {
    throw Error('rank45 registry or exact board coverage mismatch');
  }
  for (const board of boards) {
    const pin = evidence.pins.find(p => p.flop === board.flop && p.turn === board.turn);
    const lock = board.nl2_locked_variants?.find(v => v.version === 'exp_oop');
    if (!pin || !lock || board.acting_seat !== 0 || board.actual_exact_action_line !== evidence.line ||
        !Number.isSafeInteger(pin.source_run_id) || pin.source_run_id <= 0 ||
        pin.source_run_id !== board.source_run_id || pin.source_run_id !== lock.run_id ||
        !sha(pin.original_GTO_SHA256) || pin.original_GTO_SHA256 !== board.source_sha256 ||
        !sha(pin.actual_NL2_SHA256) || pin.actual_NL2_SHA256 !== lock.sha256 ||
        !Number.isInteger(pin.GTO_strict_combos) || pin.GTO_strict_combos <= 0 ||
        board.strict_full_street_combo_reachable !== pin.GTO_strict_combos ||
        !Number.isInteger(pin.NL2_strict_combos) || pin.NL2_strict_combos <= 0 ||
        !(board.actual_spr > 0) || !(board.relative_spr_error_pct >= 0 && board.relative_spr_error_pct <= 5) ||
        !(board.genuine_gto_exploitability_pct >= 0 && board.genuine_gto_exploitability_pct <= 0.5)) {
      throw Error('rank45 GTO or actor-matched NL2 source mismatch');
    }
  }
  return registry;
};

// Exact-source additions are independent of older immutable registry snapshots.
globalThis.nl2ApplyVerifiedExtensions = async function applyVerifiedExtensions(base) {
  if (base.records?.['ln-opfr-t_model-qx9t0u']?.label !== 'CERT-MULTIBOARD') throw Error('基礎資料未達雙方可達性稽核版本');
  const response = await fetch('data/nl2_hu_verified_extensions.json', {cache:'no-store'});
  if (!response.ok) throw Error('無法讀取具名公牌來源');
  const manifest = await response.json();
  if (manifest.schema !== 'NL2_EXACT_VERIFIED_EXTENSIONS_V1' || !Array.isArray(manifest.models) || !manifest.board_reach_updates || !Array.isArray(manifest.reverified_models)) {
    throw Error('具名來源格式不符');
  }
  const records = {...base.records};
  for (const [id,route] of Object.entries(manifest.trainer_route_contract?.routes || {})) {
    if (route.priced_model_spr === undefined) continue;
    if (!records[id] || !Number.isFinite(route.priced_model_spr) || route.priced_model_spr <= 0 ||
        !/^x? ?b[1-9]\d* c$/.test(route.streets[0])) throw Error('翻牌跟注的來源尺寸或 SPR 不符');
    records[id] = {...records[id],assumed_model_node_spr:route.priced_model_spr};
  }
  const extensions = {};
  const digest = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
  const positive = x => Number.isSafeInteger(x) && x > 0;
  function promote(e) {
    const m = records[e.model_id];
    if (!m || m.label !== 'APPROX' || e.rank !== m.frequency_rank || !Array.isArray(e.boards) ||
        e.boards.length < 3 || e.boards.length > 5 || e.pins?.length !== e.boards.length ||
        new Set(e.boards.map(b=>b.flop)).size !== e.boards.length) throw Error('具名牌面數或模型不符');
    for (const b of e.boards) {
      const pin = e.pins.find(p=>p.flop===b.flop && p.turn===b.turn && p.public_board===b.public_board);
      const lock = b.nl2_locked_variants?.[0];
      if (!pin || !lock || b.nl2_locked_variants.length !== 1 || ![0,1].includes(b.acting_seat) ||
          !/^[A-Za-z0-9_]+$/.test(pin.viewer_archive_code || '') || !digest(pin.viewer_sha256) ||
          (lock.run_id!==b.source_run_id && (!/^[A-Za-z0-9_]+$/.test(pin.locked_viewer_archive_code || '') ||
            !digest(pin.locked_viewer_sha256))) ||
          !digest(b.source_sha256) || b.source_sha256!==pin.original_GTO_SHA256 ||
          !digest(lock.sha256) || lock.sha256!==pin.actual_NL2_SHA256 ||
          lock.version!==(b.acting_seat===0?'exp_oop':'exp_ip') ||
          !positive(b.source_run_id) || !positive(lock.run_id) ||
          !positive(pin.GTO_strict_combos) || !positive(pin.NL2_strict_combos) ||
          b.strict_full_street_combo_reachable!==pin.GTO_strict_combos ||
          b.model_assumed_spr!==m.assumed_model_node_spr ||
          !(Math.abs(b.actual_spr/b.model_assumed_spr-1)<=0.05) ||
          !(b.genuine_gto_exploitability_pct>=0 && b.genuine_gto_exploitability_pct<=0.5) ||
          !(lock.true_hero_gap_pct>=0 && lock.true_hero_gap_pct<=0.5)) throw Error('具名公牌可達範圍、SPR 或解算來源不符');
    }
    records[e.model_id] = {...m, label:'CERT-MULTIBOARD', blocked_reason:null,
      proven_exact_board_count:e.boards.length, certified_3_to_5_exact_flop_boards:e.boards};
    extensions[e.model_id] = e.pins;
  }
  for (const e of manifest.models) promote(e);
  function appendLock(item, reachUpdates) {
    const m=records[item.model_id], v=item.lock;
    if(m?.label!=='CERT-MULTIBOARD') throw Error('附加鎖頻缺少原始認證模型');
    const boards=m.certified_3_to_5_exact_flop_boards;
    const b=boards.find(x=>x.flop===item.flop && x.turn===item.turn && x.public_board===item.public_board &&
      x.actual_exact_action_line===item.line && x.acting_seat===item.acting_seat);
    if(!b || b.source_run_id!==item.gto_run || b.source_sha256!==item.gto_sha256 ||
       !b.nl2_locked_variants.some(x=>x.run_id===item.parent_lock_run && x.sha256===item.parent_lock_sha256) ||
       b.nl2_locked_variants.some(x=>x.sha256===v?.sha256) || v?.version!==(b.acting_seat?'exp_ip':'exp_oop') ||
       !positive(v.run_id) || !positive(v.strictly_reachable_combos) || !digest(v.sha256) || !digest(v.viewer_sha256) ||
       !/^[A-Za-z0-9_]+$/.test(v.viewer_archive_code||'') || !Number.isFinite(v.true_hero_gap_pct) || v.true_hero_gap_pct<0 || v.true_hero_gap_pct>.5)
      throw Error('附加鎖頻的公牌、原始 GTO 或獨立求解來源不符');
    if(v.requires_native_joint_replay){
      const replay=reachUpdates[item.model_id]?.find(r=>r.public_board===b.public_board &&
        r.line===b.actual_exact_action_line && r.seat===b.acting_seat && r.gto_run===b.source_run_id && r.gto_sha256===b.source_sha256);
      const lock=replay?.locks.find(l=>l.run_id===v.run_id && l.sha256===v.sha256);
      if(!positive(replay?.gto?.strictly_reachable_combos) || !lock || lock.strictly_reachable_combos!==v.strictly_reachable_combos ||
         !positive(lock.subgame_applied_rust_lock_nodes))throw Error('附加鎖頻缺少雙方可達的原始下注選單或實際套鎖證據');
    }
    records[item.model_id]={...m,certified_3_to_5_exact_flop_boards:boards.map(x=>
      x===b?{...x,nl2_locked_variants:[...x.nl2_locked_variants,v]}:x)};
  }
  const variants=manifest.lock_variants || [];
  for(const item of variants){
    if(!item.after_reverification) appendLock(item, manifest.board_reach_updates);
  }
  function applyReplays(changes){
    for (const [id, updates] of Object.entries(changes)) {
      const m=records[id];
      if(m?.label!=='CERT-MULTIBOARD') throw Error('可達性重算缺少原始認證模型');
      const key=(board,line,seat)=>JSON.stringify([board,line,seat]);
      const byBoard=new Map(updates.map(r=>[key(r.public_board,r.line,r.seat),r]));
      if(byBoard.size!==updates.length) throw Error('公牌可達性來源重複');
      const kept=[];
      for(const board of m.certified_3_to_5_exact_flop_boards){
        const k=key(board.public_board,board.actual_exact_action_line,board.acting_seat);
        const row=byBoard.get(k);
        if(!row){kept.push(board);continue;}
        byBoard.delete(k);
        if(row.gto_run!==board.source_run_id || row.gto_sha256!==board.source_sha256) throw Error('原始 GTO 來源不符');
        const valid=v=>typeof v==='object' && v!==null && positive(v.run_id) && digest(v.sha256) &&
          Number.isSafeInteger(v.strictly_reachable_combos) && v.strictly_reachable_combos>=0 &&
          Number.isSafeInteger(v.compatible_hole_card_pairs) && v.compatible_hole_card_pairs>=v.strictly_reachable_combos &&
          Boolean(v.compatible_hole_card_pairs)===Boolean(v.strictly_reachable_combos) &&
          Number.isSafeInteger(v.medium_50pct_eligible_combos) && v.medium_50pct_eligible_combos>=0 &&
          v.medium_50pct_eligible_combos<=v.strictly_reachable_combos &&
          typeof v.b50_nonpolarized_relative_equity_research_candidate==='boolean' &&
          (!v.b50_nonpolarized_relative_equity_research_candidate || v.medium_50pct_eligible_combos>=20);
        const validScope=v=>{
          if(!('root_applied_rust_lock_nodes' in v) && !('subgame_applied_rust_lock_nodes' in v))return true;
          return [v.root_applied_rust_lock_nodes,v.subgame_applied_rust_lock_nodes].every(n=>Number.isSafeInteger(n)&&n>=0) &&
            v.root_applied_rust_lock_nodes+v.subgame_applied_rust_lock_nodes>0;
        };
        const unresolved=v=>v && positive(v.run_id) && digest(v.sha256) && typeof v.unresolved_reason==='string' &&
          v.unresolved_reason.trim().length>0 && !('strictly_reachable_combos' in v) && !('compatible_hole_card_pairs' in v);
        if(!Array.isArray(row.locks) || (!row.locks.length && row.gto==null) || !row.locks.every(v=>unresolved(v)||(valid(v)&&validScope(v))) ||
          (row.gto!==null && (!(valid(row.gto)||unresolved(row.gto)) || row.gto.sha256!==row.gto_sha256 || row.gto.run_id!==row.gto_run))) {
          throw Error('原始組合或半池證據不符');
        }
        const byLock=new Map(row.locks.map(v=>[v.run_id+'/'+v.sha256,v]));
        if(byLock.size!==row.locks.length) throw Error('重複的鎖頻重算來源');
        const locks=[];
        for(const lock of board.nl2_locked_variants){
          const lockKey=lock.run_id+'/'+lock.sha256, result=byLock.get(lockKey);
          if(!result){locks.push(lock);continue;}
          byLock.delete(lockKey);
          if(result.strictly_reachable_combos) locks.push({...lock,...result});
        }
        if(byLock.size) throw Error('重算缺少原始鎖頻決策');
        if(!locks.length || unresolved(row.gto) || row.gto?.strictly_reachable_combos===0) continue;
        const b={...board,nl2_locked_variants:locks};
        if(row.gto){
          b.strict_full_street_combo_reachable=row.gto.strictly_reachable_combos;
          b.compatible_hole_card_pairs=row.gto.compatible_hole_card_pairs;
          b.medium_50pct_eligible_combos=row.gto.medium_50pct_eligible_combos;
          b.b50_nonpolarized_relative_equity_research_candidate=row.gto.b50_nonpolarized_relative_equity_research_candidate;
        }
        kept.push(b);
      }
      if(byBoard.size) throw Error('可達性重算與目前牌面不符');
      const updated={...m,proven_exact_board_count:kept.length,certified_3_to_5_exact_flop_boards:kept};
      if(kept.length<3) Object.assign(updated,{label:'APPROX',blocked_reason:'FEWER_THAN_THREE_FLOPS_AFTER_TWO_SEAT_REPLAY',
        certified_3_to_5_exact_flop_boards:[],remaining_exact_board_evidence:kept});
      records[id]=updated;
    }
  }
  const contract = manifest.trainer_route_contract;
  const schema = 'NL2_HU_RENDERED_ACTION_ROUTES_V1';
  if (contract?.schema !== schema || !contract.routes || Object.keys(contract.routes).length !== 392 ||
      !Array.isArray(manifest.trainer_route_exclusions)) throw Error('缺少訓練表行動與下注尺寸證據');
  const excluded = new Set();
  const boardKey = b => JSON.stringify([b.flop,b.public_board,b.source_run_id,b.source_sha256]);
  const active = m => m.label === 'CERT-MULTIBOARD' ? m.certified_3_to_5_exact_flop_boards : m.remaining_exact_board_evidence || [];
  function actualTexture(publicBoard) {
    const cards=publicBoard.match(/../g);
    const ranks=cards.map(c=>c[0]), suits=cards.map(c=>c[1]);
    if (suits.some(s=>suits.filter(v=>v===s).length>=3)) return 'mono';
    if (new Set(ranks).size<ranks.length) return 'paired';
    if (ranks.includes('A')) return 'A_high';
    if (ranks.some(r=>'KQ'.includes(r))) return 'KQ_high';
    return ranks.some(r=>'JT'.includes(r)) ? 'mid_high' : 'low';
  }
  function reviewedRowsAllow(route, board) {
    const pins=route.reviewed_partial_sources;
    if (pins===undefined) return true;
    if (!Array.isArray(pins) || !Array.isArray(route.visible_street_rows)) throw Error('具名公牌缺少各街路徑資料');
    const reviewed=pins.some(p=>p.public_board===board.public_board && p.line===board.actual_exact_action_line &&
      p.seat===board.acting_seat && p.run===board.source_run_id && p.gto_sha256===board.source_sha256);
    return !reviewed || route.visible_street_rows.every(step=>{
      const texture=actualTexture(board.public_board.slice(0,4+2*step.street));
      return Array.isArray(step.visible[texture]) && step.visible[texture].length>0;
    });
  }
  function applyRoutes() {
    for (const [id,m] of Object.entries(records)) {
      const route = contract.routes[id];
      if (!route || ![0,1].includes(route.seat) || !Array.isArray(route.streets) || route.streets.length !== m.street+1 ||
          !route.streets.every(s=>typeof s==='string' && s.split(' ').every(t=>/^(?:|x|c|bet|raise|overbet|b[1-9][0-9]*)$/.test(t)))) {
        throw Error('訓練表尺寸或行動順序資料缺失');
      }
      if ((id==='ln-ipfr-r_model-1iypoop') !== (route.requires_three_suited_turn===true)) throw Error('轉牌過牌路徑缺少單色牌面條件');
      const before=active(m);
      const kept=before.filter(b=>{
        const actual=b.actual_exact_action_line.split('/');
        const suits=[b.public_board[1],b.public_board[3],b.public_board[5],b.public_board[7]];
        const turnAllowed=!route.requires_three_suited_turn || suits.some(s=>suits.filter(v=>v===s).length>=3);
        const match=turnAllowed && reviewedRowsAllow(route,b) && route.seat===b.acting_seat && actual.length===route.streets.length && actual.every((street,i)=>{
          const played=street.split(' ').filter(Boolean);
          const expected=route.streets[i].split(' ').filter(Boolean);
          return played.length===expected.length && played.every((v,j)=>{
            const t=expected[j];
            if(t==='bet')return /^b[1-9][0-9]*$/.test(v) || v==='a';
            if(t==='overbet')return v==='a' || (/^b[0-9]+$/.test(v) && Number(v.slice(1))>100);
            if(t==='raise')return /^r[0-9]*$/.test(v) || v==='a';
            return t===v;
          });
        });
        if(!match) excluded.add(JSON.stringify([id,b.public_board,b.actual_exact_action_line,b.acting_seat,b.source_run_id,b.source_sha256]));
        return match;
      });
      if(kept.length===before.length)continue;
      if(kept.length>=3){
        records[id]={...m,proven_exact_board_count:kept.length,certified_3_to_5_exact_flop_boards:kept};
      }else{
        records[id]={...m,label:'APPROX',blocked_reason:'FEWER_THAN_THREE_FLOPS_AFTER_RENDERED_ACTION_ROUTE_CHECK',
          proven_exact_board_count:kept.length,certified_3_to_5_exact_flop_boards:[],remaining_exact_board_evidence:kept};
      }
    }
  }
  applyReplays(manifest.board_reach_updates);
  applyRoutes();
  for(const repair of manifest.reverified_models){
    if(!repair.pins.every(p=>positive(p.GTO_compatible_hole_card_pairs) && p.GTO_compatible_hole_card_pairs>=p.GTO_strict_combos &&
      positive(p.NL2_compatible_hole_card_pairs) && p.NL2_compatible_hole_card_pairs>=p.NL2_strict_combos)) throw Error('缺少雙方合法配牌');
    promote(repair);
    delete records[repair.model_id].remaining_exact_board_evidence;
  }
  const repairedIds=new Set(manifest.reverified_models.map(m=>m.model_id));
  const repairUpdates=manifest.reverified_board_reach_updates || {};
  for(const item of variants){
    if(!item.after_reverification) continue;
    if(!repairedIds.has(item.model_id)) throw Error('附加鎖頻缺少重新驗證的模型');
    appendLock(item, repairUpdates);
  }
  applyReplays(repairUpdates);
  applyRoutes();
  const recorded=new Set(manifest.trainer_route_exclusions.map(x=>JSON.stringify([x.model_id,x.public_board,x.actual_line,x.acting_seat,x.run,x.sha256])));
  if(recorded.size!==manifest.trainer_route_exclusions.length || recorded.size!==excluded.size ||
     ![...excluded].every(key=>recorded.has(key)))throw Error('訓練表尺寸排除清單與具名公牌不符');
  for(const [id,pins] of Object.entries(extensions)){
    const keys=new Set(active(records[id]).map(boardKey));
    const kept=pins.filter(p=>keys.has(JSON.stringify([p.flop,p.public_board,p.source_run_id,p.original_GTO_SHA256])));
    if(kept.length)extensions[id]=kept;else delete extensions[id];
  }
  const models = Object.values(records);
  const cert = models.filter(m=>m.label==='CERT-MULTIBOARD').length;
  const approx = models.filter(m=>m.label==='APPROX').length;
  if (cert+approx!==392 || base.EST!==0) throw Error('模型分類總數不符');
  return {...base, records, CERT_MULTIBOARD:cert, APPROX:approx, exact_source_extensions:extensions, trainer_route_contract_schema:schema};
};

globalThis.nl2ValidateRank218 = function validateRank218(registry) {
  const record = registry.records?.['ln-ipfr-r_model-h0c7q7'];
  const evidence = registry.B465_rank218_four_original_sources;
  const withRank45 = !!registry.B463_rank45_three_true_original_GTO_NL2_OOP_flops;
  const count = withRank45 ? 166 : 165;
  const records = Object.values(registry.records || {});
  const boards = record?.certified_3_to_5_exact_flop_boards || [];
  if (registry.schema !== 'NL2_HU_392_MULTIBOARD_CERT_STATUS_V53_B465_R218' ||
      registry.TOTAL !== 392 || registry.EST !== 0 || records.length !== 392 ||
      registry.CERT_MULTIBOARD !== count || registry.APPROX !== 392-count ||
      records.filter(r => r.label === 'CERT-MULTIBOARD').length !== count ||
      records.filter(r => r.label === 'APPROX').length !== 392-count ||
      registry.records['ln-iso-iso_t_model-1x553s3']?.label !== (withRank45 ? 'CERT-MULTIBOARD' : 'APPROX') ||
      registry.records['ln-ipfr-r_model-7kv23r']?.label !== 'APPROX' ||
      registry.records['ln-opfr-t_model-qx9t0u']?.label !== 'CERT-MULTIBOARD' ||
      record?.label !== 'CERT-MULTIBOARD' || record.frequency_rank !== 218 || record.solver_profile !== 'CO_BB' ||
      record.proven_exact_board_count !== 4 || boards.length !== 4 ||
      boards.map(b=>b.flop).sort().join(',') !== '7c6h5d,Js9h4d,Js9h5d,Td8h3c' ||
      evidence?.rank !== 218 || evidence.actor !== 'CO_IP' || evidence.line !== 'x b50 c/x b50 c/x' ||
      evidence.model_flop_bet_fraction !== 0.5 || evidence.model_turn_bet_fraction !== 0.5 ||
      evidence.pins?.length !== 4 || evidence.excluded_model?.rank !== 216) {
    throw Error('rank218 model size, source coverage or registry mismatch');
  }
  const sha = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
  for (const board of boards) {
    const pin = evidence.pins.find(p => p.flop === board.flop && p.turn === board.turn && p.public_board === board.public_board);
    const lock = board.nl2_locked_variants?.find(v => v.version === 'exp_ip');
    if (!pin || !lock || board.acting_seat !== 1 || board.actual_exact_action_line !== evidence.line ||
        !Number.isSafeInteger(pin.original_GTO_run) || pin.original_GTO_run <= 0 || pin.original_GTO_run !== board.source_run_id ||
        !Number.isSafeInteger(pin.actual_NL2_IP_run) || pin.actual_NL2_IP_run <= 0 || pin.actual_NL2_IP_run !== lock.run_id ||
        !sha(pin.original_GTO_SHA256) || pin.original_GTO_SHA256 !== board.source_sha256 ||
        !sha(pin.actual_NL2_SHA256) || pin.actual_NL2_SHA256 !== lock.sha256 ||
        !Number.isInteger(pin.GTO_strict_combos) || pin.GTO_strict_combos <= 0 ||
        board.strict_full_street_combo_reachable !== pin.GTO_strict_combos ||
        !Number.isInteger(pin.NL2_strict_combos) || pin.NL2_strict_combos <= 0 ||
        !(board.actual_spr > 0) || !(board.relative_spr_error_pct >= 0 && board.relative_spr_error_pct <= 5) ||
        !(board.genuine_gto_exploitability_pct >= 0 && board.genuine_gto_exploitability_pct <= 0.5)) {
      throw Error('rank218 board GTO or actor-matched NL2 source mismatch');
    }
  }
  return registry;
};
