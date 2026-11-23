"""Verify three SB three-bet-pot checked lines and their independent conditional NL2 solves."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision, load_original, prepare_job, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board


PINS=Path('data/nl2_hu_b499_archives.json')
REPORT=Path('data/nl2_hu_b499_sb3_checked.json')
MEDIUM=Path('data/nl2_hu_b499_locked_medium.json')
BOARDS={
    'KsQh4d':('Tc',['4c','3h'],{'gto':14599605695,'exp_oop':14599228790,'exp_ip':14599049013}),
    'Ks7h2d':('9d',['5s','8h'],{'gto':14593123141,'exp_ip':14594300169}),
    'As7h3d':('Kd',['Qs','3s'],{'gto':14528582176}),
}
NEW=(('Ks7h2d','exp_oop'),('As7h3d','exp_oop'),('As7h3d','exp_ip'))
MODELS={82:('ln-3bp-3b_t_model-6vpmec','x x/',0),156:('ln-3bp-3c_t_model-1v9gtc3','x x/x',1),301:('ln-3bp-3c_r_model-1av2gz9','x x/x x/x',1)}


def code(flop,version):
    return f'B499_SB3_{flop.upper()}_{version.upper()}'


def check_pair(model,g,e,public,line,seat,gr,er):
    assert gr['source_actions']==er['source_actions'] and 'b50' in gr['source_actions']
    for s,r in ((g,gr),(e,er)):
        assert r['source_sha256']==s['source_sha256'] and r['public_board']==public and r['line']==line and r['acting_seat']==seat
        assert r['strict_legal_combos']>0 and summarize(r)['compatible_hole_card_pairs']>=r['strict_legal_combos']
        sub=s['subgame'];n,=[x for x in sub['nodes'] if (x['line'],x['board'],x['player'])==(line,public,seat)]
        nextline=line+('' if line.endswith('/') else ' ')+'b50'
        child,=[x for x in sub['nodes'] if (x['line'],x['board'],x['player'])==(nextline,public,1-seat)]
        assert n['pot']==2100 and child['pot']==3150 and child['bets'][seat]-n['bets'][seat]==1050
        assert abs((sub['stack']/n['pot'])/model['assumed_model_node_spr']-1)<.05
    assert er['subgame_applied_rust_lock_nodes']>0 and er['lock_scope']['observed_marginal_source_nodes']>0


def qualified(r):
    return r and r['status']=='POSITIVE_JOINT_REACH' and 0<=r['gto_gap_pct']<=.5 and (
        r['version']=='gto' or (0<=r['locked_hero_gap_pct']<=.5 and r['lock_scope']['observed_marginal_source_nodes']>0))


def source_artifacts(work,run,head):
    ids={}
    expected={code(f,v) for f,v in NEW}
    for info in json.loads((work/'list.json').read_bytes())['artifacts']:
        name=info['name']
        if name not in expected:continue
        assert (info['workflow_run']['id'],info['workflow_run']['head_sha'],info['workflow_run']['repository_id'])==(run,head,1438346845)
        archive=work/f"{info['id']}.zip";digest=sha(archive.read_bytes())
        assert 'sha256:'+digest==info['digest'] and name not in ids
        native=f'NL2_{name}.json.gz'
        with ZipFile(archive) as z:
            assert z.namelist()==[native]
            folder=work/name;folder.mkdir(exist_ok=True);(folder/native).write_bytes(z.read(native))
        ids[name]=dict(id=info['id'],head=head,sha256=digest,run=run)
    return ids


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals',type=Path);p.add_argument('--solver',type=Path)
    p.add_argument('--list-artifacts',action='store_true');p.add_argument('--preflight',action='store_true')
    p.add_argument('--flop',choices=BOARDS);p.add_argument('--version',choices=('exp_oop','exp_ip'))
    p.add_argument('--driver',type=Path);p.add_argument('--work',type=Path);p.add_argument('--run-id',type=int);p.add_argument('--head')
    args=p.parse_args();pins=json.loads(PINS.read_bytes())
    if args.list_artifacts:
        print(BOARDS[args.flop][2]['gto'] if args.flop else ' '.join(pins));return
    solver=args.solver.resolve();assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==SOLVER
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==POOL;pool=json.loads(poolraw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    def original(f,v):
        turn,_,versions=BOARDS[f];aid=versions[v]
        return load_original(args.originals,aid,pins[str(aid)],'SB3_BTN',f,turn,v,pot=2100,stack=9000,pipeline=pipeline,ranges=ranges)
    if args.driver:
        assert args.run_id>0 and (args.flop,args.version) in NEW
        driver=args.driver.resolve();assert driver==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',str(solver/'postflop/postflop-solver'),'rev-parse','HEAD'],text=True).strip()==RUST
        g=original(args.flop,'gto');out=solve_native(g,args.version,pool,pipeline,args.work,driver,args.run_id,code(args.flop,args.version))
        replay_native(g,args.version,pool,pipeline,out,args.run_id,code(args.flop,args.version));return
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    evidence={f:{v:original(f,v) for v in versions} for f,(_,_,versions) in BOARDS.items()}
    originals={} if args.preflight else source_artifacts(args.work,args.run_id,args.head)
    missing={};eligible={};runs={};attempts={};scopes={}
    for f,v in NEW:
        g=evidence[f]['gto'];job,meta=prepare_job(g,v,pool,pipeline);assert job['hero']==int(v=='exp_ip') and meta
        if args.preflight:continue
        assert args.run_id>0
        prefix=code(f,v);path=args.work/prefix/f'NL2_{prefix}.json.gz'
        if prefix not in originals:missing[prefix]='NO_COMPLETED_CONDITIONAL_OUTPUT';continue
        dest=EVIDENCE/path.name;shutil.copyfile(path,dest)
        src=replay_native(g,v,pool,pipeline,dest,args.run_id,prefix)
        evidence[f][v]=dict(identity=dict(g['identity'],conditional_run=args.run_id,conditional_job_sha256=sha(compact(job)),
                                        conditional_source_sha256=src['source_sha256'],conditional_archive_sha256=src['archive_sha256'],
                                        conditional_upload=originals[prefix],
                                        frozen_gto_parent_run=g['source']['run'],frozen_gto_parent_sha256=g['identity']['root_sha256']),source=src)
        scopes[prefix]=dict(first_match_verification=src['measured_lock_application'],applied_rust_rates=src['applied_rust_rates'])
    gto_rows={};locked_rows={}
    for rank,(mid,line,seat) in MODELS.items():
        model=registry[mid];assert (model['frequency_rank'],model['solver_profile'],model['family'])==(rank,'SB3_BTN','3BP')
        ver='exp_ip' if seat else 'exp_oop';selected=[];attempts[str(rank)]=[]
        for flop,(turn,rivers,_) in BOARDS.items():
            bank=evidence[flop];original_g=bank['gto'];g=original_g['source'];assert g['subgame']['rivers']==rivers
            ecase=bank.get(ver);e=ecase['source'] if ecase else None;existing=False
            for end in (rivers if rank==301 else ['']):
                public=original_g['public']+end
                gr=audit_decision(g,public,line,seat,original_g['identity']['root_sha256'])
                er=audit_decision(e,public,line,seat,ecase['identity']['root_sha256']) if e else None
                attempts[str(rank)].append(dict(flop=flop,public_board=public,line=line,gto=gr,lock=er))
                if existing or not (qualified(gr) and qualified(er)):continue
                check_pair(model,g,e,public,line,seat,gr,er)
                if args.preflight:
                    selected.append(flop);existing=True;continue
                b,pin=emit_board(model,g,e,public,line,texture(flop));assert b and pin
                assert (pin['GTO_strict_combos'],pin['NL2_strict_combos'])==(gr['strict_legal_combos'],er['strict_legal_combos'])
                pin.update(original_gto_archive=original_g['identity'],original_lock_archive=ecase['identity'])
                if e.get('verified_gto_parent'):
                    lock=b['nl2_locked_variants'][0];lock.update(variant_label='原始 GTO 翻牌範圍，轉河牌 NL2 局部鎖頻',
                          gto_parent_source_run_id=g['run'],gto_parent_source_sha256=e['verified_gto_parent']['sha256'],
                          root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=er['subgame_applied_rust_lock_nodes'])
                selected.append((b,pin,gr,er));existing=True
        eligible[str(rank)]=len(selected)
        if args.preflight:continue
        if len(selected)<3:continue
        assert len(selected)==3 and len({b['flop'] for b,p,g,e in selected})==3
        group=dict(model_id=mid,rank=rank,boards=[b for b,p,g,e in selected],pins=[p for b,p,g,e in selected])
        (EVIDENCE/f'reverified/rank{rank}.json').write_bytes(json_bytes(group));runs[str(rank)]=[p for b,p,g,e in selected]
        for b,p,g,e in selected:
            gto_rows[source_key(mid,g)]=g;locked_rows[source_key(mid,e)]=dict(e,gto=g)
    if args.preflight:
        assert eligible=={'82':1,'156':2,'301':2};print('Verified original flop pairs by rank:',eligible);return
    REPORT.write_bytes(json_bytes(dict(eligible_by_rank=eligible,reverified=runs,source_run_id=args.run_id,archive_list_sha256=sha(PINS.read_bytes()),
                                      original_source_artifacts=originals,observations=attempts,weighted_rust_lock_rates=scopes,unavailable=missing)))
    if locked_rows:MEDIUM.write_bytes(json_bytes(dict(schema='NL2_HU_B499_ORIGINAL_LOCKED_MEDIUM_V1',gto_references=gto_rows,references=locked_rows)))
    print('Paired distinct true flops:',eligible)


if __name__=='__main__':main()
