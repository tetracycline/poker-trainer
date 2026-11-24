"""Continue the saved CO/BTN flop on four previously unstudied public turns.

The pinned driver exports unconditional reach to five decimal places. At this
two-player chance event Rust preserves those weights or sets them to zero.
We reconstruct that export precision, including zero-weight hands in their
original order, and validate the entire operation against four held-out jobs.
Strategy, equity and normalized weights on the new turn require fresh CFR.
"""
import argparse
import base64
import json
from pathlib import Path
import struct
import subprocess
import sys
from zipfile import ZipFile

import hu_b758_rank75_monotone as old
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_sequential_cfr_reach import cardkey

native = old.native
checked = old.checked
FLOP = '9d8d6d'
TURNS = ('2d', '7d', '9h', 'Ac')
ORIGINAL_TURNS = ('2c', '3h', 'Ts', 'Kh')
OLD_HEAD = '0ff53f5eb30679e1150dd96fe3c2e7648d84f377'
MANIFEST = '22752dee531ceb18778e5270aec03c39d5f1bd58'
SOURCES = {
    'NL2_B758_R75_9D8D6D.zip': (14895497658, 'ba543a777db8e87b90ee3ee12eadc9fc71902cf0cb2d95ef0f906de3e5560d16'),
    'NL2_B758_ROOT_R75_9D8D6D.zip': (14894853729, '09b502857f7858c7680d09312c20dd60999486e5b7b310eb98fd586018746827'),
}
RUST_FILES = {
    'src/game/interpreter.rs': 'd44d63a9c922ba11b99b69ac685285a06a6999f6',
    'src/game/base.rs': 'f1cc0f01aa46b358de6b9ff3e4c483fcd9e85b31',
}
DRIVER_SOURCE = '815164ee87681002362bb02135e20042393b279e'
WORKER = 'tools/hu_b766_rank75_chance_turns.py'


def originals(evidence):
    manifest = evidence.parent / 'nl2_hu_b761_source_manifest.json'
    assert checked.blob(manifest) == MANIFEST
    metadata = json.loads(manifest.read_bytes())
    run = metadata['run']
    assert (run['id'], run['head_sha'], run['conclusion']) == (45339357100, OLD_HEAD, 'success')
    job, = (j for j in metadata['jobs'] if j['id'] == 138258993861)
    assert (job['name'], job['head_sha'], job['status'], job['conclusion']) == ('solve (9d8d6d)', OLD_HEAD, 'completed', 'success')
    for name, (artifact, digest) in SOURCES.items():
        item, = (a for a in metadata['artifacts'] if a['id'] == artifact)
        assert item['digest'] == 'sha256:' + digest and item['workflow_run']['head_sha'] == OLD_HEAD
        assert sha((evidence / name).read_bytes()) == digest
    full, checkpoint = [evidence / name for name in SOURCES]
    with ZipFile(full) as z, ZipFile(checkpoint) as cp:
        pin = json.loads(cp.read('checkpoint.json'))
        root_job = z.read('flop/job.json')
        root_raw = z.read('flop/result.json')
        assert cp.read('flop/job.json') == root_job and cp.read('flop/result.json') == root_raw
        assert sha(root_raw) == pin['root_sha256'] and sha(root_job) == pin['job_sha256']
        assert pin['worker_blob'] == checked.blob('tools/hu_b758_rank75_monotone.py') == '44528fa0da5661425f7b259281eba4062c034747'
        original = json.loads(z.read('proof.json'))
        assert original['root_sha256'] == pin['root_sha256'] and original['root_job_sha256'] == pin['job_sha256']
        assert original['positive_distinct_flops'] == 0
        assert [r['turn'] for r in original['turns']] == list(ORIGINAL_TURNS)
        assert all(sha(z.read(name)) == digest for name, digest in original['native_files_sha256'].items())
        old_jobs = {t: z.read(f'{t}-gto/job.json') for t in ORIGINAL_TURNS}
        old_gto = json.loads(z.read('Ts-gto/result.json'))
    root = json.loads(root_raw)
    assert old.verify_root(FLOP, root)['new_raw_boundary_sha256'] == pin['new_raw_boundary_sha256']
    return root, json.loads(root_job), old_jobs, old_gto, pin


def weight_bytes(weights):
    return b''.join(struct.pack('>d', x) for x in weights)


def blocked(hands, turn):
    """Match assign_zero_weights' two-seat, no-bunching mask on a turn."""
    hands_by_seat = [[set(cardkey(h)) for h in hs] for hs in hands]
    blocked_indices = []
    for seat in (0, 1):
        possible_other = [h for h in hands_by_seat[1-seat] if turn not in h]
        assert possible_other
        shared_opponent_cards = set.intersection(*possible_other)
        assert not shared_opponent_cards, 'Unexpected mandatory opponent card in the original ranges'
        dead = shared_opponent_cards | {turn}
        blocked_indices.append({i for i, h in enumerate(hands_by_seat[seat]) if not h.isdisjoint(dead)})
    return blocked_indices


def reconstruct(root, observed, masks, selected, turn):
    """Use only selected source public turns to recover each unchanged value."""
    result = []
    for seat, hands in enumerate(root['hands']):
        row = []
        for i in range(len(hands)):
            values = []
            for card in selected:
                value = observed[card]['wr'][seat][i]
                if i in masks[card][seat]:
                    assert weight_bytes([value]) == weight_bytes([0.0])
                else:
                    values.append(value)
            assert values and all(weight_bytes([x]) == weight_bytes([values[0]]) for x in values)
            row.append(0.0 if i in masks[turn][seat] else values[0])
        result.append(row)
    return result


def range_input(root, turn, weights):
    # This boundary supplies only ranges to turn_job/root_gate. Native decision()
    # always receives the unmodified original flop output and a real CFR result.
    original = next(n for n in root['nodes'] if n['line'] == 'b33 c/')
    boundary = dict(line='b33 c/', board=original['board'][:6]+turn, player=0,
                    pot=2740, bets=[545,545], wr=weights)
    return dict(root, nodes=[n for n in root['nodes'] if n['line'] != 'b33 c/'] + [boundary])


def preflight(args):
    solver = args.solver.resolve()
    rust = args.rust_source or solver / 'postflop/postflop-solver'
    assert sys.version_info[:2] == (3, 11)
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == native.SOLVER
    assert all(checked.blob(rust / p) == expected for p, expected in RUST_FILES.items())
    assert checked.blob(solver / 'postflop/pfdriver/src/main.rs') == DRIVER_SOURCE
    if args.driver:
        assert args.driver.resolve() == solver / 'postflop/pfdriver/target/release/pfdriver'
        assert rust.resolve() == solver / 'postflop/postflop-solver'
        assert subprocess.check_output(['git','-C',rust,'rev-parse','HEAD'],text=True).strip() == native.RUST
    assert all(checked.blob(p) == expected for p, expected in checked.PINS.items())
    assert checked.blob('tools/hu_b707_rank75_highcards.py') == '9b845a82f46de9d058117204dba58ae234bb23e6'
    assert tuple(checked.blob(p) for p in checked.APP_FILES) == old.APP
    for path, digest in [('postflop/py/pipeline.py',native.PIPELINE), ('postflop/py/ranges.py',native.RANGES),
                         ('inputs/pool_stats.json',native.POOL)]:
        assert sha((solver / path).read_bytes()) == digest
    sys.path.insert(0, str(solver / 'postflop/py'))
    import pipeline
    import ranges
    ranges.SPOTS.update(native.EXTRA_SPOTS)
    root, flop_job, old_jobs, old_gto, checkpoint = originals(args.evidence)
    assert flop_job['oop'] == ranges.to_str(ranges.ranges('CO3_BTN','gto')[0])
    assert flop_job['ip'] == ranges.to_str(ranges.ranges('CO3_BTN','gto')[1])
    assert flop_job['flop_oop'] == flop_job['flop_ip'] == '33%,50%,75%,100%'
    assert [len(h) for h in root['hands']] == [169,105]
    observed = {n['board'][6:]: n for n in root['nodes'] if n['line'] == 'b33 c/'}
    assert set(observed) == set(ORIGINAL_TURNS)
    # On a monotone flop all three off-suits are equivalent, suit d is distinct.
    categories = [(t[0], t[1]=='d') for t in (*ORIGINAL_TURNS,*TURNS)]
    assert len(set(categories)) == len(categories)
    masks = {t: blocked(root['hands'], t) for t in (*ORIGINAL_TURNS, *TURNS)}
    held_out = {}
    for t in ORIGINAL_TURNS:
        other = [s for s in ORIGINAL_TURNS if s != t]
        weights = reconstruct(root, observed, masks, other, t)
        for a,b in zip(weights, observed[t]['wr'], strict=True):
            assert weight_bytes(a) == weight_bytes(b)
        rebuilt = compact(native.turn_job(range_input(root,t,weights), t, pipeline))
        assert rebuilt == old_jobs[t], ('held-out full job bytes', t)
        held_out[t] = dict(full_job_sha256=sha(rebuilt), raw_seat_sha256=[sha(weight_bytes(a)) for a in weights])
    route = json.loads(subprocess.check_output(['node','tools/hu_b674_threebet_call_routes.cjs']))['75']
    assert (route['id'],route['line'],route['seat'],route['turn_pot'],route['turn_stack']) == (native.MODEL,native.LINE,1,2740,8705)
    assert route['routes']['mono'] == dict(parents=['DRAW','WDRAW'], decisions={'DRAW':'下注 ½','WDRAW':'過'})
    old_row,_ = native.decision(root,old_gto,'Ts',route)
    bits = base64.b64decode(old_row['compatible_action_mask_b64'],validate=True)
    original_node, = (n for n in old_gto['nodes'] if n['line'] == native.LINE and n['player'] == 1)
    checked_hands = {''.join(cardkey(h)) for h,mask in zip(old_gto['hands'][1],bits,strict=True)
                     if mask & (1 << original_node['acts'].index('x'))}
    candidates = sorted('J'+a+'Q'+b for a in 'chs' for b in 'chs' if a != b)
    assert set(candidates) <= checked_hands and all(native.hcls(h,FLOP+'Ts') == 'S' for h in candidates)
    gates,jobs = {},{}
    for t in TURNS:
        raw = reconstruct(root,observed,masks,ORIGINAL_TURNS,t)
        source = range_input(root,t,raw)
        gate = checked.checked_gate(source,t,route)
        assert set(candidates) <= set(gate['rendered_hands'])
        assert all(native.hcls(h,FLOP+t) == 'WDRAW' for h in candidates)
        gate.update(raw_seat_sha256=[sha(weight_bytes(a)) for a in raw],prior_Ts_accepted_check=candidates)
        gates[t] = gate
        jobs[t] = native.turn_job(source,t,pipeline)
    evidence = dict(archive_sha256=SOURCES,source_head=OLD_HEAD,source_run=45339357100,source_job=138258993861,
                    root=checkpoint,solver=native.SOLVER,rust=native.RUST,driver_source=DRIVER_SOURCE,
                    native_chance_sources=RUST_FILES,original_export_decimals=5,seat_hand_counts=[169,105],
                    leave_one_turn_out=held_out,root_gates=gates)
    return root, route, pipeline, jobs, evidence


def run(args):
    root, route, pipeline, jobs, evidence = preflight(args)
    if args.preflight:
        print(json.dumps(evidence)); return
    folder = args.output
    if args.driver:
        assert not folder.exists() or not any(folder.iterdir())
    else:
        assert (folder/'proof.json').is_file()
    folder.mkdir(parents=True,exist_ok=True)
    pool = json.loads((args.solver/'inputs/pool_stats.json').read_bytes())['NL2']
    records = []
    for turn, job in jobs.items():
        entry = dict(turn=turn,root_gate=evidence['root_gates'][turn])
        records.append(entry)
        for mode in ('gto','exp_ip'):
            if mode == 'exp_ip':
                job, rules = native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='CO3_BTN')),job=job),
                                                mode,pool,pipeline)
                job['out'] = 'result.json'
            sub = folder / f'{turn}-{mode}'
            game = native.solve(sub,job,args.driver)
            assert (sub/'job.json').read_bytes() == compact(job)
            assert (game['flop'],game['pot'],game['stack']) == (FLOP,2740,8705)
            assert 0 <= game['info']['gto_expl_pct'] <= .5
            n, = (n for n in game['nodes'] if n['line']==native.LINE and n['player']==1)
            assert checked.cards(n['board'][:6]) == checked.cards(FLOP) and n['board'][6:] == turn
            assert 'b50' in n['acts']
            row,hands = native.decision(root,game,turn,route)
            assert set(hands) <= set(entry['root_gate']['rendered_hands'])
            entry[mode] = dict(job_sha256=sha(compact(job)),result_sha256=sha((sub/'result.json').read_bytes()),
                               reach=row,rendered_hands=hands)
            if mode == 'gto':
                assert not game['info'].get('lock_stats')
                if not hands:
                    break
            else:
                assert 0 <= game['info']['hero_gap_pct'] <= .5
                measured = native.audit_patterns(game,job,dict(locks=rules),pool,1)
                assert any(n > 0 for k,n in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
                entry['measured_lock_application'] = measured
        entry['shared_hands'] = sorted(entry['gto']['rendered_hands'].keys() & entry.get('exp_ip',{}).get('rendered_hands',{}).keys())
        if entry['shared_hands']:
            break
    joint = [r['exp_ip']['reach'] for r in records if 'exp_ip' in r and r['exp_ip']['reach']['strict_legal_combos']
             and r['exp_ip']['reach']['compatible_hole_card_pairs']]
    medium = [r['b50'] for r in joint if r['b50'] is not None]
    report = dict(schema='NL2_B766_RANK75_CONDITIONAL_TURNS_V1',rank=75,model_id=native.MODEL,line=native.LINE,
                  flop=FLOP,actor=1,pot=2740,stack=8705,source_worker_blob=checked.blob(__file__),
                  origin=evidence,turns=records,actor_locked_joint_boards=len(joint),half_pot_assessed=len(medium),
                  nonpolarized_candidates=sum(b['candidate'] for b in medium),positive_distinct_flops=int(any(r['shared_hands'] for r in records)),
                  not_a_certification=True,no_per_hand_observed_nl2_frequencies=True)
    (folder/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','actor_locked_joint_boards','half_pot_assessed','nonpolarized_candidates','positive_distinct_flops')}))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--solver',type=Path,required=True)
    cli.add_argument('--rust-source',type=Path)
    cli.add_argument('--evidence',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
