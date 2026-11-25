"""B843: receipt-pinned independent replay of seven completed priority artifacts.
No Rust invocation, no promotion, and no changes to any current registry cell.
"""
import argparse, importlib, json, subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt, job_receipt, artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes, sha
from hu_sequential_cfr_reach import accepted, cardkey, mask_at_node, game_reach
from hu_b483_locked_medium import proof

SOURCES = json.loads(r'''[
  {
    "batch": 839,
    "rank": 29,
    "run": 45527116296,
    "head": "5db0af332e8dbe84edc18284aad6543d748f2f9b",
    "wf": "nl2-hu-b839-rank29-monotone.yml",
    "worker": "hu_b839_rank29_new_monotone",
    "steps": [
      "Reject duplicated historical originals and wrong exact route before native work",
      "Build pinned original native driver",
      "Solve original river-barrel path and NL2 measured partial lock once",
      "Run actions/upload-artifact@v4"
    ],
    "pins": [
      [
        "AdJd7d",
        138913099276,
        14982762422,
        "7786c857ac24f6f407116e06126b7350928ba7585418a89cb4419b77f8e99d19"
      ],
      [
        "KdTd6d",
        138913098996,
        14982922780,
        "7948917d9dd1ca98376ca83bd1645725bf8b91903eaaf09cd3c28e583767f65f"
      ]
    ]
  },
  {
    "batch": 840,
    "rank": 57,
    "run": 45527191880,
    "head": "c97ab1e6decb8b4dd1484421fab8534de8be2cc8",
    "wf": "nl2-hu-b840-rank57-paired.yml",
    "worker": "hu_b840_rank57_new_paired",
    "steps": [
      "Preflight new native flop sources and exact SB action line",
      "Build native driver pinned to solved input",
      "Solve authentic GTO and partial measured NL2 opponent lock",
      "Run actions/upload-artifact@v4"
    ],
    "pins": [
      [
        "Ad6h6s",
        138913351913,
        14982203888,
        "561fd6f22168b686e8e24f4cb2cf50674a65b8b4341aaccde273771a61016929"
      ],
      [
        "Kh8d8s",
        138913351272,
        14983660946,
        "92fb7deadf389f051f0f304b4d94fafceca3ac0de01f7537953321ef9ce7a9c5"
      ]
    ]
  },
  {
    "batch": 837,
    "rank": 75,
    "run": 45521622280,
    "head": "845e126f3a5f163e6025a411b2eff9405727d3ed",
    "wf": "nl2-hu-b837-rank75-b833-root.yml",
    "worker": "hu_b837_rank75_b833_root",
    "steps": [
      "Reconstruct original held-out jobs and verify B809 two-seat witness",
      "Build the pinned native driver",
      "Solve the missing conditional games and replay evidence from native output",
      "Preserve original jobs, decisions and range reconstruction"
    ],
    "pins": [
      [
        "Td8d6d",
        138894634911,
        14981175247,
        "86ae0c8d45c5c6418ad5bdc00bfb2d97b33f5d76a28ae245280f711d58a6be97"
      ]
    ]
  },
  {
    "batch": 841,
    "rank": 80,
    "run": 45527456112,
    "head": "a64d376fce5068f92789b903526186b661b5682a",
    "wf": "nl2-hu-b841-rank80-originals.yml",
    "worker": "hu_b841_rank80_new_originals",
    "steps": [
      "Preflight preserved source and all historical flop suit-orbits",
      "Compile pinned Rust driver",
      "Solve original b33 call and measured NL2 partial lock exactly once",
      "Run actions/upload-artifact@v4"
    ],
    "pins": [
      [
        "6c6d3h",
        138914220210,
        14983542296,
        "3a648696315c00c5820288270f4b04468aaab2efa4af022ad79e5ad27eb4edb0"
      ],
      [
        "KdJd5c",
        138914220593,
        14983332243,
        "8f87058407d926d87606a38a55b1420069c130ecfbfdbd17ab51aeae6249339c"
      ]
    ]
  }
]''')
def read(p): return json.loads(p.read_bytes())
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for s in SOURCES:
        ep='actions/runs/'+str(s['run'])
        wf='.github/workflows/'+s['wf']
        run=run_receipt(json.loads(api(ep)),s['run'],s['head'],wf)
        assert run['run_attempt']==1
        js=json.loads(api(ep+'/jobs?per_page=100'))
        ars=json.loads(api(ep+'/artifacts?per_page=100'))
        assert js['total_count']==ars['total_count']==len(s['pins'])
        rec=dict(run=run,jobs=[],artifacts=[],blobs={})
        for path in (wf,'tools/'+s['worker']+'.py'):
            pin=json.loads(api('contents/'+path+'?ref='+s['head']))['sha']
            assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
            rec['blobs'][path]=pin
        for flop,jid,aid,digest in s['pins']:
            j,=[x for x in js['jobs'] if x['id']==jid]
            rec['jobs'].append(job_receipt(j,run,jid,'solve ('+flop+')',s['steps']))
            a,=[x for x in ars['artifacts'] if x['id']==aid]
            name=f"B{s['batch']}-R{s['rank']}-{flop}"
            a=artifact_receipt(a,run,aid,name,digest)
            raw=api('actions/artifacts/'+str(aid)+'/zip')
            assert sha(raw)==digest and len(raw)==a['size_in_bytes']
            (folder/(str(aid)+'.zip')).write_bytes(raw)
            rec['artifacts'].append(a)
        receipts.append(rec)
    (folder/'receipt.json').write_bytes(json_bytes(receipts))

def seat_sets(root, sub, node):
    board=node['board']; actor=node['player']; dead={board[i:i+2] for i in range(0,len(board),2)}
    result=[]
    for seat in (0,1):
        hands=sub['hands'][seat]
        keep={cardkey(h) for h,w in zip(hands,node['w'][seat],strict=True) if w>1e-4 and dead.isdisjoint(cardkey(h))}
        if seat==actor:
            keep &= {cardkey(h) for h,m in zip(hands,mask_at_node(node,sub['hands']),strict=True) if m}
        for st,history in enumerate(node['line'].split('/')):
            game=root if st==0 else sub
            pub=board[:6+2*st]
            parents={n['line']:n for n in game['nodes'] if n['board']==pub}
            actions=history.split()
            for i,act in enumerate(actions):
                prefix='/'.join(node['line'].split('/')[:st]+[' '.join(actions[:i])])
                parent=parents[prefix]
                if parent['player']==seat: keep &= accepted(parent,game['hands'],act)
        result.append(keep)
    return result

def medium_counts(dest,claim,rank):
    if rank==75:
        return [claim[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')],[]
    root=read(dest/'flop/result.json')
    actor=1 if rank==80 else 0
    line=claim['line']
    mode='exp_ip' if actor else 'exp_oop'
    out=[]
    for turn in claim['turns']:
        t=turn['turn']; lp=dest/(t+'-'+mode)/'result.json'
        assert lp.exists()==turn['paired_policies']
        if not lp.exists():continue
        g=read(dest/(t+'-gto')/'result.json'); e=read(lp)
        assert e['info']['lock_stats'] and g['hands']==e['hands']
        for sub in (g,e):
            sub.update(line0=line.split('/')[0],turn=t)
        gn={n['board']:n for n in g['nodes'] if (n['line'],n['player'])==(line,actor)}
        en={n['board']:n for n in e['nodes'] if (n['line'],n['player'])==(line,actor)}
        assert set(gn)==set(en)
        gm=em=None
        for board in sorted(gn):
            x,y=gn[board],en[board]
            assert (x['pot'],x['bets'])==(y['pot'],y['bets'])
            gs,es=seat_sets(root,g,x),seat_sets(root,e,y)
            s0,s1=(a&b for a,b in zip(gs,es,strict=True))
            # A common pair must be the same two legal physical hands in both policies.
            witness=next(([list(a),list(b)] for a in sorted(s0) for b in sorted(s1) if set(a).isdisjoint(b)),None)
            row=dict(board=board,common_seat_counts=[len(s0),len(s1)],joint_witness=witness,
                     positive_halfpot_assessed=False,halfpot_candidate=False)
            if witness and 'b50' in x['acts'] and 'b50' in y['acts']:
                if gm is None:gm=game_reach(root,g)[0];em=game_reach(root,e)[0]
                gp=proof(root,g,x,gm);ep=proof(root,e,y,em)
                assert gp['b50'] is not None and ep['b50'] is not None
                row.update(positive_halfpot_assessed=True,
                    halfpot_candidate=bool(gp['b50']['candidate'] and ep['b50']['candidate']),
                    gto_halfpot=gp['b50'],locked_halfpot=ep['b50'])
            out.append(row)
    assert len({r['board'] for r in out})==len(out)
    return [len(out),sum(r['positive_halfpot_assessed'] for r in out),sum(r['halfpot_candidate'] for r in out)],out

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence'; partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json'); before=registry.read_bytes()
    recs=read(a.archives/'receipt.json'); assert len(recs)==len(SOURCES)
    totals=[0,0,0]; observations=[]
    with TemporaryDirectory(prefix='b843-') as tmp:
        for s,rec in zip(SOURCES,recs,strict=True):
            assert (rec['run']['id'],rec['run']['head_sha'])==(s['run'],s['head'])
            worker=importlib.import_module(s['worker'])
            for flop,jid,aid,digest in s['pins']:
                raw=(a.archives/(str(aid)+'.zip')).read_bytes()
                assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in rec['artifacts'])
                dest=Path(tmp)/str(aid);dest.mkdir()
                names=unpack_original(raw,dest)
                hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                claim=read(dest/'proof.json')
                worker.run(SimpleNamespace(solver=a.solver,output=dest,flop=flop,driver=None,preflight=False))
                actual=read(dest/'proof.json')
                assert actual==claim and actual['rank']==s['rank'] and actual['flop']==flop
                if s['rank']==75: assert actual['positive_distinct_flops']==0
                else: assert not any(t['checks'] for t in actual['turns'])
                counts,rows=medium_counts(dest,actual,s['rank'])
                assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
                assert counts[2]<=counts[1]<=counts[0]
                totals=[x+y for x,y in zip(totals,counts,strict=True)]
                name=f"NL2_B{s['batch']}_R{s['rank']}_{flop.upper()}.zip"
                (ev/name).write_bytes(raw)
                observations.append(dict(rank=s['rank'],batch=s['batch'],flop=flop,job=jid,
                    archive=name,artifact=aid,archive_sha256=digest,native_file_sha256=hashes,
                    proof=claim,lock_halfpot_counts=counts,common_reach_observations=rows))
    result=dict(source_runs=[s['run'] for s in SOURCES],source_artifacts=[o['artifact'] for o in observations],
        positive_distinct_flops=0,cert_eligible_ranks=[],native_repeated=0,
        locked_public_boards=totals[0],joint_halfpot_assessed=totals[1],halfpot_candidates=totals[2],
        unchanged_registry_sha256=sha(before),
        rank_counts=[dict(rank=o['rank'],flop=o['flop'],counts=o['lock_halfpot_counts']) for o in observations])
    (stage/'nl2_hu_b843_source_receipts.json').write_bytes(json_bytes(recs))
    (stage/'nl2_hu_b843_results.json').write_bytes(json_bytes(result))
    (partial/'b843_priority_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    assert before==registry.read_bytes()
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
