#!/usr/bin/env python3
"""B232 classify zero-match cause for pinned authentic B231 GTO/EXP on rank71.
Keep original Rust raw source independent of the strict 40%/70% reachable mask.
"""
import argparse,collections,gzip,hashlib,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_sequential_cfr_reach import game_reach
ROOT=pathlib.Path(__file__).resolve().parents[1];D=ROOT/'data'
LINE='b50 c/x b50 c/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',type=pathlib.Path,required=True)
    ap.add_argument('--new',type=pathlib.Path,required=True)
    a=ap.parse_args()
    pin=json.loads((D/'nl2_hu_b216_rank71_lmp_9s8h4d_gto_parent_pin.json').read_text())
    ix=json.loads((D/'solver_evidence/NL2_MULTIBOARD_B231_R71_9S8H4D_DONK50_PAIR.index.json').read_text())
    assert ix['schema']=='NL2_MULTIBOARD_B231_EXACT_SHA_GTO_PLUS_PARTIAL_NL2_DONK50_V1'
    assert ix['paired_exact_line_actor_SPR_reach'] is False
    assert ix['upstream_original_B216_run_id']==44884042851
    assert ix['original_parent_pin_sha256']==sha(D/'nl2_hu_b216_rank71_lmp_9s8h4d_gto_parent_pin.json')
    assert ix['new_river_donk']=='50%' and ix['rank']==71 and ix['flop']=='9s8h4d'
    parent=a.parent.resolve()/'solver/postflop/out/LMP_CO_BB/gto/9s8h4d_multiboard.json'
    assert sha(parent)==pin['original_gto_root_sha256']
    root=json.loads(parent.read_text())
    new=a.new.resolve()/'solver/postflop/out/LMP_CO_BB'
    report=[]
    for ver in ('gto','exp_oop'):
        p=D/'solver_evidence'/f'NL2_MULTIBOARD_B231_R71_9S8H4D_DONK50_{ver.upper()}.json.gz'
        assert sha(p)==ix['records'][ver]['gzip_sha256']
        raw=gzip.decompress(p.read_bytes())
        assert hashlib.sha256(raw).hexdigest()==ix['records'][ver]['raw_sha256']
        data=json.loads(raw)
        jobpath=new/ver/'9s8h4d_b50c_Ah.job.json'
        assert jobpath.is_file()
        job=json.loads(jobpath.read_text())
        assert sha(jobpath)==ix['records'][ver]['job_sha256']
        assert job['river_donk']=='50%' and job['pot']>0
        if ver=='gto':assert job.get('hero') is None and not job.get('locks')
        else:assert job['hero']==0 and job.get('locks')
        seq,stats=game_reach(root,data)
        rows=[]
        for n in data['nodes']:
            seat=n['player'];board=n['board']
            key='|'.join((board,n['line'],str(seat)))
            before=sum(float(w)>1e-4 for w in n['w'][seat])
            after=seq[key]['count']
            assert before>=after
            rows.append(dict(line=n['line'],actor_seat=seat,public_board=board,
                original_source_actor_combos=before,strict_after_previous_actions=after,
                parent_actor_decisions=seq[key]['parent_actor_decisions'],
                actions=n['acts'],pot_bb=n['pot']/100,
                spr=round((data['stack']-max(n['bets']))/n['pot'],5)))
        target=[z for z in rows if z['line']==LINE and z['actor_seat']==0 and len(z['public_board'])==10]
        found_target=len(target)>0
        before=sum(z['original_source_actor_combos'] for z in target)
        after=sum(z['strict_after_previous_actions'] for z in target)
        assert after==0, 'Expected B231 prior strict zero; this is a changed source that must be separately reconciled'
        prefix=[z for z in rows if z['line'].startswith('b50 c/x b50 c') and len(z['public_board'])==10]
        all_actor=collections.Counter((len(z['public_board']),z['actor_seat']) for z in rows)
        all_line=collections.Counter((z['line'],z['actor_seat']) for z in rows)
        reason=('TARGET_DECISION_ABSENT_FROM_RUST_EXTRACTED_NODES' if not found_target else
            'TARGET_EXISTS_BUT_SOURCE_0_COMBOS' if before==0 else
            'TARGET_SOURCE_COMBOS_REMOVED_BY_40_70_PREVIOUS_ACTION_GATE')
        out=dict(version=ver,actual_Rust_nodes=len(rows),
            native_actor_boardlen_counts={str(k):v for k,v in all_actor.items()},
            exact_line_actor_counts=[dict(line=k[0],actor=k[1],raw_nodes=v)
                for k,v in sorted(all_line.items())],
            target_original_node_exists=found_target,
            target_original_actor_node_count=len(target),
            target_original_source_combos=before,
            target_strict_reachable_combos=after,
            diagnostic_reason=reason,
            target_nodes=target,
            nearest_pot_action_prefixes=prefix[:30],
            sample_available_OOP_river=[z for z in rows if z['actor_seat']==0 and len(z['public_board'])==10][:20],
            reach_stats=dict(stats))
        assert after==ix['records'][ver]['river_target_strict_combos']
        report.append(out)
    status=D/'nl2_hu_multiboard_status_v38_b206_rank190.json'
    original=json.loads(status.read_text())
    assert (original['CERT_MULTIBOARD'],original['APPROX'],original['EST'])==(151,241,0)
    assert original['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    doc=dict(schema='NL2_HU_B232_B231_RIVER_DONK50_RAW_VS_STRICT_ROOTCAUSE_V1',
        original_B216_GTO_root_sha256=sha(parent),
        B231_source_index_sha256=sha(D/'solver_evidence/NL2_MULTIBOARD_B231_R71_9S8H4D_DONK50_PAIR.index.json'),
        strict_filter="maximum action, or >=40% and >=70% of highest; intersect all actor's prior actions",
        verified_true_original_GTO_and_separate_partial_NL2_lock=True,
        B231_exact_target_no_valid_CERT=True,source_results=report,
        CERT_MULTIBOARD=151,APPROX=241,EST=0,TOTAL=392,
        V38_status_sha256=sha(status),no_invented_NL2_private_combo_frequencies=True,
        PR2_Draft_NEVER_MERGE=True)
    (D/'nl2_hu_b232_b231_original_vs_strict_actor_reach.json').write_text(json.dumps(doc,indent=2)+'\n')
    lines=['# B232: B231 authentic GTO vs NL2 river-donk50 actor/line zero-combo root cause','',
        'B216 original full GTO flop remains SHA-fixed, LMP 169-class preflop ranges ASSUMED.',
        'B231 true GTO and NL2 partially locked turn/river differ from original river tree by a preregistered 50%-pot donk option.',
        'Full per-combo ancestry uses the maximum-frequency action or alternative >=40% and >=70% of the highest; never silently relax this gate.','']
    for z in report:
        lines.extend([f"## {z['version']}",
            f"Rust nodes {z['actual_Rust_nodes']}, raw correct actor target nodes {z['target_original_actor_node_count']}, "
            f"source combos {z['target_original_source_combos']}, strict combos {z['target_strict_reachable_combos']}.",
            f"Diagnostic: **{z['diagnostic_reason']}**.",''])
    lines+=['See JSON for all exact lines, seats and nearest turn-to-river nodes.',
        'No source data was fabricated or relabeled as measured conditional NL2 hand frequencies.',
        'B232 is a diagnostic checkpoint, not a new solve or a third certified flop.',
        'V38 151 CERT/241 APPROX/0 EST unchanged; all 581 existing locks and HU 2475/2475 must pass.',
        'PR #2 stays Draft, NEVER MERGE.','']
    pathlib.Path('docs/NL2_HU_B232_REAL_RIVER_DONK50_GTO_VS_STRICT_NODE_REACH.md').write_text('\n'.join(lines))
    print('PASS B232 strict actor rootcause',json.dumps([{k:z[k] for k in
        ('version','diagnostic_reason','target_original_actor_node_count','target_original_source_combos')}
        for z in report]))
if __name__=='__main__':main()
