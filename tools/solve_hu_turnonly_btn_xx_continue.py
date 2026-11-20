#!/usr/bin/env python3
# B29 immutable official GTO parent branch; three predeclared hero lines only.
"""Real Rust turn/river NL2 hero lock with SHA-pinned GTO flop reach parent.

We DO NOT claim to solve a locked flop: flop strategy/reach is frozen to a
previously independently verified GTO artifact. Only the turn+river response
is locked to pooled, partially imputed NL2 opponent marginals. Every output
preserves exact public cards, pot, actor, SPR, source SHA, full-street
sequential combo reach, and an explicit limited-scope tag.
"""
import argparse,hashlib,json,pathlib,re,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--solver-root',type=pathlib.Path,required=True)
    a.add_argument('--gto-artifact-root',type=pathlib.Path,required=True)
    a.add_argument('--gto-parent-run-id',type=int,required=True)
    a.add_argument('--spot',choices=['BTN_BB'],required=True)
    a.add_argument('--flop',required=True)
    a.add_argument('--flop-line',choices=['x x','x b50 c'],required=True)
    a.add_argument('--turn-line',choices=['b100 c','b66 c','x x'],default='b100 c')
    a.add_argument('--version',choices=['exp_oop','exp_ip'],required=True)
    a.add_argument('--manifest',type=pathlib.Path,required=True)
    args=a.parse_args()
    if args.turn_line=='b66 c' and args.flop_line!='x x':
        a.error('Pinned exact b66 turn proof requires flop checkcheck')
    if args.turn_line=='x x' and not (
        args.flop_line=='x b50 c' and args.version=='exp_oop' and args.spot=='BTN_BB'):
        a.error('Checked-through turn is preregistered for BTN_BB x-b50-c hero OOP only')
    if not re.fullmatch(r'(?:[23456789TJQKA][cdhs]){3}',args.flop):
        a.error('Explicit flop 3 cards required')
    root=args.gto_artifact_root.resolve()
    src=args.solver_root.resolve()
    pf=src/'postflop'
    # B31 independently SHA-checked true BTN_BB 100bb GTO range roots.
    pinned={
      'Ks7s2s':dict(
        manifest='543ee8b77cd22e27488c9d2f491259990f7743013f9843a6486c04864e819925',
        flop='50216984f138dc4404f206547ee9c07c05dc4f1e4e9e3af655235bc75ebc74d5',
        job='e0d38da008131f1b9a6d6ce679b08167f160f541a1d9b0e2079fd583e6f3c774',
        turn='9d'),
      '9s6h3d':dict(
        manifest='dad046881f9837e3b3c62fd3c0298db426f0ab731456ecde57651312d527841c',
        flop='259105deb64e55228bb6f85b1a3a479c54c4b3f149b697cd74e22bf0a7a18321',
        job='00987298491613f9728d3b97bb6ae28352ff9582bb3e8f3dca725b8d6911d2ce',
        turn='Ts')}
    if (args.spot!='BTN_BB' or args.flop not in pinned or
        args.gto_parent_run_id!=44525865923 or
        args.flop_line=='x b50 c' and args.version!='exp_oop'):
        raise ValueError('B32 only supports original BTN_BB GTO roots and predeclared hero action histories')
    expected=pinned[args.flop]
    manifest=root/('evidence/BTN_BB-gto-'+args.flop+'.json')
    original_root=root/('solver/postflop/out/BTN_BB/gto/'+args.flop+'_extra_branch.json')
    original_job=original_root.with_suffix('.job.json')
    if not all(p.is_file() for p in (manifest,original_root,original_job)):
        raise FileNotFoundError('Missing B31 original BTN_BB GTO artifact bytes')
    if any(sha(p)!=expected[k] for k,p in (
        ('manifest',manifest),('flop',original_root),('job',original_job))):
        raise ValueError('Original weighted BTN_BB GTO root SHA changed since B31')
    legacy=json.loads(manifest.read_text())
    if (legacy.get('schema')!='HU_MISSING_ACTION_HISTORY_CFR_V1' or
        legacy.get('spot')!='BTN_BB' or legacy.get('version')!='gto' or
        args.flop not in str(legacy.get('selected_flops')) or legacy.get('failures')):
        raise ValueError('Invalid original BTN_BB GTO manifest')
    # The original GTO weighted 169 range was solved under its OWN historical
    # dependencies, not necessarily the currently pinned poker-solver files.
    # Preserve both sets of SHA hashes and disclose all differences; the
    # original complete flop weights are copied byte-for-byte from the B28
    # verified artifact, so no source tree/range substitution occurs.
    original_deps={k:legacy.get(k) for k in (
        'source_preflop_tree_sha256','source_ranges_sha256','source_pipeline_sha256')}
    current_deps={
        'source_preflop_tree_sha256':sha(src/'v8_build/build/pf_data.json'),
        'source_ranges_sha256':sha(pf/'py/ranges.py'),
        'source_pipeline_sha256':sha(pf/'py/pipeline.py')}
    if any(not isinstance(v,str) or len(v)!=64 for v in original_deps.values()):
        raise ValueError('Historical source hashes missing, cannot preserve original GTO lineage')
    legacy_mismatch=[k for k in original_deps if original_deps[k]!=current_deps[k]]
    print(json.dumps(dict(legacy_original_dependency_differences=legacy_mismatch,
        reuse_policy='GTO weighted parent byte-for-byte original; NOT labeled as current preflop CFR')),flush=True)
    m=dict(schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
        version='gto',spot=args.spot,flop=args.flop,failures=[],
        no_generic_certification=True,root_pot_bb=5.5,root_remaining_bb=97.5,
        selected_lines=['x x','x b50 c'],
        turns=[expected['turn']],turn_sizing_mode='default',
        file_flop=str(original_root.relative_to(root/'solver/postflop')),
        file_flop_sha256=expected['flop'],
        pool_source_sha256=sha(src/'inputs/pool_stats.json'))
    manifests=[manifest]
    if sha(original_root)!=m['file_flop_sha256']:
        raise ValueError('GTO flop parent SHA mismatch with original source manifest')
    fr=json.loads(original_root.read_text());gto_job=json.loads(original_job.read_text())
    if gto_job.get('hero') is not None or fr['flop']!=args.flop or fr['pot']!=550 or fr['stack']!=9750:
        raise ValueError('GTO source has wrong actor/root')
    if expected['turn'] not in fr.get('turns',[]) or not fr.get('hands') or not fr.get('nodes'):
        raise ValueError('Official GTO root lacks original chosen turn/combo weights')
    if gto_job.get('rake_rate')!=0.05 or gto_job.get('rake_cap')!=1000:
        raise ValueError('GTO original job NL2 rake settings mismatch')
    if not (pf/'pfdriver/target/release/pfdriver').exists():
        raise RuntimeError('Genuine pinned Rust CFR driver not available')
    sys.path.insert(0,str(pf/'py'))
    import pipeline,job
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    if m['pool_source_sha256']!=sha(src/'inputs/pool_stats.json'):
        raise ValueError('Pinned NL2 source pool changed')
    original_locks=pipeline.lock_list
    pipeline.lock_list=lambda spot,ver,flop:make_fallbacks(spot,ver,pool,original_locks,flop)
    orig_make=pipeline.make_job
    def sized(*pos,**kwargs):
        kwargs['target']=0.5
        kwargs['rank']=0.5
        kwargs['iters']=1700
        j=orig_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES)
        j['flop_ip']=','.join(SIZES)
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=sized
    if args.turn_line=='b66 c':
        pipeline.SUB.update(turn_oop='66%',turn_ip='66%')
    pipeline.TURN_LINES=[args.turn_line]
    turns=pipeline.turns_for(args.flop)[:1]
    if len(turns)!=1:raise ValueError('Pinned turn selection vanished')
    turn=turns[0]
    if m['turns'][0]!=turn:raise ValueError('Turn card differs from GTO parent')
    parent=next((n for n in fr['nodes'] if n['line']==args.flop_line+'/' and n['board'][-2:]==turn),None)
    if parent is None or not parent.get('wr'):
        raise ValueError('Pinned GTO flop has no exact parent action/turn')
    legal=[]
    board_cards={args.flop[i:i+2] for i in (0,2,4)}|{turn}
    for seat in (0,1):
        total=0.
        for hole,w in zip(fr['hands'][seat],parent['wr'][seat]):
            if float(w)<=1e-4 or hole[:2] in board_cards or hole[2:4] in board_cards:
                continue
            total+=float(w)
        legal.append(total)
    if min(legal)<=1e-4:
        raise ValueError('GTO parent has illegal/empty combo weights after blockers')
    out=pf/'out'/args.spot/args.version
    out.mkdir(parents=True,exist_ok=True)
    dst=out/(args.flop+'_multiboard.json')
    dst_job=dst.with_suffix('.job.json')
    shutil.copy2(original_root,dst)
    shutil.copy2(original_job,dst_job)
    locks,lock_src=pipeline.lock_list(args.spot,args.version,args.flop)
    if not locks:raise ValueError('No frozen NL2 partial villain patterns')
    report=dict(schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
        spot=args.spot,version=args.version,flop=args.flop,
        pot_family='SRP',root_pot_bb=5.5,root_remaining_bb=97.5,root_spr=round(97.5/5.5,6),
        preflop_ranges=dict(
            source='PINNED_LEGACY_OFFICIAL_GTO_FLOP_WEIGHTS',
            spot=args.spot,
            original_official_preflop_tree_sha256=original_deps['source_preflop_tree_sha256'],
            original_official_manifest_sha256=expected['manifest'],
            original_official_root_sha256=expected['flop'],
            original_official_root_job_sha256=expected['job'],
            old_source_dependencies=original_deps,
            currently_pinned_solver_dependencies=current_deps,
            legacy_dependency_mismatches=legacy_mismatch,
            do_not_claim_same_preflop_tree_as_current=bool(legacy_mismatch)),
        n_NL2_hands=pool['hands'],pool_source_sha256=sha(src/'inputs/pool_stats.json'),
        solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
        flop_action_sizes=dict(oop=gto_job['flop_oop'],ip=gto_job['flop_ip'],
                              raise_sizes=gto_job['flop_raise']),
        flop_size_profile='legacy-official-pinned',
        restricted_original_GTO_tree=True,
        allow_OOP_flop_leads=True,
        flop_line_policy=('checkcheck' if args.flop_line=='x x' else 'checked-b50only'),
        selected_lines=[args.flop_line],
        turn_line_policy=('xxonly' if args.turn_line=='x x' else 'b66only' if args.turn_line=='b66 c' else 'b100only'),
        selected_turn_lines=[args.turn_line],
        turn_sizing_mode=('exact-b66-only' if args.turn_line=='b66 c' else 'default'),
        turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
        turns=turns,
        file_flop=str(dst.relative_to(pf)),file_flop_sha256=sha(dst),
        flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
        flop_root_jobfile_sha256=sha(dst_job),gto_parent_source_sha256=sha(original_root),
        gto_parent_source_run_id=args.gto_parent_run_id,
        gto_parent_source_manifest_sha256=sha(manifests[0]),
        pinned_official_legacy_source_id=44525865923,
        pinned_official_legacy_gto_root_sha256=sha(original_root),
        pinned_official_legacy_job_sha256=sha(original_job),
        source_origin_policy='Independently SHA-checked original official GTO flop root. New genuine downstream NL2 partial lock with observed pool marginals when available; old unknown source counts NOT overwritten.',
        gto_parent_source_note='GTO flop root/reach unchanged. NL2 partial villain lock ONLY on authentic turn/river subgame; never full locked flop.',
        locks=[dict(pat=z['pat'],scope=z.get('scope','PINNED_MEASURED_NL2_SOURCE'),
                    source=z.get('src'),n=z.get('n')) for z in lock_src],
        unknown_action_frequency_policy='Measured NL2 aggregate frequencies when present; otherwise declared assumptions. NOT exact conditional combo behavior.',
        no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
        cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        pipeline.solve_sub(args.spot,args.version,args.flop,fr,args.flop_line,turn)
        sub=out/(args.flop+'_'+args.flop_line.replace(' ','')+'_'+turn+'.json')
        if not sub.is_file():raise FileNotFoundError('Missing genuine Rust downstream solver subgame')
        d=json.loads(sub.read_text())
        if not any(len(n['board'])==10 for n in d['nodes']):
            raise ValueError('No real river node in downstream Rust job')
        report['cases'].append(dict(line=args.flop_line,turn=turn,
            source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
            real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
            flop_parent_pot_bb=parent['pot']/100,
            flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
            true_river_nodes=sum(len(n['board'])==10 for n in d['nodes']),
            source_node_count=len(d['nodes']),
            gto_gap_pct=d['info'].get('gto_expl_pct'),
            hero_gap_pct=d['info'].get('hero_gap_pct'),
            lock_stats=d['info'].get('lock_stats',{}),
            status='NL2_TURN_ONLY_PARTIAL_LOCK_FROM_IMMUTABLE_GTO_FLOP_PARENT'))
    except Exception as e:
        report['failures'].append({'error':str(e),'traceback':traceback.format_exc()[-1800:]})
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:report[k] for k in ('spot','version','flop','selected_lines','solved_cases','failures','elapsed_seconds')}),flush=True)
    if report['failures'] or report['solved_cases']<1:raise SystemExit(1)
if __name__=='__main__':main()
