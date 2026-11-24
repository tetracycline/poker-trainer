"""Extend rank150 on new paired two-suit flops after an original A5-suited river check."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b724_rank150_rivers as source
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER='tools/hu_b743_rank150_paired.py'
BASE='854dfd8cc37fb3bcfb7481573a74bb78c3419120'
PRIOR='9410fbd73365fafacf681007f7bb425b747d317ae26a2eea15bee27c2c4df289'
GROUP='f14c92520889bdf41947971c99f674c82a5e0750'
CASES={
    '9h9d7h':[('2d','Ah5h','2c'),('3c','Ah5h','3s'),('4d','Ah5h','7c'),('2s','Ah5h','7d')],
    'TsTc6s':[('2d','As5s','2h'),('3h','As5s','3c'),('4c','As5s','6d'),('2c','As5s','6h')],
    'JdJh7d':[('2h','Ad5d','2c'),('3c','Ad5d','3s'),('4h','Ad5d','7c'),('2s','Ad5d','7h')],
}
HISTORICAL=set('2c2d4h 2s3h4d 2s4h6d 3c3d4h 3s3h2d 3s4h5d 4s4h2d 4s4h3d 4s4h3s 4s4h6d 5c5d2h 5s5h3d 6c4h2d 6s5h3d 6s5h4d 6s6h2d 7h6c4h 7h6d4s 7h6h4c 7s5h2d 7s5h3d 7s5h3s 7s5h4d 7s5s3d 7s5s3s 7s7h2d 8s7h5d 8s8h3d 9s6h3d 9s8h4d As7d4c As7h3d As9h4d AsQh8d Jc8d3h Jh9d6s Js9h4d Ks7h2d Ks7s2s KsJh4d KsQh4d Th7c4d 8s8h5s 9c9h6c Ts9s5h Kd9d4c Qh8h3s As7s2d 8s7s6d 6c5c4h 5d4d2c'.split())
BASE_GATE=source.parent_gate
BASE_SOLVE=source.solve


def prior(evidence):
    assert source.limp.git_blob('tools/hu_b724_rank150_rivers.py')==BASE
    group=evidence/'partial/b731_rank150.json'
    assert source.limp.git_blob(group)==GROUP
    p,=json.loads(group.read_bytes())['pins']
    assert (p['flop'],p['turn'],p['public_board'],p['archive_sha256'])==('9c9h6c','2d','6c9c9h2d2h',PRIOR)
    hand,=p['rendered_decision_hands']
    assert (hand['hand'],hand['displayed_suggestion'])==('5cAc','過')
    for v in ('gto','nl2'):
        assert hand[v]['accepted_actions']==['x'] and hand[v]['strategy']['x']>.97
    archive=evidence/'NL2_B724_R150_9C9H6C.zip'
    assert sha(archive.read_bytes())==PRIOR
    with ZipFile(archive) as z:
        proof=json.loads(z.read('proof.json'))
        original,=proof['turns']
        assert original['turn']=='2d' and original['common']=={'6c9c9h2d2h':['5cAc'],'6c9c9h2d6s':['5cAc']}
        for v in ('gto','exp_ip'):
            assert sha(z.read('2d-'+v+'/result.json'))==original['policies'][v]['source_sha256']
    return dict(prior_group_blob=GROUP,prior_zip_sha256=PRIOR,prior_proof_sha256=sha(json_bytes(proof)),
        original_hand=hand['hand'],two_positive_rivers=sorted(original['common']))


def ranked_gate(root,turn,route):
    parent,eligible,_,diagnostic=BASE_GATE(root,turn,route)
    options=list(eligible)
    configured,=[f for f in CASES if source.cards(f)==source.cards(root['flop'])]
    suit=configured[1]
    flank=configured[4]
    priority=[r for r in options if r[0] in (turn[0],flank) and r[1]!=suit]
    remaining=[r for r in options if r not in priority]
    slots=min(12-len(priority),len(remaining))
    assert slots>=0
    if slots==1:
        extra=remaining[:1]
    elif slots:
        extra=[remaining[round(i*(len(remaining)-1)/(slots-1))] for i in range(slots)]
    else:
        extra=[]
    rivers=priority+extra
    assert len(rivers)==len(set(rivers))==min(12,len(options))
    return parent,eligible,rivers,dict(diagnostic,preregistered_river_rule='TURN_OR_FLANK_PAIR_WITHOUT_COMPLETING_FLOP_SUIT_THEN_SPREAD',
        retained_eligible_priority_rivers=priority)


def checkpoint_root(args):
    # Write and upload the true original before any conditional study.
    target=args.output/'flop'
    assert args.driver and (not args.output.exists() or not any(args.output.iterdir()))
    with ZipFile(source.limp.TEMPLATE) as z:
        template=json.loads(z.read('original-flop.job.json'))
        manifest=json.loads(z.read('original-manifest.json'))
    source.limp.check_limp_source(dict(manifest=manifest,root_job=template,subgame_job=None))
    turns=[v[0] for v in CASES[args.flop]]
    job=dict(template,flop=args.flop,flop_oop='33%,50%,75%,100%',flop_ip='33%,50%,75%,100%',
        iters=2400,target_pct=.45,out='result.json',extract=[dict(prefix=[],street=True)]+[
        dict(prefix=prefix+[t],street=False,raw=True) for prefix in (['x','b33','c'],['b33','c']) for t in turns])
    root=BASE_SOLVE(target,job,args.driver)
    assert source.cards(root['flop'])==source.cards(args.flop) and (root['pot'],root['stack'])==(250,9900)
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    expected={l+t for l in ('x b33 c/','b33 c/') for t in turns}
    boundaries={n['line']+n['board'][-2:] for n in root['nodes'] if n.get('wr') and n['line'] in ('x b33 c/','b33 c/')}
    assert boundaries==expected
    ident=dict(flop=args.flop,worker_blob=source.limp.git_blob(WORKER),base_blob=BASE,
        original_root_sha256=sha((target/'result.json').read_bytes()),original_root_job_sha256=sha((target/'job.json').read_bytes()))
    (args.output/'checkpoint.json').write_bytes(json_bytes(ident))


def use_checkpoint(checkpoint):
    ident=json.loads((checkpoint/'checkpoint.json').read_bytes())
    def load_or_solve(folder,job,driver):
        if folder.name!='flop':
            return BASE_SOLVE(folder,job,driver)
        assert (job['flop'],source.limp.git_blob(WORKER),BASE)==(ident['flop'],ident['worker_blob'],ident['base_blob'])
        raw_job=(checkpoint/'flop/job.json').read_bytes()
        assert raw_job==compact(job) and sha(raw_job)==ident['original_root_job_sha256']
        raw=(checkpoint/'flop/result.json').read_bytes()
        assert sha(raw)==ident['original_root_sha256']
        folder.mkdir(parents=True)
        (folder/'job.json').write_bytes(raw_job)
        (folder/'result.json').write_bytes(raw)
        return BASE_SOLVE(folder,job,None)
    return load_or_solve


def run(args):
    evidence=args.prior_evidence
    origin=prior(evidence)
    new={suit_isomorphism_class(f) for f in CASES}
    assert len(new)==3 and new.isdisjoint({suit_isomorphism_class(f) for f in HISTORICAL})
    source.CASES=CASES
    source.parent_gate=ranked_gate
    if args.checkpoint_only:
        source.run(SimpleNamespace(**(vars(args)|{'preflight':True})))
        checkpoint_root(args)
        return
    if args.driver and not args.preflight:
        assert args.checkpoint, 'Use the separately preserved original root'
        source.solve=use_checkpoint(args.checkpoint)
    source.run(args)
    if args.preflight:
        return
    proof=args.output/'proof.json';result=json.loads(proof.read_bytes())
    assert result['source_worker_blob']==BASE
    result.update(schema='NL2_B743_R150_PAIRED_A5_SOURCE_V1',source_worker_blob=source.limp.git_blob(WORKER),
        base_worker_blob=BASE,selection_origin=origin,original_flop_roots_per_worker=1,
        extra_flop_native_solves_in_continuation=0)
    proof.write_bytes(json_bytes(result))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):cli.add_argument('--'+k,required=True,type=Path)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--checkpoint-only',action='store_true')
    cli.add_argument('--checkpoint',type=Path)
    cli.add_argument('--preflight',action='store_true')
    cli.add_argument('--prior-evidence',type=Path,default=Path('data/solver_evidence'))
    run(cli.parse_args())
