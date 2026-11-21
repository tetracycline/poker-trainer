#!/usr/bin/env python3
"""B237 verify and archive only the original completed authentic B233-B235
UTG_CO GTO Rust sources. Previous workflow metadata mistakes do NOT authorize
re-solving, pretending zero reachable turn combos are CERT, or fabricating
per-private-hand NL2 observations.
"""
import argparse,gzip,hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data'
SPECS=[
 ('B233',44894288118,'4s4h2d'),
 ('B234',44894366667,'7s5h3d'),
 ('B235',44894369547,'KsQh4d'),
]
SPOT='UTG_CO';MODEL='ln-opfr-t_model-1hmsxaw'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--downloads',type=pathlib.Path,required=True)
    ap.add_argument('--solver-root',type=pathlib.Path,required=True)
    args=ap.parse_args()
    status=D/'nl2_hu_multiboard_status_v38_b206_rank190.json'
    s=load(status)
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(151,241,0,392)
    assert s['records'][MODEL]['label']=='APPROX'
    source_root=args.downloads.resolve()
    solver_root=args.solver_root.resolve()
    assert (solver_root/'v8_build/build/pf_data.json').is_file()
    out=D/'solver_evidence';out.mkdir(parents=True,exist_ok=True)
    results=[]
    for name,run,flop in SPECS:
        artifact_name=f'nl2-multiboard-{name}_R30_UTGCO_{flop.upper()}-UTG_CO-gto-{flop}'
        root=source_root/name/artifact_name
        mf=root/'evidence'/f'{SPOT}-gto-{flop}.json'
        parent=root/'solver/postflop/out'/SPOT/'gto'/f'{flop}_multiboard.json'
        job=parent.with_suffix('.job.json')
        if not all(z.is_file() for z in (mf,parent,job)):
            results.append(dict(batch=name,run_id=run,flop=flop,status='ORIGINAL_RAW_ARTIFACT_NOT_AVAILABLE',
                verified_gto_cases=0,CERT_upgrades=0))
            continue
        m=load(mf);fr=load(parent);j=load(job)
        assert (m['spot'],m['flop'],m['version'],m['solved_cases'])==(SPOT,flop,'gto',1)
        assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        assert m['preflop_ranges']['full_sha256']==sha((solver_root/'v8_build/build/pf_data.json').read_bytes())
        assert m['selected_lines']==['b50 c']
        assert m['root_pot_bb']==6.5 and m['root_remaining_bb']==97.5
        assert (fr['flop'],fr['pot'],fr['stack'])==(flop,650,9750)
        assert (j['pot'],j['stack'],j['rake_rate'],j['rake_cap'])==(650,9750,.05,1000)
        assert j.get('hero') is None and not j.get('locks')
        assert fr['info'].get('gto_expl_pct') is not None and float(fr['info']['gto_expl_pct'])<=.5
        assert m['cases'][0]['line']=='b50 c'
        verify_out=out/f'NL2_MULTIBOARD_{name}_R30_{flop.upper()}_GTO.revalidated.json'
        command=[sys.executable,str(ROOT/'tools/verify_hu_multiboard_100bb.py'),
            '--downloads',str(source_root/name),'--solver-root',str(solver_root),
            '--run-id',str(run),'--out',str(verify_out)]
        subprocess.run(command,check=True)
        x=load(verify_out)
        assert x['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
        assert x['source_run_id']==run and x['exact_board_gto_sources']==1 and not x['errors']
        assert (x['imputed_pool_locked_sources'],x['new_authentic_board_cases'])==(0,1)
        assert len(x['artifacts'])==1
        a=x['artifacts'][0];assert not a['errors'] and a['version']=='gto'
        c=a['cases'][0]
        assert c['flop_line']=='b50 c' and c['gto_exploitability_pct']<=.5
        turn=c['turn'];assert turn==m['turns'][0]
        nodes=[n for n in c['nodes'] if n['exact_node_line']=='b50 c/' and n['acting_seat']==0 and
            len(n['public_board'])==8 and n['strictly_reachable_combos']>0 and
            abs(n['node_spr']-7.25)/7.25<=.05]
        archive=out/f'NL2_MULTIBOARD_{name}_R30_{flop.upper()}_GTO.json.gz'
        raw=verify_out.read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0)
        pinpath=D/f'nl2_hu_{name.lower()}_rank30_utgco_{flop}_gto_parent_pin.json'
        idxpath=archive.with_suffix('').with_suffix('.index.json')
        p=dict(schema=f'NL2_HU_{name}_RANK30_UTGCO_{flop.upper()}_GTO_PARENT_PIN_V1',
            source_run_id=run,source_gto_job_id=None,
            spot=SPOT,flop=flop,turn=turn,flop_line='b50 c',turn_line='',
            target_rank=30,model_id=MODEL,
            original_gto_manifest_sha256=sha(mf.read_bytes()),
            original_gto_root_sha256=sha(parent.read_bytes()),
            original_gto_job_sha256=sha(job.read_bytes()),
            original_full_100bb_utgco_gto_source_pinned=True,
            preflop_CFR_pinned_not_observed_NL2_private_card=True,
            direct_nl2_lock_source_present=False,
            target_exact_actor_OOP_turn_nodes=len(nodes),
            target_exact_actor_OOP_turn_strict_combos=sum(n['strictly_reachable_combos'] for n in nodes),
            no_generic_model_certification=True)
        idx=dict(schema='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1',
            batch=f'{name}_R30_{flop.upper()}_GTO',run_id=run,
            actual_spot_flop_version_jobs=1,verified_cases=1,gto_cases=1,locked_cases=0,
            source_sha256=sha(raw),gzip_sha256=sha(packed),
            original_parent_GTO_root_SHA256=p['original_gto_root_sha256'],
            original_parent_GTO_job_SHA256=p['original_gto_job_sha256'],
            original_parent_GTO_manifest_SHA256=p['original_gto_manifest_sha256'],
            target_line='b50 c/',turn=turn,frozen_high_frequency_rank=30,
            exact_target_actor_OOP_turn_nodes=len(nodes),
            exact_target_actor_OOP_turn_strict_combos=p['target_exact_actor_OOP_turn_strict_combos'],
            rank30_remains_APPROX_until_actor_correct_genuine_NL2_lock=True,
            no_generic_model_certification=True,immediate_CERT_upgrades=0)
        # Never overwrite a contrary immutable source from another run.
        for path,data in ((archive,packed),
            (pinpath,(json.dumps(p,indent=2)+'\n').encode()),
            (idxpath,(json.dumps(idx,indent=2)+'\n').encode())):
            if path.exists() and path.read_bytes()!=data:
                raise ValueError('Conflicting existing source provenance '+str(path))
            path.write_bytes(data)
        verify_out.unlink()
        results.append(dict(batch=name,run_id=run,flop=flop,turn=turn,status='SOURCE_SHA_VERIFIED',
            source_sha256=sha(raw),parent_flop_GTO_sha256=p['original_gto_root_sha256'],
            pinned_preflop_CFR=True,GTO_gap_pct=c['gto_exploitability_pct'],
            strict_actor_turn_nodes=len(nodes),
            strict_actor_turn_combos=p['target_exact_actor_OOP_turn_strict_combos'],
            matched_true_NL2_partial_lock=False,CERT_upgrades=0))
    assert results and len(results)==3
    report=dict(schema='NL2_HU_B237_RANK30_3_ORIGINAL_GTO_INDEPENDENT_SALVAGE_V1',
        checked_sources=results,V38_parent_status_sha256=sha(status.read_bytes()),
        preflop_CFR_pinned_not_observed_NL2_private_card=True,
        no_gto_run_recomputed=True,real_Rust_verified_count=sum(z['status']=='SOURCE_SHA_VERIFIED' for z in results),
        all_sources_river_target_not_mislabeled_as_turn=True,
        new_NL2_hero_locked_sources=0,
        CERT_MULTIBOARD=151,APPROX=241,EST=0,TOTAL=392,
        no_false_CERT=True,no_generic_texture_GTO=True,PR2_Draft_NEVER_MERGE=True)
    (D/'nl2_hu_b237_rank30_original_GTO_source_salvage.json').write_text(json.dumps(report,indent=2)+'\n')
    notes=['# B237: rank30 UTG_CO authentic original GTO source salvage / no re-solves','',
        'Original Rust jobs are independent, with **pinned preflop solver CFR** '
        '(not observed NL2 per-private-card action rates). Their prior GitHub workflow '
        'source archive did not commit because a stale other-rank model ID failed a '
        'full fail-closed navigation gate; do not bypass it.',
        'B237 revalidates original SHA, actual Rust solver convergence, spot, size, '
        'turn actor, original source combo gates and model SPR before archiving.','',
        '| Batch | Exact flop/turn | Real GTO | OOP turn strict combos |',
        '|---|---|---|---:|']
    for z in results:
        notes.append('|'+z['batch']+'|'+z['flop']+' / '+z.get('turn','—')+'|'+z['status']+'|'+str(z.get('strict_actor_turn_combos',0))+'|')
    notes.extend(['','No new actor-matched NL2 lock; these are not yet CERT-MULTIBOARD. '
        'Exact three to five distinct true GTO plus actor-matched NL2 boards are required.',
        'V38 151 CERT/241 APPROX/0 EST and full existing 581 board/673 lock/133 b50 '
        'research and 2475/2475 HU regression must remain verified.',
        'PR #2 is Draft, NEVER MERGE.',''])
    pathlib.Path('docs/NL2_HU_B237_RANK30_ACTUAL_GTO_SOURCE_REVALIDATION.md').write_text('\n'.join(notes))
    print(json.dumps(dict(B237=True,real_sources=report['real_Rust_verified_count'],
        sources=[(z['batch'],z.get('strict_actor_turn_combos',0)) for z in results],
        CERT=151,APPROX=241)))
if __name__=='__main__':main()
