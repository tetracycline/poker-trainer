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
