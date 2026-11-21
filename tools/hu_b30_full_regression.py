#!/usr/bin/env python3
"""Immutable all-streets NL2 navigation + full CERT proof regression.

No GTO labeling outside frozen exact named boards. Only 24/392 high-frequency
models certified. This script compares independent JS HU link and reach
analyses with source-verified exact GTO/partial lock provenance and b50 policy.
"""
import collections,hashlib,json,pathlib

DATA=pathlib.Path('data')
AUDIT=pathlib.Path('audit')
OUT=DATA/'nl2_hu_b30_full_integrity.json'
MD=pathlib.Path('docs/NL2_HU_B30_FULL_INTEGRITY.md')

def load(name):
    return json.loads(name.read_text())
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    reg_path=DATA/'nl2_hu_multiboard_status.json'
    matrix_path=DATA/'nl2_hu_cert_lock_medium_matrix.json'
    gate_path=DATA/'nl2_hu_cert_ui_completeness_gate.json'
    reg=load(reg_path);matrix=load(matrix_path);gate=load(gate_path)
    links=load(AUDIT/'link.json')
    reach=load(AUDIT/'reach.json')
    model=load(AUDIT/'model-path.json')
    contract=load(AUDIT/'hu-contract.json')
    assert reg['CERT_MULTIBOARD']==24 and reg['APPROX']==368 and reg['TOTAL']==392
    assert len(reg['records'])==392
    assert matrix['CERT_MULTIBOARD']==24 and matrix['APPROX']==368
    assert gate['cert_models']==24 and gate['approx_models']==368
    assert gate['named_board_coverage']=='88/88'
    assert gate['node_lock_source_coverage']=='99/99'
    assert gate['b50_nonpolarized_research_candidate_boards']==35
    assert gate['b50_evidence_not_supported']==53
    counts=links['counts']
    assert counts['continuing']>0 and counts['continuing']==counts['reachRiver']
    assert counts.get('noRiver',0)==0
    assert not links.get('misses') and not links.get('unresolvedCells')
    assert not reach['violations'] and reach['counts']['violations']==0
    assert model['coverage']==100 and not model['violations']
    assert model['stats']['modelTables']==392
    assert not contract['errors'] and contract['stats']['tables']>0
    allcert=[r for r in reg['records'].values() if r['label']=='CERT-MULTIBOARD']
    assert len(allcert)==24 and {r['frequency_rank'] for r in allcert}==set(range(1,25))
    thin=[]
    source_locks=[]
    n_boards=0
    for m in allcert:
        for b in m['certified_3_to_5_exact_flop_boards']:
            n_boards+=1
            assert b['nl2_locked_variants'] and b['strict_full_street_combo_reachable']>0
            if b['strict_full_street_combo_reachable']<10:
                thin.append(dict(rank=m['frequency_rank'],model_id=m['model_id'],
                    flop=b['flop'],turn=b['turn'],strict_combos=b['strict_full_street_combo_reachable']))
            for lock in b['nl2_locked_variants']:
                assert len(lock['sha256'])==64 and lock['run_id']>0
                source_locks.append(lock)
    assert n_boards==88 and len(source_locks)==99
    a=matrix['strict_aggregate']
    assert a['hero_lock_variants']==99
    assert a['named_board_proofs']==88
    assert a['b50_research_candidate_boards']==35
    unknown=[(model_key,b) for model_key,b in ((r['model_id'],x)
        for r in allcert for x in r['certified_3_to_5_exact_flop_boards'])
        if any(lock['observed_marginal_source_nodes'] is None
            for lock in b['nl2_locked_variants'])]
    assert len(unknown)==gate['counts']['unknown_legacy_lock_variants']
    report=dict(
      schema='TASK_HYBRID_B30_FROZEN_HU_NAV_CERT_LOCK_FULL_REGRESSION_V1',
      source_file_sha256={str(path):digest(path)
        for path in (reg_path,matrix_path,gate_path)},
      prereg_top24_certified=24,not_preregistered_approx=368,EST=0,
      navigation=dict(continuing=counts['continuing'],reach_river=counts['reachRiver'],
        share_pct=counts['riverShare'],missing_river=counts.get('noRiver',0),
        independent_model_route_coverage_pct=model['coverage'],
        independent_model_route_count=model['stats']['modelTables'],
        link_misses=len(links.get('misses',[])),
        reach_violations=reach['counts']['violations'],
        modeled_path_violations=len(model['violations']),
        hu_contract_errors=len(contract['errors'])),
      exact_board_coverage=dict(named_boards=n_boards,matched_hero_lock_source_variants=len(source_locks),
        b50_nonpolarized_research_candidates=a['b50_research_candidate_boards'],
        b50_unsupported=n_boards-a['b50_research_candidate_boards'],
        low_strict_reach_less_than10=thin,
        old_lock_provenance_unknown=len(unknown),
        observed_pool_marginal_pattern_nodes=a['observed_marginal_pattern_nodes'],
        assumed_default_pattern_nodes=a['assumed_pattern_nodes'],
        unmatched_villain_nodes=a['unmatched_opponent_nodes']),
      hard_limits=dict(
        generic_texture_may_not_be_called_GTO=True,
        old_legacy_sources_with_unknown_counts_not_fabricated=True,
        observed_NL2_pool_marginal_not_per_private_card_conditional=True,
        assumed_LMP_169_class_ranges_not_observed_NL2=True,
        missing_b50_nonpolarized_proof_not_a_bet_recommendation=True,
        frozen_certification_rules_untouched=True),
      PR_2_remains_draft_and_never_merge=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    MD.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      '# NL2 392 MODEL：B30 跨街導航＋具名 GTO／鎖頻／50% 下注完整回歸驗證','',
      f'分類：**24 CERT-MULTIBOARD／368 APPROX／0 EST**。前 24 個高頻模型均僅在 3–5 張具名牌面取得來源認證。','',
      f"河牌導航：**{counts['reachRiver']}/{counts['continuing']}（{counts['riverShare']}%）**。模型行動線表格：{model['stats']['modelTables']} 張；獨立路徑覆蓋 {model['coverage']}%；違規 0。",'',
      f'來源精確配對：**{n_boards}/88 張具名牌面，{len(source_locks)}/99 組英雄端局部 lock**。',
      f"其中 50% 底池非極化研究候選 {a['b50_research_candidate_boards']} 張、證據不足 {n_boards-a['b50_research_candidate_boards']} 張。",
      f'歷史來源未記錄逐節點統計：{len(unknown)} 筆；其數值維持未知，不代入 0 或聲稱觀測。',
      f'嚴格可達 combo 少於 10 的牌面：{len(thin)} 張。','',
      '來源的 NL2 聚合頻率不等於逐私牌、逐牌面、逐行動歷史的實測行為。',
      'LMP 的 50% 單尺寸限制樹與 169-class 假設起始範圍不等於完整 NL2 GTO。',
      '本次只做完整回歸驗證，不重寫原始 GTO、CERT 規則、排序或其他 APPROX。',
      'PR #2 必須維持 Draft／Open，絕不 merge。','',
      '來源檔 SHA-256：','']
    lines.extend('- '+k+': \`'+v+'\`' for k,v in report['source_file_sha256'].items())
    MD.write_text('\n'.join(lines)+'\n')
    print('PASS B30: 24 CERT / 368 APPROX; river',counts['reachRiver'],
          '/',counts['continuing'],'source boards 88 / 88; hero lock 99 / 99')
if __name__=='__main__':main()
