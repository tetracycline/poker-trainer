"""Verify and preserve the four B766 turn attempts, including the actual NL2 lock."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b772_rank75_receipts as source
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize
from hu_sequential_cfr_reach import accepted, cardkey
from hu_b690_rank75_connected import ACTIONS, LINE, MODEL, hcls, tx

RECEIPT_BLOB = 'eaee3c58a934b88fa9d1011bbc3ed34e073c11e0'
TURNS = ('2d','7d','9h','Ac')


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(['git',*args],text=True).strip()


def diagnose(root, game, evidence, gate, route):
    node, = (n for n in game['nodes'] if (n['line'],n['player']) == (LINE,1))
    parent, = (n for n in game['nodes'] if (n['line'],n['player']) == ('b33 c/',0))
    co, = (n for n in root['nodes'] if n['line'] == '')
    btn, = (n for n in root['nodes'] if n['line'] == 'b33')
    row = evidence['reach']
    public = node['board']
    assert (row['public_board'],node['pot'],node['bets']) == (public,2740,[0,0])
    public_cards = {public[i:i+2] for i in range(0,8,2)}
    co_b33 = accepted(co,root['hands'],'b33')
    btn_call = accepted(btn,root['hands'],'c')
    co_check = accepted(parent,game['hands'],'x')
    villains = co_b33 & co_check & {cardkey(h) for h,w in zip(game['hands'][0],node['w'][0],strict=True)
                                    if w > 1e-4 and public_cards.isdisjoint(cardkey(h))}
    masks = base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    strict = pair_count = 0
    hands = {}
    for h,bits in zip(game['hands'][1],masks,strict=True):
        if not bits:
            continue
        physical = cardkey(h)
        assert physical in btn_call and public_cards.isdisjoint(physical)
        deals = sum(set(physical).isdisjoint(v) for v in villains)
        assert deals > 0
        strict += 1
        pair_count += deals
        if ''.join(physical) not in gate['rendered_hands']:
            continue
        fc,tc = hcls(h,public[:6]),hcls(h,public)
        assert fc in route['routes'][tx(public[:6])]['parents']
        shown = route['routes'][tx(public)]['decisions'][tc]
        allowed = [a for i,a in enumerate(node['acts']) if bits & (1<<i)]
        hands[''.join(physical)] = dict(flop_class=fc,turn_class=tc,displayed=shown,
                                       accepted=allowed,match=ACTIONS[shown] in allowed)
    assert (strict,pair_count) == (row['strict_legal_combos'],row['compatible_hole_card_pairs'])
    assert sorted(h for h,data in hands.items() if data['match']) == sorted(evidence['rendered_hands'])
    return dict(source_job_sha256=evidence['job_sha256'],source_result_sha256=evidence['result_sha256'],
                oop_flop_b33=len(co_b33),ip_flop_call=len(btn_call),oop_turn_check=len(co_check),
                oop_turn_check_with_original_b33=len(co_check & co_b33),positive_weight_unblocked_oop=len(villains),
                strict_combos=strict,compatible_pairs=pair_count,strict_rendered_hands_before_action=len(hands),
                matches=len(evidence['rendered_hands']),strict_ui_actions=hands,b50=row['b50'])


def publish(args):
    assert sys.version_info[:2] == (3,11)
    registry = Path('data/nl2_hu_multiboard_status_current.json')
    snapshot = registry.read_bytes()
    model = json.loads(snapshot)['records'][MODEL]
    assert (model['frequency_rank'],model['label'],model['solver_profile'],model['assumed_model_node_spr']) == (75,'APPROX','CO3_BTN',3.177)
    receipt = args.receipts/'receipt.json'
    assert git('hash-object',str(receipt)) == RECEIPT_BLOB
    auth = read(receipt)
    assert source.validate(auth) == auth and receipt.read_bytes() == json_bytes(auth)
    meta, = auth['artifacts']
    raw = (args.receipts/(str(source.ARTIFACT)+'.zip')).read_bytes()
    assert len(raw) == meta['size_in_bytes'] and sha(raw) == source.DIGEST
    for path,blob in source.BLOBS.items():
        assert git('rev-parse',source.HEAD+':'+path) == blob
    stage = args.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    evid = stage/'solver_evidence'
    partial = evid/'partial'
    partial.mkdir(parents=True)
    route_cmd = ['node','tools/hu_b674_threebet_call_routes.cjs']
    route = json.loads(subprocess.check_output(route_cmd))['75']
    with TemporaryDirectory(prefix='b772-') as tmp:
        frozen = Path(tmp)/'source'
        materialize(source.HEAD,frozen)
        assert json.loads(subprocess.check_output(route_cmd,cwd=frozen))['75'] == route
        folder = Path(tmp)/'original'
        files = unpack_original(raw,folder)
        original = (folder/'proof.json').read_bytes()
        claim = json.loads(original)
        assert (claim['schema'],claim['rank'],claim['model_id'],claim['flop'],claim['source_worker_blob']) == (
            'NL2_B766_RANK75_CONDITIONAL_TURNS_V1',75,MODEL,'9d8d6d',source.BLOBS[source.WORKER])
        expected = {f'{t}-gto/{n}.json' for t in TURNS for n in ('job','result')}
        expected.update({'proof.json','2d-exp_ip/job.json','2d-exp_ip/result.json'})
        assert files == expected
        before = {p:sha((folder/p).read_bytes()) for p in sorted(files)}
        subprocess.run([sys.executable,str(frozen/source.WORKER),'--solver',str(args.solver.resolve()),
                        '--rust-source',str(args.rust_source.resolve()),'--evidence',str(args.evidence.resolve()),
                        '--output',str(folder)],cwd=frozen,check=True)
        assert (folder/'proof.json').read_bytes() == original
        assert all(sha((folder/p).read_bytes()) == digest for p,digest in before.items())
        assert claim['not_a_certification'] and (claim['positive_distinct_flops'],claim['actor_locked_joint_boards'],claim['half_pot_assessed']) == (0,0,0)
        assert [r['turn'] for r in claim['turns']] == list(TURNS)
        origin = claim['origin']
        root_filename = 'NL2_B758_ROOT_R75_9D8D6D.zip'
        with ZipFile(args.evidence/root_filename) as z:
            root_raw = z.read('flop/result.json')
        assert sha(root_raw) == origin['root']['root_sha256']
        root = json.loads(root_raw)
        attempts = []
        for r in claim['turns']:
            assert not r['shared_hands']
            t = r['turn']
            item = dict(turn=t,source_public_board=r['gto']['reach']['public_board'],root_gate=r['root_gate'])
            for mode in ('gto','exp_ip'):
                if mode not in r:
                    continue
                game = read(folder/f'{t}-{mode}/result.json')
                item[mode] = diagnose(root,game,r[mode],r['root_gate'],route)
            item['reason'] = ('LOCKED_TWO_SEAT_REACH_ZERO' if 'exp_ip' in r else
                'GTO_TWO_SEAT_REACH_ZERO' if not item['gto']['strict_combos'] else
                'GTO_DISPLAY_ACTION_INTERSECTION_ZERO')
            if 'exp_ip' in r:
                assert t=='2d' and item['gto']['matches']==6 and item['exp_ip']['strict_combos']==0
                item['measured_lock_application'] = r['measured_lock_application']
            attempts.append(item)
    medium = dict(schema='NL2_HU_B772_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    result = dict(schema='NL2_B772_R75_VERIFIED_CONDITIONAL_OUTCOMES_V1',model_id=MODEL,rank=75,
                  run=source.RUN,head=source.HEAD,job=source.JOB,artifact=source.ARTIFACT,archive_sha256=source.DIGEST,
                  original_proof_sha256=sha(original),native_files_sha256=before,flop='9d8d6d',origin=origin,
                  native_gto_turns=4,gto_joint_decisions=3,gto_rendered_positive_turns=1,
                  executed_exp_ip_locks=1,joint_eligible_actor_locked_boards=0,joint_half_pot_assessed=0,
                  joint_nonpolarized_candidates=0,positive_distinct_flops=0,turns=attempts,changed_registry_records=0)
    (stage/'nl2_hu_b772_source_manifest.json').write_bytes(receipt.read_bytes())
    (stage/'nl2_hu_b772_results.json').write_bytes(json_bytes(result))
    (evid/'NL2_B766_R75_9D8D6D.zip').write_bytes(raw)
    (partial/'b772_9d8d6d_proof.json').write_bytes(original)
    (partial/'b772_rank75.json').write_bytes(json_bytes(dict(rank=75,model_id=MODEL,boards=[],pins=[])))
    (partial/'b772_rank75_locked_medium.json').write_bytes(json_bytes(medium))
    assert registry.read_bytes() == snapshot


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    for k in ('solver','rust-source','receipts','output'):
        cli.add_argument('--'+k,type=Path,required=True)
    cli.add_argument('--evidence',type=Path,default=Path('data/solver_evidence'))
    publish(cli.parse_args())
