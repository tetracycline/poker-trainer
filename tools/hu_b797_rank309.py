"""Preserve and replay the B796 river policies without running the native driver."""
import argparse
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b796_rank309_checked_qc as native
import hu_b797_collect as source
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_publish import unpack_original

RECEIPT_SHA='fb46c91487f55e09e7c51a1f062f5675f44018715f2dddf233aee54aa5083e8a'
ARCHIVE='NL2_B796_R309_9H7H5H_QC.zip'
MODES=('gto','exp_ip')
WHY='EVERY_FLOP_AND_RAW_QC_ELIGIBLE_BTN_MID_HAND_ACCEPTS_HALF_POT_AND_NONE_ACCEPTS_TURN_CHECK_UNDER_EXP_IP'


def verify_turn(folder,claim,root):
    gate=claim['gate']
    public=gate['public_board']
    hands=set(map(native.cardkey,gate['displayed_btn_hands']))
    fl=public[:6]
    live_hero=native.accepted(native.node(root,fl,'x',1),root['hands'],'x')
    raw=native.node(root,public,'x x/',0)['wr'][1]
    weighted={native.cardkey(h) for h,w in zip(root['hands'][1],raw,strict=True) if w>1e-4}
    assert hands <= live_hero & weighted and len(hands)==6
    turn={};rows={}
    for mode in MODES:
        d=folder/('Qc-'+mode)
        g=json.loads((d/'result.json').read_bytes())
        j=json.loads((d/'job.json').read_bytes())
        assert (sha((d/'job.json').read_bytes()),sha((d/'result.json').read_bytes()))==tuple(claim['policies'][mode][key] for key in ('job_sha256','source_sha256'))
        assert (j['turn'],j['line0'],j['pot'],j['stack'])==('Qc',['x','x','/'],1650,9250)
        n=native.node(g,public,'x x/x',1)
        turn[mode]={a:sorted(''.join(h) for h in hands&native.accepted(n,g['hands'],a)) for a in n['acts']}
        board_rows=claim['policies'][mode]['boards']
        assert len(board_rows)==16 and set(board_rows)=={public+r for r in gate['selected_rivers']}
        rows[mode]={}
        for board,r in sorted(board_rows.items()):
            reach=r['reach']
            assert reach['public_board']==board and reach['acting_seat']==1 and reach['line']==native.LINE
            assert reach['compatible_hole_card_pairs']>=reach['strict_legal_combos']>0 and 'b50' in reach['source_actions']
            rows[mode][board]=dict(strict_legal_combos=reach['strict_legal_combos'],compatible_hole_card_pairs=reach['compatible_hole_card_pairs'],
                displayed_btn_hands=sorted(r['co_by_displayed_btn']),halfpot=reach['b50'])
    assert turn['gto']['x']==['8c8h','8d8h','8h8s'] and not turn['exp_ip']['x']
    assert turn['exp_ip']['b50']==sorted(''.join(h) for h in hands)
    assert [sum(bool(v['displayed_btn_hands']) for v in rows[m].values()) for m in MODES]==[11,0]
    assert sum(v['halfpot']['candidate'] for v in rows['exp_ip'].values())==9
    return turn,rows


def publish(a):
    out=a.output.resolve()
    assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    static=Path(native.__file__).resolve().parents[1]
    for name,pin in source.BLOBS.items():
        blob=subprocess.check_output(['git','hash-object',str(static/name)],text=True).strip()
        assert blob==pin,name
    reg=Path('data/nl2_hu_multiboard_status_current.json')
    before=reg.read_bytes();rec=json.loads(before)['records'][native.MODEL]
    assert (rec['frequency_rank'],rec['solver_profile'])==(309,native.SPOT)
    auth_raw=(a.archives/'receipt.json').read_bytes()
    assert sha(auth_raw)==RECEIPT_SHA and json_bytes(source.validate(json.loads(auth_raw)))==auth_raw
    raw=(a.archives/(str(source.ARTIFACT)+'.zip')).read_bytes()
    assert sha(raw)==source.DIGEST and len(raw)==json.loads(auth_raw)['artifacts'][0]['size_in_bytes']
    with TemporaryDirectory(prefix='b797-replay-') as tmp:
        folder=Path(tmp)
        names=unpack_original(raw,folder)
        assert names=={'original-flop.json','original-flop.job.json','rendered-routes.json','proof.json'}|{
            'Qc-'+m+'/'+f+'.json' for m in MODES for f in ('job','result')}
        original_hashes={n:sha((folder/n).read_bytes()) for n in sorted(names)}
        assert original_hashes['original-flop.json']==native.ROOT_SHA and original_hashes['original-flop.job.json']==native.ROOT_JOB_SHA
        native.run(SimpleNamespace(solver=a.solver,output=folder,driver=None,preflight=False))
        assert original_hashes=={n:sha((folder/n).read_bytes()) for n in sorted(names)}
        claim=json.loads((folder/'proof.json').read_bytes())
        assert claim['selected'] is None and not claim['common']
        assert (claim['positive_distinct_flops'],claim['locked_public_boards'],claim['joint_halfpot_assessed'],claim['halfpot_candidates'])==(0,16,16,9)
        turn,rows=verify_turn(folder,claim,json.loads((folder/'original-flop.json').read_bytes()))
    ev=out/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    (ev/ARCHIVE).write_bytes(raw)
    (out/'nl2_hu_b797_source_manifest.json').write_bytes(auth_raw)
    partial_group=dict(rank=309,model_id=native.MODEL,boards=[],pins=[],candidate_flop=native.FLOP,turn=native.TURN,
        policy_turn_actions_for_upstream_btn_hands=turn,upstream=claim['gate'],failure_reason=WHY,
        source_archive=ARCHIVE,source_sha256=source.DIGEST,original_proof_sha256=original_hashes['proof.json'])
    (partial/'b797_rank309.json').write_bytes(json_bytes(partial_group))
    medium=dict(schema='NL2_HU_B797_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={},assessed_public_boards=rows,
        model_id=native.MODEL,source_run=source.RUN,archive_sha256=source.DIGEST,
        policy_sources={m:{k:claim['policies'][m][k] for k in ('job_sha256','source_sha256')} for m in MODES},
        measured_lock_application=claim['policies']['exp_ip']['applied'])
    (partial/'b797_rank309_locked_medium.json').write_bytes(json_bytes(medium))
    result=dict(schema='NL2_HU_B797_R309_VERIFIED_CHECKED_QC_V1',rank=309,model_id=native.MODEL,source_run=source.RUN,
        source_head=source.HEAD,job=source.JOB,artifact=source.ARTIFACT,archive_sha256=source.DIGEST,source_files_sha256=original_hashes,
        original_flops_assessed=1,positive_distinct_flops=0,cert_eligible_ranks=[],selected=None,
        locked_public_boards=16,joint_halfpot_assessed=16,halfpot_candidates=9,gto_displayed_rivers=11,nl2_displayed_rivers=0,
        rejected_at='exp_ip BTN turn check',preserved_b581_original_zip_sha256=native.ARCHIVE_SHA)
    (out/'nl2_hu_b797_results.json').write_bytes(json_bytes(result))
    assert before==reg.read_bytes()
    print(json.dumps({k:result[k] for k in ('positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','archives','output'):p.add_argument('--'+name,type=Path,required=True)
    publish(p.parse_args())
