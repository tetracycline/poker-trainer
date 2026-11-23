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
          !/^[A-Za-z0-9_]+$/.test(pin.viewer_archive_code || '') ||
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
  const models = Object.values(records);
  const cert = models.filter(m=>m.label==='CERT-MULTIBOARD').length;
  const approx = models.filter(m=>m.label==='APPROX').length;
  if (cert+approx!==392 || base.EST!==0) throw Error('模型分類總數不符');
  return {...base, records, CERT_MULTIBOARD:cert, APPROX:approx, exact_source_extensions:extensions};
};
