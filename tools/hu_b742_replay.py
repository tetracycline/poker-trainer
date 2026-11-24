"""Verify all six B739 turn policies and preserve the two positive rank108 flops."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b467_river_source_gate import json_bytes,sha,compact
from hu_b710_publish import unpack_original
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
import hu_b739_rank108 as native

RUN=45331727303
HEAD='b970b1d1f94b7a3e143c2d2f1220fcf69a85021f'
WORKFLOW='.github/workflows/nl2-hu-b739-rank108-turns.yml'
ROUTE='tools/hu_b739_rank108_routes.cjs'
FILES={WORKFLOW:'424315d421f35a86bab12342da5deec17ca9a7f9',ROUTE:'f3e413e029542819ad0c011196c6fe8984840b30','tools/hu_b739_rank108.py':'80d942e394270c0a1fece4a01ec89b9121e92d79'}
PINS={'2c2d4h':(14892591803,138234269317,'90a3b17cbcccc70f414f6207cf3f9dbde3721cdcf14c1beb093374067c3c0d7f'),
      '3s3h2d':(14892253160,138234269259,'4127bea4146cbb05f4e65dfe574c4ac74d6a7e65a631d13a72384affab968aa5'),
      '4s4h2d':(14892408047,138234268890,'70513e76d4e64bb067144ebbd07a6d39faa457cd97121bce705315c782e0b94a')}
STEPS=['Verify the exact BB lead, CO raise and two-seat reach on the original GTO roots','Build the pinned native solver',
       'Extract missing raise-call boundary weights, verify every old node and solve new priced turns','Run actions/upload-artifact@v4']


def read(p):return json.loads(p.read_bytes())


def authenticate(d):
    r=run_receipt(d['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(d['jobs'])==len(d['artifacts'])==len(PINS)==3
    for f,(aid,jid,digest) in PINS.items():
        a,=[x for x in d['artifacts'] if x['id']==aid];j,=[x for x in d['jobs'] if x['id']==jid]
        out['jobs'].append(job_receipt(j,r,jid,'solve ('+f+')',STEPS));out['artifacts'].append(artifact_receipt(a,r,aid,'B739-R108-'+f,digest))
    return out


def replay(f,folder,raw,route,solver):
    aid,jid,digest=PINS[f];assert sha(raw)==digest
    names=unpack_original(raw,folder);out=folder/'proof.json';orig=out.read_bytes();d=json.loads(orig)
    routebytes=(folder/'routes.json').read_bytes();original_route=json.loads(routebytes)
    assert d['rendered_route_sha256']==sha(routebytes) and original_route['registry_spr']==10.695
    assert route['registry_spr'] in (10.695,9.525) and dict(route,registry_spr=10.695)==original_route
    assert (d['flop'],d['rank'],d['model'],d['line'],d['actual_spr'])==(f,108,native.MODEL,native.LINE,9.525)
    expected={'proof.json','routes.json','boundary/job.json','boundary/result.json'}
    for t in d['turns']:
        for mode in ['gto']+(['exp_oop'] if 'nl2' in t else []):
            expected|={t['turn']+'/'+mode+'/'+s for s in ('result.json','job.json')}
    assert expected==names
    native.main(SimpleNamespace(flop=f,solver=solver,output=folder,routes=folder/'routes.json',driver=None,preflight=False))
    assert out.read_bytes()==orig
    root=read(folder/'boundary/result.json')
    old,oj,tj,m,origin=native.original(f)
    index={(n['line'],n['board'],n['player']):n for n in root['nodes']}
    for n in old['nodes']:assert n==index[(n['line'],n['board'],n['player'])]
    assert len(index)==len(old['nodes'])+2
    turns=[]
    for t in d['turns']:
        turn=t['turn'];lim,=[n for n in root['nodes'] if n['line']==native.LINE+'/' and n['board'].endswith(turn)]
        assert (lim['pot'],lim['bets'],lim['player'])==(1000,[375,375],0) and all(any(w>1e-4 for w in wr) for wr in lim['wr'])
        rows={}; hands={}
        for version,key,hashkey in [('gto','gto','source_gto_sha256'),('exp_oop','nl2','source_nl2_sha256')]:
            if key not in t:continue
            part=folder/turn/version
            job=read(part/'job.json');game=read(part/'result.json');game.update(line0=native.LINE,turn=turn)
            assert sha((part/'result.json').read_bytes())==t[hashkey]
            for i,k in enumerate(('oop_w','ip_w')): assert job[k]==[[h,w] for h,w in zip(root['hands'][i],lim['wr'][i],strict=True) if w>1e-4]
            n,=[n for n in game['nodes'] if (n['line'],n['player'])==(native.LINE+'/',0)]
            p=native.proof(root,game,n,native.game_reach(root,game)[0]);assert p==t[key]['reach']
            mask=base64.b64decode(p['compatible_action_mask_b64'],validate=True)
            shown={}
            for i,(h,b) in enumerate(zip(game['hands'][0],mask,strict=True)):
                fc,tc=[native.hand_cell(h,n['board'][:l]) for l in (6,8)]
                if fc[0] not in route['flop'] or tc[0] not in route['turn']:continue
                label=route['turn'][tc[0]];action=native.ACTIONS[label]
                if not b&(1<<n['acts'].index(action)):continue
                fq=[max(0.,n['strat'][j*len(mask)+i]) for j in range(len(n['acts']))]
                assert sum(fq)>0
                shown[''.join(native.cardkey(h))]=dict(displayed=label,flop_class=fc[1],turn_class=tc[1],accepted_mask=b,
                    action_order=n['acts'],strategy={a:round(w/sum(fq),7) for a,w in zip(n['acts'],fq,strict=True)})
            assert sorted(shown)==t[key]['displayed_hands']
            hands[key]=shown;rows[key]=dict(source_sha256=t[hashkey],job_sha256=sha((part/'job.json').read_bytes()),reach=p)
        common=sorted(hands['gto'].keys()&hands.get('nl2',{}).keys())
        assert common==t.get('shared_displayed_hands',[])
        turns.append(dict(turn=turn,public_board=lim['board'],root_boundary_sha256=sha(compact(lim)),policies=rows,
            measured_lock=t.get('measured_lock'),shared_displayed_hands={h:{k:v[h] for k,v in hands.items()} for h in common}))
    return dict(flop=f,source_run=RUN,source_job=jid,source_artifact=aid,source_digest=digest,original_parent=origin,
                preserved_original_source_nodes=len(old['nodes']),root_source_sha256=d['boundary_source_sha256'],proof_sha256=sha(orig),
                positive_distinct_flops=d['positive_distinct_flops'],turns=turns)


def main(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in FILES.items():assert subprocess.check_output(['git','hash-object',path],text=True).strip()==digest
    auth=authenticate(read(a.receipts));stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';ev.mkdir(parents=True)
    route=json.loads(subprocess.check_output(['node',ROUTE]));rows=[]
    with TemporaryDirectory(prefix='b742-') as tmp:
        for f,(aid,jid,digest) in PINS.items():
            name='NL2_B739_R108_'+f.upper()+'.zip';file=a.archives/f'{aid}.zip'
            raw=(file if file.is_file() else a.archives/name).read_bytes();assert sha(raw)==digest
            rows.append(replay(f,Path(tmp)/f,raw,route,a.solver.resolve()))
            (ev/name).write_bytes(raw)
    ts=[t for w in rows for t in w['turns']]
    pos=[w['flop'] for w in rows if any(t['shared_displayed_hands'] for t in w['turns'])]
    assert pos==['3s3h2d','4s4h2d'] and sum(w['positive_distinct_flops'] for w in rows)==2
    locked=[t['policies']['nl2']['reach'] for t in ts if 'nl2' in t['policies']]
    actual=[r for r in locked if r['compatible_hole_card_pairs']>0 and r['b50'] is not None]
    assert len(locked)==len(actual)==3 and not any(r['b50']['candidate'] for r in actual)
    (stage/'nl2_hu_b742_source_receipts.json').write_bytes(json_bytes(auth))
    (ev/'partial').mkdir()
    (ev/'partial/b742_rank108.json').write_bytes(json_bytes(dict(rank=108,model_id=native.MODEL,source_run=RUN,source_head=HEAD,
        distinct_verified_positive_flops=pos,source_price_in_chips=[1000,9525],turn_source_spr=9.525,workers=rows,
        actor_locked_public_boards=len(locked),halfpot_joint_assessed=len(actual),nonpolarized_candidates=0,
        publisher_native_solves_repeated=0,cert_eligible_ranks=[])))
    print(json.dumps(dict(positive_flops=pos,lock=len(locked),medium=len(actual),candidates=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--solver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--archives',type=Path,default=Path('data/solver_evidence'));p.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b742_source_receipts.json'))
    main(p.parse_args())

