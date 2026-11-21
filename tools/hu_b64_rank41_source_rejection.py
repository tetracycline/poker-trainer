#!/usr/bin/env python3
"""B64 negative audit: salvaged B52 CO_BB EXP_IP is authentic but cannot certify
rank41 because it has NO strictly reachable acting-seat=IP node on GTO line.
Never weaken original actor/reach/sizing or generic 3-board certification gates.
"""
import gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
R=pathlib.Path('data')
V8=R/'nl2_hu_multiboard_status_v8_batch61.json'
B48=R/'nl2_hu_b48_next9_sourceblind_gaps.json'
GZ=R/'solver_evidence/NL2_MULTIBOARD_B52_TWO_IP_LOCKS.json.gz'
IX=R/'solver_evidence/NL2_MULTIBOARD_B52_TWO_IP_LOCKS.index.json'
OUT=R/'nl2_hu_b64_rank41_unmatched_hero_node.json'
DOC=pathlib.Path('docs/NL2_HU_B64_RANK41_REJECTION.md')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    v=json.loads(V8.read_text());frozen=json.loads(B48.read_text())
    idx=json.loads(IX.read_text())
    raw=gzip.decompress(GZ.read_bytes());proof=json.loads(raw)
    assert v['CERT_MULTIBOARD']==56 and v['APPROX']==336
    assert idx['batch']=='B52_TWO_IP_LOCKS' and idx['actual_spot_flop_version_jobs']==1
    assert idx['source_sha256']==sha(raw) and idx['gzip_sha256']==sha(GZ.read_bytes())
    assert idx['locked_cases']>=1 and len(idx['excluded_invalid_source'])==1
    assert len(proof['artifacts'])==1
    a=proof['artifacts'][0]
    assert (a['spot'],a['flop'],a['version'])==('CO_BB','8s8h3d','exp_ip')
    assert not proof['errors'] and a['cases'] and not a['errors']
    hero_nodes=[dict(turn=c['turn'],board=n['public_board'],
       line=n['exact_node_line'],actor=n['acting_seat'],
       strict=n['strictly_reachable_combos'])
       for c in a['cases'] for n in c['nodes'] if n['acting_seat']==1]
    assert not hero_nodes, 'Actual IP hero nodes unexpectedly present: evidence must be reevaluated'
    rank=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
    m=next(x for x in queue['records'] if x['model_id']=='ln-ipfr-t_model-sxr0qa')
    r=next(dict(x) for x in rank['nodes'] if x['model_id']==m['model_id'])
    assert r['rank_by_empirically_grounded_frequency_proxy']==41
    assert next(x for x in frozen['rows'] if x['rank']==41)['missing_to_three_flops']==1
    assert v['records'][m['model_id']]['label']=='APPROX'
    assert hero_seat(m['preflop_text'])==1
    r['preflop_text']=m['preflop_text'];r['abstract_action_history']=m['abstract_action_history']
    sources=[pathlib.Path(x) for x in v['source_evidence']['source_files']]
    assert GZ not in sources and all(x.is_file() for x in sources)
    exact,locked,_=build_source_index(R,sources+[GZ])
    cand,why=candidates(r,exact,locked,None)
    assert not why
    auth={x['flop'] for x in cand if x['nl2_locked_variants']}
    assert auth=={'As9h2d','Js9h4d'}, 'No unverified lock can upgrade rank41'
    incomplete=[x for x in cand if x['flop']=='8s8h3d']
    assert incomplete and all(not x['nl2_locked_variants'] for x in incomplete)
    winners,gate=choose_3_5(cand)
    assert not winners and gate=='NOT_ENOUGH_DISTINCT_AUTHENTIC_FLOPS_WITH_HERO_LOCKED_SOURCE'
    result=dict(schema='NL2_HU_B64_RANK41_TRUE_SOURCE_NEGATIVE_AUDIT_V1',
        status='PASS_EXCLUSION',rank=41,model_id=m['model_id'],
        previous_B63_failed_action_run=44811874214,
        original_b52_run_id=44809135555,
        salvaged_CO_BB_source_verified_but_not_reachable_as_hero=True,
        admitted_hero_source_boards=sorted(auth),
        unmatched_third_GTO_flop='8s8h3d',
        unmatched_line='x x/x',
        new_EXP_IP_source_hero_nodes=len(hero_nodes),
        B52_bad_SB_BB_original_source_still_rejected=True,
        no_CERT_promotion=True,CERT=56,APPROX=336,
        previous_original_count_unchanged=True,
        no_observed_private_combo_NL2_rates=True,
        never_merge=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B64 | Rank41 remains APPROX: no matching hero IP source\n\n'+
      'Original B52 completed both Rust jobs but independently rejected SB_BB focused flop extraction.\n'+
      'B62 salvaged one authentic CO_BB 8s8h3d EXP_IP subgame with SHA. It has **zero strictly matched acting-IP decision nodes** on the desired public-board line, so it is NOT a rank41 hero lock.\n'+
      'B63 independently detected exactly two valid paired GTO/hero flops: As9h2d, Js9h4d. Third 8s8h3d has GTO only.\n'+
      '**No 3-board certification, no weakened actor/SRP reach gates; V8 remains 56 CERT/336 APPROX.**\n'+
      'Source run 44809135555; failed-but-protective B63 verify run 44811874214.\n'+
      'NL2 pooled marginals are not actual private combo frequencies. PR #2 remains Draft, never merge.\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
