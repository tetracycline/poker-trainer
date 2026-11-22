#!/usr/bin/env python3
"""B379: individually SHA-freeze two completed B374 real Rust solves with 40/70 sequential reach.
One GTO flop + one matching partially locked NL2 hero-IP flop = ONE, not THREE, distinct certified flops.
"""
import hashlib,json,pathlib,sys
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path('data')
OUT=D/'nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json'
DOC=pathlib.Path('docs/NL2_HU_B379_RANK107_FIRST_TRUE_PAIR.md')
RUN=45017142943
ORIG={
'gto':dict(root='96729a02602711c3841af8b3597905b52f141cabf99816d361d0912da9934379',
 sub='be6672544be8c347024d8c2d9ccd56a48956729f7d8717ffb17e05100fd48582',
 manifest='48b9046bbad0b7b66a64d89ff3febcc240a16076c1a946dedf64718596a631f5'),
'exp_ip':dict(root='e8dbb1ee904438effa2f98105fb8c0d4cf5c2d7f851ac03517529acff577008d',
 sub='1fd6f897604af9919a1806a2f82d96eadbb3f96f61510834d701a3630b6457b5',
 manifest='728839611199828d512601280b80812f7b3e5a03e9da0c327f546a99c227e8dc')}
PIN='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
RUST='9d1509fe5077d019825f833eed04b16d342dfda1'
POOL='c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    root=pathlib.Path(sys.argv[1]); cases={}
    for version,proof in ORIG.items():
        name=f'nl2-multiboard-B374_R107-BTN_BB-7s5h3d-{version}'
        folder=root/name
        mp=folder/'evidence'/f'BTN_BB-7s5h3d-{version}.json'
        frp=folder/'solver/postflop/out/BTN_BB'/version/'7s5h3d_multiboard.json'
        sp=folder/'solver/postflop/out/BTN_BB'/version/'7s5h3d_b33c_6c.json'
        assert all(x.is_file() for x in (mp,frp,sp)),(version,folder)
        assert (folder/'evidence/poker-solver-pin.txt').read_text().strip()==PIN
        assert (folder/'evidence/rust-pin.txt').read_text().strip()==RUST
        assert sha(mp)==proof['manifest'] and sha(frp)==proof['root'] and sha(sp)==proof['sub']
        m,fr,sub=read(mp),read(frp),read(sp)
        assert (m['schema'],m['spot'],m['pot_family'],m['version'],m['flop'])==(
            'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','BTN_BB','SRP',version,'7s5h3d')
        assert (m['preflop_ranges']['source'],m['pool_source_sha256'])==(
            'PINNED_POKER_SOLVER_PREFLOP_CFR',POOL)
        assert (m['root_pot_bb'],m['root_remaining_bb'])==(5.5,97.5)
        assert (m['flop_size_profile'],m['flop_action_sizes'])==('full',['33%','50%','75%','100%'])
        assert (m['solved_cases'],len(m['cases']))==(1,1) and not m['failures'] and not m['skipped']
        assert (m['cases'][0]['line'],m['cases'][0]['turn'])==('b33 c','6c')
        assert m['file_flop_sha256']==proof['root'] and m['cases'][0]['source_sha256']==proof['sub']
        assert (sub['flop'],sub['turn'],sub['line0'])==('7s5h3d','6c','b33 c')
        assert (fr['flop'],fr['pot'],fr['stack'])==('7s5h3d',550,9750)
        assert m['cases'][0]['gto_gap_pct']<=0.5
        if version=='exp_ip':
            assert m['cases'][0]['hero_gap_pct']<=.5
            assert any(int(x.get('n') or 0)>=500 for x in m['locks'])
            assert any(int(v['nodes'])>0 for v in m['cases'][0]['lock_stats'].values())
        masks,stats=game_reach(fr,sub)
        source={}
        for n in sub['nodes']:
            if n['line']=='b33 c/x b50 c/x' and n['player']==1 and len(n['board'])==10:
                k='|'.join((n['board'],n['line'],str(n['player'])))
                q=masks[k]
                if q['count']>0:
                    source[n['board']]=dict(strict_reachable_hero_IP_combos=q['count'],
                      source_river_SPR=round((sub['stack']-max(n['bets']))/n['pot'],6),
                      exact_history=n['line'],acting_seat=n['player'])
        assert len(source)==2, (version,source)
        cases[version]=dict(source_manifest_sha256=proof['manifest'],
           original_flop_source_sha256=proof['root'],
           genuine_turn_river_source_sha256=proof['sub'],
           source_run_id=RUN,source_artifact_name=name,
           gto_gap_pct=m['cases'][0]['gto_gap_pct'],
           hero_gap_pct=m['cases'][0]['hero_gap_pct'],
           strict_full_street_summary=dict(stats),positive_named_river_actor_IP_nodes=source)
    assert set(cases['gto']['positive_named_river_actor_IP_nodes'])==set(cases['exp_ip']['positive_named_river_actor_IP_nodes'])
    expected={'3d5h7s6c9s':(44,28),'3d5h7s6c7h':(42,32)}
    pairs=[]
    for board,(a,b) in expected.items():
        q=cases['gto']['positive_named_river_actor_IP_nodes'][board]
        r=cases['exp_ip']['positive_named_river_actor_IP_nodes'][board]
        assert (q['strict_reachable_hero_IP_combos'],r['strict_reachable_hero_IP_combos'])==(a,b)
        assert q['exact_history']==r['exact_history']=='b33 c/x b50 c/x'
        assert abs(q['source_river_SPR']-r['source_river_SPR'])<1e-6
        assert abs(q['source_river_SPR']-4.968)/max(1.,q['source_river_SPR'])<=.05
        pairs.append(dict(exact_public_board=board,GTO_strict_40_70_actor_IP_combos=a,
             genuine_NL2_partially_locked_strict_actor_IP_combos=b,actual_SPR=q['source_river_SPR'],
             exact_hero_actor='BTN_IP',exact_history=q['exact_history']))
    s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
    mid='ln-ipfr-r_model-ujl14x'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(159,233,0,392)
    assert s['records'][mid]['label']=='APPROX' and s['records'][mid]['frequency_rank']==107
    out=dict(schema='NL2_HU_B379_FIRST_SHA_PINNED_TRUE_RANK107_GTO_NL2_IP_PAIR_STRICT_40_70_V1',
       original_run_id=RUN,original_solver_pin=PIN,original_Rust_pin=RUST,
       rank=107,model_id=mid,spot='BTN_BB',flop='7s5h3d',turn='6c',
       genuine_original_full_flop_GTO_and_NL2_hero_IP_sources=cases,
       two_named_exact_river_board_pair_proofs=pairs,
       one_distinct_flop_not_three=True,
       NL2_pool_rates_aggregate_history_proxy_not_observed_private_combos=True,
       no_generalized_texture_GTO=True,no_fabricated_sources=True,
       no_CERT_promotion_until_three_distinct_flops=True,
       CERT_MULTIBOARD=159,APPROX=233,EST=0,
       HU2475_independently_audited_by_workflow=True,PR2_draft_never_merge=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text("# B379 rank107 first real paired 100bb flop\n\n"
      "Genuine original GTO and separately genuine partially NL2-locked BTN-IP Rust solves on "
      "`7s5h3d/6c` are both SHA-pinned and follow max / 40%-70% actor-specific full-street reach. "
      "Named river public boards `3d5h7s6c9s` and `3d5h7s6c7h` have respectively **44/28** "
      "and **42/32** strict GTO/EXP actor-IP combos. This is **ONE distinct flop** "
      "(two river nodes), so rank107 remains APPROX; the original preflop ranges are "
      "pinned solver CFR, NL2 lock input is pooled marginal not private hand behavior. "
      "**159 CERT / 233 APPROX** unchanged.\n")
    print('PASS B379 rank107 first authentic same exact GTO/NL2 IP flop pair 44/28,42/32; CERT159 APPROX233')
if __name__=='__main__':main()
