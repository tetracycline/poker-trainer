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
  if (base.records?.['ln-opfr-t_model-qx9t0u']?.label !== 'CERT-MULTIBOARD') return base;
  const response = await fetch('data/nl2_hu_verified_extensions.json', {cache:'no-store'});
  if (response.status === 404) return base;
  if (!response.ok) throw Error('無法讀取具名公牌來源');
  const manifest = await response.json();
  if (manifest.schema !== 'NL2_EXACT_VERIFIED_EXTENSIONS_V1' || !Array.isArray(manifest.models)) {
    throw Error('具名來源格式不符');
  }
  const records = {...base.records};
  const extensions = {};
  const digest = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
  const positive = x => Number.isSafeInteger(x) && x > 0;
  for (const e of manifest.models) {
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
  for (const item of manifest.lock_variants || []) {
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
    records[item.model_id]={...m,certified_3_to_5_exact_flop_boards:boards.map(x=>
      x===b?{...x,nl2_locked_variants:[...x.nl2_locked_variants,v]}:x)};
  }
  const models = Object.values(records);
  const cert = models.filter(m=>m.label==='CERT-MULTIBOARD').length;
  const approx = models.filter(m=>m.label==='APPROX').length;
  if (cert+approx!==392 || base.EST!==0) throw Error('模型分類總數不符');
  return {...base, records, CERT_MULTIBOARD:cert, APPROX:approx, exact_source_extensions:extensions};
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
