"""Replay eight original GTO BB leads shared by the rank106/107 river routes."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import json_bytes
from hu_b715_collect import api
from hu_sequential_cfr_reach import accepted

HEAD = '4e5bb6450f2d96abe4eea43a00ae2d159ca6a67e'
MODELS = {106:'ln-ipfr-r_model-5ce65m',107:'ln-ipfr-r_model-ujl14x'}
PINS = {'4s4h2d': (14752918562,
            45019019774,
            '6fb740e5d8cc927471a74f018b5daf19aed8424d',
            'nl2-multiboard-B382_R107-BTN_BB-4s4h2d-gto',
            '0c65a74939d4bb620320f535773543abc3d1068674b0d305eb336ccf72d975a0'),
 '7s5h3d': (14752561398,
            45017142943,
            '80ce82befa1b23cec0ca927587ac69edb7170f95',
            'nl2-multiboard-B374_R107-BTN_BB-7s5h3d-gto',
            '09d99dd11f6f32dd872dad5d36695b0c1e16c9b6bc6bda61ab56e39af5c27a8e'),
 '9s6h3d': (14753465435,
            45018856098,
            '9c0e2c6353e4cb368570434651629b7f43178074',
            'nl2-multiboard-B381_R107-BTN_BB-9s6h3d-gto',
            '7f8487d06b9724ec0f9ced29ec53912c4839376117eac01ed5cd64048e0fa105'),
 'As9h2d': (14754399840,
            45023132316,
            '9ed2c11372b1bd87eededeb503e53332c8a11871',
            'nl2-multiboard-B387_R107_GTO_FIRST-BTN_BB-As9h2d-gto',
            'd534da19c0f927de828705826749fcb65882c24073eb4f6a079c52e670962c24'),
 'Jh9d6s': (14628385508,
            44732810327,
            'e33eb6200a79be505804028059c8a7f6b28f62fd',
            'nl2-multiboard-B4_MICRO-BTN_BB-gto-Jh9d6s',
            '36b9cbd95ffe8d0a6356a01876778e1e93ac4c1e4a046a59507ee92c9f45292b'),
 'Js9h4d': (14754258840,
            45023132316,
            '9ed2c11372b1bd87eededeb503e53332c8a11871',
            'nl2-multiboard-B387_R107_GTO_FIRST-BTN_BB-Js9h4d-gto',
            'becbed87b2ab9b57d62598614087cf4ccbd9b01973a00dbe787bccb932b374d0'),
 'KsQh4d': (14753000740,
            45017142943,
            '80ce82befa1b23cec0ca927587ac69edb7170f95',
            'nl2-multiboard-B374_R107-BTN_BB-KsQh4d-gto',
            '1b42b977662900a6b5a0ef4c27ef0bd9eab01672b04682160d02b4d2eb4626d8'),
 'QsJh4d': (14755175780,
            45023132316,
            '9ed2c11372b1bd87eededeb503e53332c8a11871',
            'nl2-multiboard-B387_R107_GTO_FIRST-BTN_BB-QsJh4d-gto',
            '7dcd39364818b77937b0e9af5b2907907a353e6715f1536e56c3a3741ded2589')}
digest = lambda raw:hashlib.sha256(raw).hexdigest()


def audit(folder):
    registry = json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    routes = json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes']
    for rank,model in MODELS.items():
        assert (registry[model]['frequency_rank'],registry[model]['solver_profile']) == (rank,'BTN_BB')
        assert routes[model]['seat']==1 and routes[model]['streets']==['bet c','x b'+('75' if rank==106 else '50')+' c','x']
    results = []
    for flop,(aid,run,head,name,archive_digest) in sorted(PINS.items()):
        raw = (folder/(str(aid)+'.zip')).read_bytes()
        assert digest(raw)==archive_digest
        with ZipFile(folder/(str(aid)+'.zip')) as archive:
            files = archive.namelist()
            assert len(files)==len(set(files))
            pins = {archive.read(n).decode().strip() for n in files if n.endswith('.txt') and n.startswith('evidence/')}
            assert {SOLVER,RUST}<=pins
            man, = [n for n in files if n.startswith('evidence/BTN_BB-') and n.endswith('.json')]
            manifest = json.loads(archive.read(man))
            assert (manifest['spot'],manifest['version'],manifest['flop'],manifest['failures'])==('BTN_BB','gto',flop,[])
            assert manifest['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
            path = 'solver/postflop/'+manifest['file_flop']
            root_raw = archive.read(path);job_raw = archive.read(path[:-5]+'.job.json')
            assert digest(root_raw)==manifest['file_flop_sha256']
            root,job = json.loads(root_raw),json.loads(job_raw)
            assert (root['flop'],root['pot'],root['stack'])==(flop,550,9750)
            assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
            lead, = [n for n in root['nodes'] if n['line']=='' and n['player']==0 and len(n['board'])==6]
            assert 'b33' in lead['acts'] and lead['bets']==[0,0] and lead['pot']==550
            assert not accepted(lead,root['hands'],'b33')
            offered, = [n for n in root['nodes'] if n['line']=='b33' and n['player']==1 and len(n['board'])==6]
            assert (offered['pot'],offered['bets'])==(732,[182,0])
            results.append(dict(flop=flop,source_run=run,source_head=head,artifact_id=aid,artifact_name=name,artifact_sha256=archive_digest,
                root_sha256=digest(root_raw),root_job_sha256=digest(job_raw),flop_oop_menu=job['flop_oop'],gto_gap_pct=root['info']['gto_expl_pct'],
                bb_eligible_one_third_hands=0,btn_eligible_call_hands=len(accepted(offered,root['hands'],'c'))))
    return dict(schema='NL2_B725_R106_R107_SHARED_BB_THIRD_POT_ANCESTRY',checked_registry_head=HEAD,rows=results,
        original_gto_flops=len(results),flops_with_positive_joint_ancestry=0,actor_locked_boards_added=0,
        half_pot_boards_assessed=0,native_solves_repeated=0,
        scope='The eight original BTN_BB GTO roots reject the BB one-third lead before the BTN call. Only these exact board and tree pairs are excluded.')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--archives',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--download',action='store_true');a=cli.parse_args()
    if a.download:
        a.archives.mkdir(parents=True,exist_ok=True)
        for aid,run,head,name,expected in PINS.values():
            archive=a.archives/(str(aid)+'.zip')
            if archive.exists():
                assert digest(archive.read_bytes())==expected
                continue
            metadata=json.loads(api(f'actions/artifacts/{aid}'))
            origin=metadata['workflow_run']
            assert (origin['id'],origin['head_sha'],origin['repository_id'],metadata['name'],metadata['digest'])==(run,head,1438346845,name,'sha256:'+expected)
            raw=api(f'actions/artifacts/{aid}/zip');assert digest(raw)==expected;archive.write_bytes(raw)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(json_bytes(audit(a.archives)))
