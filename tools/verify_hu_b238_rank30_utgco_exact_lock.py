#!/usr/bin/env python3
"""B238 independently verify a genuine Rust UTG_CO rank30 KsQh4d actor-OOP
partially locked turn/river child from SHA-pinned original B235 GTO flop.
Use full sequential per-combo reach and real SPR. No generic CERT or
unobserved NL2 hole-card conditional rates.
"""
import argparse,gzip,hashlib,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_sequential_cfr_reach import game_reach
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data';SPOT='UTG_CO';FLOP='KsQh4d';TURN='Tc';LINE='b50 c/'
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for piece in iter(lambda:f.read(1024*1024),b''):h.update(piece)
    return h.hexdigest()
def load(path):return json.loads(path.read_text())
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=pathlib.Path,required=True)
    p.add_argument('--fresh',type=pathlib.Path,required=True)
    a=p.parse_args()
    pin_path=D/'nl2_hu_b235_rank30_utgco_KsQh4d_gto_parent_pin.json'
    index_path=D/'solver_evidence/NL2_MULTIBOARD_B235_R30_KSQH4D_GTO.index.json'
    parent_sha=D/'solver_evidence/NL2_MULTIBOARD_B235_R30_KSQH4D_GTO.json.gz'
    pin=load(pin_path);idx=load(index_path)
    assert pin['source_run_id']==idx['run_id']==44894369547
    assert (pin['target_rank'],pin['model_id'],pin['spot'],pin['flop'],pin['turn'])==(
        30,'ln-opfr-t_model-1hmsxaw',SPOT,FLOP,TURN)
    assert pin['preflop_CFR_pinned_not_observed_NL2_private_card'] is True
    assert pin['direct_nl2_lock_source_present'] is False
    assert idx['source_sha256']==hashlib.sha256(gzip.decompress(parent_sha.read_bytes())).hexdigest()
    assert idx['gzip_sha256']==sha(parent_sha)
    assert (pin['target_exact_actor_OOP_turn_nodes'],pin['target_exact_actor_OOP_turn_strict_combos'])==(1,1)
    assert (idx['exact_target_actor_OOP_turn_nodes'],idx['exact_target_actor_OOP_turn_strict_combos'])==(1,1)
    parent=a.parent.resolve()
    mfile=parent/'evidence/UTG_CO-gto-KsQh4d.json'
    root=parent/'solver/postflop/out/UTG_CO/gto/KsQh4d_multiboard.json'
    rootjob=root.with_suffix('.job.json')
    for f,expected in ((mfile,pin['original_gto_manifest_sha256']),
                       (root,pin['original_gto_root_sha256']),
                       (rootjob,pin['original_gto_job_sha256'])):
        assert f.is_file() and sha(f)==expected, f'B235 original SHA mismatch: {f}'
    fr=load(root);gjob=load(rootjob);m=load(mfile)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,650,9750)
    assert (gjob['pot'],gjob['stack'],gjob['rake_rate'],gjob['rake_cap'])==(650,9750,.05,1000)
    assert gjob.get('hero') is None and not gjob.get('locks')
    assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert fr['info']['gto_expl_pct']<=.5
    fresh=a.fresh.resolve()
    report_path=fresh/'evidence/UTG_CO-exp_oop-KsQh4d.json'
    source=fresh/'solver/postflop/out/UTG_CO/exp_oop/KsQh4d_b50c_Tc.json'
    jobpath=source.with_suffix('.job.json')
    assert all(z.is_file() for z in (report_path,source,jobpath))
    report=load(report_path);raw=load(source);job=load(jobpath)
    assert report['schema']=='NL2_HU_B236_TRUE_PINNED_UTG_CO_GTO_FLOP_PARTIAL_NL2_OOP_V1'
    assert (report['target_rank'],report['model_id'],report['spot'],report['flop'],report['turn'])==(
        30,'ln-opfr-t_model-1hmsxaw',SPOT,FLOP,TURN)
    assert report['source_preflop']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert report['no_observed_private_card_NL2_rates'] is True
    assert report['original_GTO_flop_unchanged'] is True and report['partially_locked_turn_river_only'] is True
    assert report['original_GTO_source_run_id']==44894369547 and report['original_GTO_pin_sha256']==sha(pin_path)
    assert report['original_GTO_flop_root_sha256']==sha(root)
    assert report['original_GTO_job_sha256']==sha(rootjob)
    assert report['original_GTO_manifest_sha256']==sha(mfile)
    assert report['original_GTO_flop_full_sizing_not_reoptimized'] is True
    assert report['no_generic_CERT_upgrade'] is True and report['PR2_Draft_NEVER_MERGE'] is True
    assert not report['failures'] and len(report['cases'])==1
    case=report['cases'][0]
    assert (case['flop'],case['turn'],case['exact_action_line'])==(FLOP,TURN,LINE)
    assert (case['source_sha256'],case['original_exp_job_sha256'])==(sha(source),sha(jobpath))
    assert job['hero']==0 and job.get('locks') and job['rake_rate']==.05 and job['rake_cap']==1000
    assert (raw['line0'],raw['turn'])==('b50 c',TURN)
    assert any(len(z['board'])==10 for z in raw['nodes'])
    seq,stats=game_reach(fr,raw)
    actual=[]
    for n in raw['nodes']:
        if not(n['line']==LINE and n['player']==0 and len(n['board'])==8):continue
        v=seq['|'.join((n['board'],n['line'],'0'))]
        if v['count']<=0:continue
        spr=(raw['stack']-max(n['bets']))/n['pot']
        actual.append(dict(board=n['board'],strict_combos=v['count'],spr=round(spr,6),
            relative_spr_error_pct=round(100*abs(spr-7.25)/7.25,5),
            actions=n['acts']))
    strict=sum(x['strict_combos'] for x in actual)
    matched=sum(x['strict_combos'] for x in actual if x['relative_spr_error_pct']<=5)
    assert strict==case['strictly_reachable_actor_turn_combos']
    assert matched==case['model_SPR_eligible_actor_turn_combos']
    assert report['genuine_GTO_parent_actor_turn_strict_combos']==1
    blob=source.read_bytes()
    gz=gzip.compress(blob,compresslevel=9,mtime=0)
    archive=D/'solver_evidence/NL2_MULTIBOARD_B238_R30_KSQH4D_EXP_OOP.json.gz'
    archive.write_bytes(gz)
    idxout=dict(schema='NL2_HU_B238_RANK30_EXACT_B235_GTO_PLUS_REAL_NL2_PARTIAL_LOCK_V1',
        source_run_id=int(__import__('os').environ['GITHUB_RUN_ID']),
        original_B235_GTO_source_run_id=44894369547,
        original_B235_GTO_source_index_sha256=sha(index_path),
        original_B235_GTO_parent_pin_sha256=sha(pin_path),
        original_GTO_root_sha256=sha(root),original_GTO_job_sha256=sha(rootjob),
        original_preflop_CFR_pinned_not_observed_NL2_private_card=True,
        original_GTO_exploitability_pct=fr['info']['gto_expl_pct'],
        new_real_NL2_partial_Rust_source_sha256=sha(source),
        new_real_NL2_Rust_job_sha256=sha(jobpath),
        new_Rust_NL2_partial_source_gzip_sha256=sha(archive),
        version='exp_oop',spot=SPOT,rank=30,model_id='ln-opfr-t_model-1hmsxaw',
        flop=FLOP,turn=TURN,exact_line=LINE,hero_actor=0,
        original_GTO_target_turn_strict_combos=1,
        new_actor_OOP_turn_strict_combos=strict,
        new_actor_OOP_turn_exact_SPR_eligible_combos=matched,
        authentic_same_hero_board_paired_source=(matched>0),
        true_actor_node_examples=actual,
        actual_hero_gap_pct=case['hero_gap_pct'],
        pooled_NL2_marginal_or_assumed_lock_patterns=report['locks'],
        no_observed_per_hole_card_conditionals=True,
        source_reach_stats=dict(stats),
        only_downstream_turn_river_NL2_locked=True,
        no_new_full_flop_NL2_lock=True,
        no_generic_texture_CERT=True,immediate_CERT_upgrades=0,
        V38_CERT_MULTIBOARD=151,V38_APPROX=241,V38_EST=0,
        PR2_Draft_NEVER_MERGE=True)
    index_out=D/'solver_evidence/NL2_MULTIBOARD_B238_R30_KSQH4D_EXP_OOP.index.json'
    index_out.write_text(json.dumps(idxout,ensure_ascii=False,indent=2)+'\n')
    doc=ROOT/'docs/NL2_HU_B238_RANK30_KSQH4D_TRUE_PARTIAL_NL2_LOCK.md'
    doc.write_text('# B238 rank30 exact KsQh4d/Tc: genuine 100bb Rust UTG_CO OOP NL2 partial lock\n\n'
        'Upstream original GTO 44894369547, pinned 100bb preflop CFR, authentic GTO flop '
        'root and original job SHA unchanged. Downstream actor OOP turn+river was '
        're-solved with real Rust using pooled NL2 street/size marginal locks and '
        'explicit fallback assumptions (not observed conditional hole-card NL2 rates).\n\n'
        f'Original GTO actor turn strict combos: 1. New matched partial-NL2 actor turn '
        f'combos: {matched} (before SPR gate: {strict}). Genuine paired source={matched>0}. '
        f'Original GTO flop exploitability {fr["info"]["gto_expl_pct"]:.4f}%; '
        f'NL2 partial hero gap {case["hero_gap_pct"]}.\n\n'
        'This is one thin exact-board research example only. Do NOT generalize to all '
        'textures or claim measured private-hand frequencies. Even if positive, '
        'rank30 needs three to five different authentic GTO+NL2 actor-paired flops '
        'before any CERT-MULTIBOARD. V38 stays 151/241/0, full HU2475/2475 '
        'audit required and PR #2 remains Draft, NEVER MERGE.\n')
    print('B238 independent Rust NL2 strict source: '+json.dumps(dict(
        GTO_original=1,NL2_strict=strict,NL2_exact_SPR=matched,genuine_paired=matched>0,
        old_CERT=151,old_APPROX=241)))
if __name__=='__main__':main()
