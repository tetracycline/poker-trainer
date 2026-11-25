"""B873 rank152: authenticate original archived GTO and IP measured-lock policies.
Read-only, no native solves; fail closed on absent job/ancestor, price, or action.
Preliminary source index is not certification; no registry write.
"""
import json, subprocess, sys
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
from collections import Counter
from hu_b859_limp_boundaries import api
from hu_b467_river_source_gate import sha,json_bytes
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted,cardkey
from verify_hu_multiboard_100bb import lock_scope

BRANCH='fix/nl2-hu-lines-audit-20261118'
MODEL='ln-ipc-t_model-1jnj1k6'
LINE='b75 r c/x'
B1=44666285424
ST=44522421850
HEAD={B1:'92c10f1d3ed037e04ca9b99feb702f2174ebd9af',ST:'369a6d17ec9e0261b2992366bed9b301a89b24b9'}
PINS={
 '8s8h3d':[(B1,14598504895,136056270785,'17f1f9d0c1e6e5bb1301873e4eb76e44e619dd23b5fe4d32d911fdd258020722'),(B1,14599910729,136056270404,'b69ac48b82f7bdd21573373ca076038bb5460664ff1e82382bf55ebfc7a28d28')],
 'Js9h4d':[(B1,14599361276,136056270468,'50f129112a18235d20dbc3938a7a2160c560b143216fb7e92270fa1d404fb6d7'),(B1,14598803503,136056270522,'a470b65019dfc72a1490f5ef7ea73e9be21efc60f0352cc2cc569b425c64c407')],
 'AsTh4d':[(ST,14529096110,135554164305,'fc8e17ff2ba07578928a6467a4e7b73721cf05c5747b44b9d440a2b51d1cc39f'),(ST,14528213401,135554164640,'43e4a1681039dacff31e4dab40503e800f1af06d6c22bb5dcbf07a6de3707647')]
}
GTO={'8s8h3d':'cc15da63fc34dfd70b7df32f59dbf697ba49060940acda9f66bf24c6f7602d4a','Js9h4d':'e43bd9d808dc949fcf29e8ee43a4c621dce98c91ae782ead31d5e8d9e27e50d3','AsTh4d':'f18452daac821e62f4a31888460c20e2477ae67c691252a00ebeb147101a06db'}
ACT={'過':'x','下注 ⅓':'b33','下注 1/3':'b33','下注 ½':'b50','下注 1/2':'b50','下注 ¾':'b75','下注 3/4':'b75','下注 1':'b100'}
def get(p):return json.loads(api(p))
def cards(b):return {b[i:i+2] for i in range(0,len(b),2)}
def live(g,n,s):return {cardkey(h) for h,w in zip(g['hands'][s],n['w'][s],strict=True) if w>1e-4 and cards(n['board']).isdisjoint(cardkey(h))}
def witness(h,v):return next(([ ''.join(a),''.join(b)] for a in sorted(h) for b in sorted(v) if set(a).isdisjoint(b)),None)
def pair_count(h,v):
    c=Counter(k for a in v for k in a)
    return sum(len(v)-c[a]-c[b]+((a,b) in v) for a,b in h)
def find(g,l,b):
    n=[n for n in g['nodes'] if n['line']==l and n['board']==b]
    assert len(n)<=1
    return n[0] if n else None
def download(flop,version,pin,out):
    run,aid,jid,digest=pin
    meta=get(f'actions/artifacts/{aid}');job=get(f'actions/jobs/{jid}');rr=get(f'actions/runs/{run}')
    name=f'nl2-multiboard-B1-SB_BB-{version}-{flop}' if run==B1 else f'nl2-stage2-SB_BB-{version}-0'
    jname=f'solve (SB_BB, {flop}, {version})' if run==B1 else f'solve (SB_BB, 0, {version})'
    assert (rr['head_sha'],rr['head_branch'],rr['status'],rr['conclusion'])==(HEAD[run],BRANCH,'completed','success')
    assert (job['run_id'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(run,HEAD[run],jname,'completed','success')
    assert (meta['name'],meta['digest'],meta['expired'],meta['workflow_run']['id'],meta['workflow_run']['head_sha'])==(name,'sha256:'+digest,False,run,HEAD[run])
    raw=api(f'actions/artifacts/{aid}/zip');assert len(raw)==meta['size_in_bytes'] and sha(raw)==digest
    (out/f'{aid}-receipt.json').write_bytes(json_bytes(dict(run=rr,job=job,artifact=meta)))
    cases={}
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None
        manifests=[(p,json.loads(z.read(p))) for p in z.namelist() if p.startswith('evidence/') and p.endswith('.json')]
        mf,m=next((p,m) for p,m in manifests if m.get('spot')=='SB_BB' and m.get('version')==version and any(c.get('flop',m.get('flop'))==flop for c in m.get('cases',[])))
        assert not m.get('failures')
        for case in m['cases']:
            if (case.get('flop',m.get('flop')),case['line'])!=(flop,'b75 r c'):continue
            fp='solver/postflop/'+(case.get('flop_json') or m['file_flop'])
            sp='solver/postflop/'+(case.get('sub_json') or case['source_path'])
            fr=z.read(fp);sr=z.read(sp)
            fs=case.get('flop_sha256') or m['file_flop_sha256'];ss=case.get('sub_sha256') or case['source_sha256']
            assert (sha(fr),sha(sr))==(fs,ss)
            if version=='gto' and ss!=GTO[flop]:continue
            root,sub=json.loads(fr),json.loads(sr)
            identity=dict(run=run,job=jid,artifact=aid,zip_sha256=digest,manifest_sha256=sha(z.read(mf)),root_sha256=fs,subgame_sha256=ss,turn=case['turn'])
            assert (root['flop'],sub['flop'],sub['turn'],sub['line0'])==(flop,flop,case['turn'],'b75 r c')
            jr={}
            for key,path in [('root',fp),('sub',sp)]:
                jp=path[:-5]+'.job.json'
                if jp in z.namelist():
                    jraw=z.read(jp);jr[key]=json.loads(jraw);identity[key+'_job_sha256']=sha(jraw)
            assert case['turn'] not in cases
            cases[case['turn']]=(root,sub,m,jr,identity)
    return cases
def evaluate(case,route,version):
    root,sub,m,jr,identity=case
    if set(jr)!={'root','sub'}:return dict(identity=identity,status='BLOCKED_MISSING_ORIGINAL_JOB'),None
    hero=None if version=='gto' else 1
    for k,g in [('root',root),('sub',sub)]:
        j=jr[k]
        if (j.get('hero'),j.get('rake_rate'),j.get('rake_cap'))!=(hero,.05,1000) or (j.get('pot'),j.get('stack'))!=(g['pot'],g['stack']):
            return dict(identity=identity,status='BLOCKED_JOB_ACTOR_OR_CHIP_MISMATCH'),None
        if not 0<=g['info']['gto_expl_pct']<=.5:return dict(identity=identity,status='BLOCKED_CONVERGENCE'),None
        if version=='exp_ip' and (not 0<=g['info'].get('hero_gap_pct',99)<=.5 or not g['info'].get('lock_stats')):
            return dict(identity=identity,status='BLOCKED_LOCK_OR_CONVERGENCE'),None
    f=next(n['board'] for n in root['nodes'] if n['line']=='')
    target=[n for n in sub['nodes'] if n['line']==LINE and n['player']==1 and len(n['board'])==8]
    if len(target)!=1:return dict(identity=identity,status='BLOCKED_TARGET_NOT_EXPORTED'),None
    n=target[0];b=n['board']
    actual=[n['pot']/100,(sub['stack']-max(n['bets']))/100]
    rendered=[route['pot'],route['stack']]
    info=dict(identity=identity,board=b,actor=1,line=LINE,source_actions=n['acts'],source_root_pot_stack=[root['pot']/100,root['stack']/100],actual_pot_stack=actual,rendered_pot_stack=rendered)
    if b[:6]!=f or b[6:]!=identity['turn']:return dict(info,status='BLOCKED_BOARD_LINEAGE'),None
    if any(abs(a-b)>.011 for a,b in zip(actual,rendered)) or abs(root['pot']/100-route['root']['pot'])>.011 or abs(root['stack']/100-route['root']['stack'])>.011:
        return dict(info,status='BLOCKED_EXACT_CHIP_PRICE'),None
    par=find(root,'b75 r c/',b)
    if par is None:return dict(info,status='BLOCKED_MISSING_ORIGINAL_BOUNDARY'),None
    if par['pot']!=sub['pot'] or root['stack']-max(par['bets'])!=sub['stack']:
        return dict(info,status='BLOCKED_PARENT_CHIP_PRICE'),None
    if any(jr['sub'].get(k)!=[[h,w] for h,w in zip(root['hands'][s],par['wr'][s],strict=True) if w>1e-4] for s,k in enumerate(('oop_w','ip_w'))):
        return dict(info,status='BLOCKED_PARENT_RANGE_LINEAGE'),None
    seq=[(root,'',f,0,'b75'),(root,'b75',f,1,'r'),(root,'b75 r',f,0,'c'),(sub,'b75 r c/',b,0,'x')]
    seats=[live(sub,n,s) for s in (0,1)]
    for g,line,board,s,a in seq:
        p=find(g,line,board)
        if p is None or p['player']!=s or a not in p['acts']:return dict(info,status='BLOCKED_MISSING_EXACT_ANCESTOR'),None
        seats[s]&=accepted(p,g['hands'],a)
    if version=='exp_ip':
        if not m.get('locks'):return dict(info,status='BLOCKED_MISSING_LOCK_PROVENANCE'),None
        scope=lock_scope(sub,m['locks'],version)
        info['lock_scope']=scope
        if scope.get('observed_marginal_source_nodes',0)<=0:return dict(info,status='BLOCKED_NO_OBSERVED_MARGINAL_LOCK'),None
    shown=set();half=set()
    for h in seats[1]:
        fc=hand_cell(''.join(h),f)[0];tc=hand_cell(''.join(h),b)[0]
        if fc not in route['flop'] or not route['flop'][fc].startswith('加注') or tc not in route['turn']:continue
        a=ACT.get(route['turn'][tc])
        if a in n['acts'] and h in accepted(n,sub['hands'],a):shown.add(h)
        if 'b50' in n['acts'] and h in accepted(n,sub['hands'],'b50'):half.add(h)
    info.update(status='EXACT_SOURCE_SCREEN',strict_seat_counts=list(map(len,seats)),displayed_hero_count=len(shown),displayed_pairs=pair_count(shown,seats[0]),halfpot_hero_count=len(half))
    return info,(seats[0],seats[1],shown,half)
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    raw=subprocess.check_output(['node','tools/hu_b873_rank152_routes.cjs'])
    route=json.loads(raw)
    p=json.loads(Path('data/nl2_hu_b871_current_234_source_gap_rescreen.json').read_bytes())
    q=next(x for x in p['models'] if x['rank']==152)
    assert q['model_id']==MODEL and q['is_above_research_threshold'] and p['NL2_weighted_opportunity_coverage_pct']<90
    assert {x['flop']:x['sha256'] for x in q['preliminary_3to5_named_proofs']}==GTO
    rows=[]
    for flop,pins in PINS.items():
        try:
            g,e=[download(flop,v,pin,out) for v,pin in zip(('gto','exp_ip'),pins,strict=True)]
            for t,gc in g.items():
                gi,gs=evaluate(gc,route,'gto')
                ei,es=evaluate(e[t],route,'exp_ip') if t in e else (dict(status='BLOCKED_NO_SAME_TURN_LOCK'),None)
                row=dict(flop=flop,turn=t,gto=gi,nl2=ei,status='BLOCKED_NO_DUAL_EXACT_SOURCE',joint_displayed_pairs=0)
                if gs is not None and es is not None and gi['board']==ei['board']:
                    v=gs[0]&es[0];h=gs[2]&es[2];half=gs[3]&es[3]
                    row.update(status='DUAL_EXACT_SOURCE_SCREEN',joint_displayed_pairs=pair_count(h,v),witness=witness(h,v),joint_halfpot_reach_pairs=pair_count(half,v))
                rows.append(row)
            if not g:rows.append(dict(flop=flop,status='BLOCKED_GTO_SOURCE_NOT_FOUND'))
        except (AssertionError,KeyError,ValueError,StopIteration,TypeError,subprocess.CalledProcessError) as err:
            rows.append(dict(flop=flop,status='BLOCKED_SOURCE_AUTHENTICATION_OR_SCHEMA',detail=repr(err)))
    report=dict(schema='NL2_B873_R152_ORIGINAL_DUAL_POLICY_SCREEN',rank=152,route_sha256=sha(raw),rows=rows,
      native_solves=0,CERT_promotions=0,positive_distinct_flops=len({x['flop'] for x in rows if x.get('joint_displayed_pairs',0)>0}),
      scope='Read-only exact-price source screen. Joint halfpot reach alone is NOT nonpolarization evidence. A blocked or missing source is not a zero-reach negative. No registry change.')
    (out/'report.json').write_bytes(json_bytes(report));(out/'rendered-route.json').write_bytes(raw)
    print(json.dumps(dict(rank=152,statuses=dict(Counter(x['status'] for x in rows)),positive_distinct_flops=report['positive_distinct_flops'],native_solves=0,CERT_promotions=0)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
