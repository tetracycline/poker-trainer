"""Inventory every GTO/lock decision in d347cb2 and replay independently authenticated residual originals."""
import argparse
import base64
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from hu_b483_locked_medium import PIN,RUST,POOL,PIPELINE,RANGES,proof
from hu_board_reach_corrections import summarize
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

BASE='d347cb2a19d48ef48d288071631dae419843a883'
DATA=Path('data')
REG='data/nl2_hu_multiboard_status_current.json'
PINS=DATA/'nl2_hu_b490_original_artifacts.json'
OUT=DATA/'nl2_hu_b490_locked_medium.json'
INVENTORY=DATA/'nl2_hu_b490_source_inventory.json'

def encode(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_bytes())
def disk(path,obj):path.write_bytes(encode(obj)+b'\n')

def planned():
    raw=subprocess.check_output(['git','show',BASE+':'+REG])
    reg=json.loads(raw)
    index={}
    for mid,m in reg['records'].items():
        if m['label']!='CERT-MULTIBOARD':continue
        for b in m['certified_3_to_5_exact_flop_boards']:
            head=[mid,b['public_board'],b['actual_exact_action_line'],b['acting_seat']]
            for run,sh,v in [(b['source_run_id'],b['source_sha256'],'gto')]+[(l['run_id'],l['sha256'],l['version']) for l in b['nl2_locked_variants']]:
                key=encode(head+[run,sh]).decode()
                assert key not in index
                index[key]=(m,b,run,sh,v)
    assert reg['CERT_MULTIBOARD']==97 and sum(v[-1]=='gto' for v in index.values())==346 and len(index)==744
    return reg,index,sha(raw)


def prior(index):
    rows={};origins={}
    for batch in (483,485):
        report=read(DATA/f'nl2_hu_b{batch}_locked_medium.json')
        source=dict(report.get('gto_references',{}))
        for key,row in report['references'].items():
            source[key]=row
            g=row.get('gto')
            if g:source[encode(json.loads(key)[:4]+[g['source_run_id'],g['source_sha256']]).decode()]=g
        for key,row in source.items():
            if key in index:
                if key in rows:assert summarize(rows[key])==summarize(row)
                rows[key]=row;origins[key]=f'B{batch}'
    return rows,origins


class Replay:
    def __init__(self,index,old):
        self.requests=defaultdict(list)
        for key,(m,b,run,sh,ver) in index.items():
            if key not in old:self.requests[run,sh,ver].append((key,m,b))
        self.rows={};self.roots={};self.root_requests=set();self.parent_roots={};self.parent_requested=set();self.skipped=Counter();self.used=set()

    def evaluate(self,run,ver,root,sub,source_sha,root_sha,manifest,job,digest,origin,meta=None):
        wanted=self.requests.get((run,source_sha,ver))
        if not wanted:return
        spot=manifest['spot']; family=manifest['pot_family']; patterns=manifest['locks']
        assert sha(encode(root))==root_sha and (sub['flop'],sub['turn'],sub['line0'])==(root['flop'],job['turn'],' '.join(job['line0'][:-1]))
        assert (job['pot'],job['stack'],job.get('hero'))==(sub['pot'],sub['stack'],None if ver=='gto' else int(ver=='exp_ip'))
        assert [q['pat'] for q in job.get('locks',[])]==[q['pat'] for q in patterns]
        parent,=(n for n in root['nodes'] if n['line']==sub['line0']+'/' and n['board'][-2:]==sub['turn'] and len(n['board'])==8)
        assert (parent['pot'],root['stack']-max(parent['bets']))==(sub['pot'],sub['stack'])
        for seat,side in enumerate(('oop_w','ip_w')):
            expected=[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
            assert job[side]==expected
        parent_gto=ver!='gto' and root['info'].get('hero_gap_pct') is None
        if parent_gto:
            assert manifest.get('gto_parent_source_sha256')==root_sha and manifest.get('gto_parent_source_run_id')
        if (sub['info']['gto_expl_pct']>.5 or root['info']['gto_expl_pct']>.5 or
            (ver!='gto' and (sub['info'].get('hero_gap_pct',1)>.5 or (not parent_gto and root['info'].get('hero_gap_pct',1)>.5)))):
            self.skipped['convergence']+=1;return
        scope=lock_scope(sub,patterns,ver)
        scope.pop('matching_examples',None);scope.pop('caveat',None)
        if ver!='gto' and not scope['observed_marginal_source_nodes']:
            self.skipped['no_observed_lock']+=1;return
        masks=game_reach(root,sub)[0]
        nodes={(n['board'],n['line'],n['player']):n for n in sub['nodes']}
        for key,m,b in wanted:
            assert (spot,family,sub['flop'],sub['turn'],sub['line0'])==(m['solver_profile'],m['family'],b['flop'],b['turn'],b['exact_flop_action'])
            n=nodes[b['public_board'],b['actual_exact_action_line'],b['acting_seat']]
            assert (n['pot']/100,(sub['stack']-max(n['bets']))/100)==(b['actual_pot_bb'],b['actual_effective_stack_bb'])
            if ver=='gto':assert n['acts']==b['exact_node_actions']
            else:assert int(ver=='exp_ip')==n['player']
            row=dict(source_sha256=source_sha,source_run_id=run,archive_sha256=digest,source_archive=origin,
                     original_root_sha256=root_sha,spot=spot,family=family,version=ver,flop=sub['flop'],turn=sub['turn'],
                     gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
                     lock_scope=scope,**proof(root,sub,n,masks))
            if meta:row['archive_id']=meta['id']
            summarize(row)
            if key in self.rows:assert summarize(self.rows[key])==summarize(row)
            else:self.rows[key]=row;self.used.add(origin)

    def zip(self,path,meta):
        blob=path.read_bytes();assert sha(blob)==meta['sha256']
        with zipfile.ZipFile(path) as z:
            names=z.namelist(); files=[s for s in names if s.startswith('evidence/') and s.endswith('.json')]
            if len(files)!=1:return
            m=json.loads(z.read(files[0]))
            if m.get('schema')!='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1':return
            if m.get('pool_source_sha256')!=POOL or m.get('solver_pin')!=PIPELINE or m.get('solver_ranges_sha256')!=RANGES:return
            pins={z.read(n).decode().strip() for n in names if n.startswith('evidence/') and n.endswith('.txt') and z.getinfo(n).file_size<300}
            if not {PIN,RUST}<=pins:return
            root_path='solver/postflop/'+m['file_flop'];ss=m['file_flop_sha256']
            if root_path not in names:return
            rr=z.read(root_path);assert sha(rr)==ss;root=json.loads(rr);ver=m['version'];run=meta['run']
            if (run,ss) in self.parent_requested and ver=='gto':self.parent_roots[run,ss]=(root,meta['name'])
            for c in m['cases']:
                sub_sha=c['source_sha256']
                if (run,sub_sha,ver) not in self.requests and (ss,sub_sha) not in self.root_requests:continue
                sp='solver/postflop/'+c['source_path'];jp=sp[:-5]+'.job.json'
                if sp not in names or jp not in names:continue
                sr=z.read(sp);assert sha(sr)==sub_sha;sub=json.loads(sr);job=json.loads(z.read(jp))
                self.evaluate(run,ver,root,sub,sub_sha,ss,m,job,meta['sha256'],meta['name'],meta)
                if (ss,sub_sha) in self.root_requests:self.roots[ss,sub_sha]=(root,sub,m,job,meta['name'])

    def local(self,reg):
        root=DATA/'solver_evidence'
        expected={}
        for group in reg['exact_source_extensions'].values():
            for p in group:
                for field in ('archive_sha256','locked_original_archive_sha256'):
                    if field in p:expected[p[field]]=p.get('source_run_id')
        for name in ('B463_rank45_three_true_original_GTO_NL2_OOP_flops','B453_rank32_three_true_original_GTO_NL2_OOP_flops'):
            for p in reg[name]['pins']:
                if 'archive_sha256' in p:expected[p['archive_sha256']]=p['source_run_id']
        for p in sorted(root.glob('NL2_B*.json.gz')):
            bb=p.read_bytes();digest=sha(bb)
            if digest not in expected:continue
            pack=json.loads(gzip.decompress(bb))
            for s in pack.get('source_arrays',[]):
                if not s.get('subgame') or not s.get('root'):continue
                assert (pack.get('pinned_solver',pack.get('solver')),pack.get('pinned_rust',pack.get('rust')))==(PIN,RUST)
                if sha(encode(s['subgame']))!=s['source_sha256']:continue
                self.evaluate(pack['run_id'],s['version'],s['root'],s['subgame'],s['source_sha256'],s['root_sha256'],
                              s['manifest'],s['subgame_job'],digest,p.name)

    def verified_btn(self):
        directory=DATA/'solver_evidence'/'b466'
        for p in directory.glob('*.proof.json'):
            evidence=read(p)
            archive=directory/evidence['archive']
            if not archive.exists():archive=directory.parent/evidence['archive']
            bb=archive.read_bytes();digest=sha(bb);assert digest==evidence['archive_sha256']
            pack=json.loads(gzip.decompress(bb))
            assert (pack['solver_pin'],pack['rust_pin'])==(PIN,RUST)
            run=int(p.name.split('_')[-1].split('.')[0])
            for ver in ('gto','exp_oop'):
                s=pack[ver]
                assert sha(encode(s['turn_subgame']))==s['subgame_sha256'] and sha(encode(s['flop_root']))==s['root_sha256']
                self.evaluate(run,ver,s['flop_root'],s['turn_subgame'],s['subgame_sha256'],s['root_sha256'],
                              s['manifest'],s['turn_job'],digest,str(archive.relative_to(DATA)))

    def corrected_street(self,assemble):
        for desc in sorted((DATA/'solver_evidence/lock_variants').glob('rank1_b*.json')):
            row=read(desc);p=DATA/'solver_evidence'/row['original_package'];blob=p.read_bytes()
            assert sha(blob)==row['original_package_sha256']
            pack=json.loads(gzip.decompress(blob));raw=base64.b64decode(pack['source_file_b64'],validate=True)
            assert sha(raw)==pack['source_sha256']==row['lock']['sha256']
            if 'history' in pack:
                h=pack['history'];root_sha,old_sha=h['root_sha256'],h['lock_sha256']
                assert h['pool_sha256']==POOL
            else:
                assert pack['pool_sha256']==POOL
                h=pack['original_exp'];root_sha,old_sha=h['root_sha256'],h['source_sha256']
            key=(root_sha,old_sha)
            self.root_requests.add(key)
            if not assemble or key not in self.roots:continue
            root,old,m,oldjob,original_zip=self.roots[key]
            new=dict(json.loads(raw),line0=old['line0'],turn=old['turn'],rivers=old['rivers'])
            job=pack['job'];patterns=[]
            for old_rule,rule,meta in zip(oldjob['locks'],job['locks'],m['locks'],strict=True):
                assert old_rule['pat']==meta['pat'] and {k:v for k,v in rule.items() if k!='pat'}=={k:v for k,v in old_rule.items() if k!='pat'}
                patterns.append(dict(meta,pat=rule['pat']))
            assert job['oop_w']==oldjob['oop_w'] and job['ip_w']==oldjob['ip_w']
            self.evaluate(pack['run'],'exp_oop',root,new,pack['source_sha256'],root_sha,dict(m,locks=patterns),
                          job,sha(blob),p.name)
            self.used.add(original_zip)

    def partial(self,path,meta,assemble):
        with zipfile.ZipFile(path) as z:
            names=z.namelist();files=[n for n in names if n.startswith('evidence/') and n.endswith('.json')]
            if len(files)!=1:return
            m=json.loads(z.read(files[0]))
            standard=m.get('schema')=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
            if standard:
                if 'gto_parent_source_run_id' not in m or 'solver/postflop/'+m['file_flop'] in names:return
                assert m['file_flop_sha256']==m['gto_parent_source_sha256'] and m['pool_source_sha256']==POOL
                m=dict(m,original_GTO_source_run_id=m['gto_parent_source_run_id'],original_GTO_flop_root_sha256=m['gto_parent_source_sha256'])
            elif not m.get('partially_locked_turn_river_only') or not m.get('original_GTO_flop_unchanged'):return
            ver=m['version'];run=meta['run'];parent=m['original_GTO_source_run_id'],m['original_GTO_flop_root_sha256']
            if not any((run,c['source_sha256'],ver) in self.requests for c in m['cases']):return
            self.parent_requested.add(parent)
            if not assemble:return
            pins={z.read(n).decode().strip() for n in names if n.startswith('evidence/') and n.endswith('.txt') and z.getinfo(n).file_size<300}
            if not {PIN,RUST}<=pins:return
            assert sha(path.read_bytes())==meta['sha256']
            original=self.parent_roots.get(parent)
            if original is None:
                for n in names:
                    if n.startswith('solver/postflop/out/') and n.endswith('.json') and not n.endswith('.job.json'):
                        data=z.read(n)
                        if sha(data)==parent[1]:
                            original=(json.loads(data),meta['name']);break
            if original is None:return
            root,origin=original
            for c in m['cases']:
                sh=c['source_sha256']
                if (run,sh,ver) not in self.requests:continue
                sp='solver/postflop/'+(c['source_path'] if standard else c['original_Rust_exp_subgame_path']);jp=sp[:-5]+'.job.json'
                if sp not in names or jp not in names:continue
                data=z.read(sp);jb=z.read(jp);assert sha(data)==sh
                if not standard:assert sha(jb)==c['original_exp_job_sha256']
                normalized=dict(spot=m['spot'],pot_family=self.requests[run,sh,ver][0][1]['family'],
                                locks=m['locks'],gto_parent_source_sha256=parent[1],gto_parent_source_run_id=parent[0])
                before=len(self.rows)
                self.evaluate(run,ver,root,json.loads(data),sh,parent[1],normalized,json.loads(jb),meta['sha256'],meta['name'],meta)
                if len(self.rows)>before:self.used.add(origin)

def unavailable_b144(row,artifacts,folder):
    model,board,run,src,ver=row
    assert run==44852646580 and model['frequency_rank'] in (47,150) and ver=='exp_ip'
    meta,=(m for m in artifacts if m['run']==run and board['flop'].lower() in m['name'].lower())
    path=folder/f'{meta["id"]}.zip'
    assert sha(path.read_bytes())==meta['sha256']
    with zipfile.ZipFile(path) as z:
        mf,=(f for f in z.namelist() if f.startswith('evidence/') and f.endswith('.json'))
        manifest=json.loads(z.read(mf));case,=(c for c in manifest['cases'] if c['source_sha256']==src)
        assert (manifest['version'],manifest['spot'],manifest['flop'],case['turn'],case['line'])==(
            ver,model['solver_profile'],board['flop'],board['turn'],board['exact_flop_action'])
        assert not any(n.endswith('/'+case['source_path']) for n in z.namelist())
        code,=(n for n in z.namelist() if n.startswith('trainer/data/solver_evidence/') and n.endswith('.json.gz'))
        compacted=json.loads(gzip.decompress(z.read(code)))
        original,=(c for a in compacted['artifacts'] for c in a['cases'] if c['source_sha256']==src and c['version']==ver)
        assert all('w' not in n and 'strat' not in n for n in original['nodes'])
    return dict(status='ORIGINAL_SUBGAME_MISSING',version=ver,source_run_id=run,source_sha256=src,archive_id=meta['id'],
                archive_sha256=meta['sha256'],spot=model['solver_profile'],family=model['family'],flop=board['flop'],turn=board['turn'],
                public_board=board['public_board'],line=board['actual_exact_action_line'],acting_seat=board['acting_seat'],
                reason='ORIGINAL_RUST_SUBGAME_NOT_PUBLISHED',detail='Published B144 artifact contains the source manifest and single-actor hand masks; the original Rust turn subgame needed to replay both players is absent.')


def inventory_row(row,batch):
    fields=('version','source_run_id','source_sha256','archive_sha256','status','strict_legal_combos','compatible_hole_card_pairs')
    result={k:row[k] for k in fields};result['evidence']=batch
    b=row['b50']
    result['b50']=None if b is None else {k:b[k] for k in ('eligible','preferred','candidate','status')}
    if row['version']!='gto':
        scope=row['lock_scope']
        result['lock_scope']={k:scope[k] for k in ('observed_marginal_source_nodes','imputed_assumption_nodes','unmatched_nodes')}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',required=True,type=Path)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    reg,index,regsha=planned();old,origins=prior(index)
    replay=Replay(index,old);replay.local(reg);replay.verified_btn();replay.corrected_street(False)
    artifacts=read(PINS)
    def path(meta):return args.downloads/f'{meta["id"]}.zip'
    for meta in artifacts:replay.partial(path(meta),meta,False)
    for meta in artifacts:replay.zip(path(meta),meta)
    for meta in artifacts:replay.partial(path(meta),meta,True)
    replay.corrected_street(True)
    locks={};gtos={};unresolved={};covered={}
    counts=Counter()
    for k,(m,b,run,src,ver) in index.items():
        original_key=encode(json.loads(k)[:4]+[b['source_run_id'],b['source_sha256']]).decode()
        if k in old:row=old[k];evidence=origins[k]
        elif k in replay.rows:
            row=replay.rows[k];evidence='B490'
            if ver=='gto':gtos[k]=row
            else:locks[k]=dict(row,gto=replay.rows.get(original_key))
        else:
            unresolved[k]=unavailable_b144(index[k],artifacts,args.downloads)
            row=None;evidence='ORIGINAL_SUBGAME_MISSING'
        counts[evidence]+=1
        group=covered.setdefault(m['model_id'],dict(frequency_rank=m['frequency_rank'],spot=m['solver_profile'],family=m['family'],boards={}))
        bs=group['boards'].setdefault(b['public_board'],dict(flop=b['flop'],turn=b['turn'],line=b['actual_exact_action_line'],acting_seat=b['acting_seat'],sources=[]))
        bs['sources'].append(inventory_row(row,evidence) if row else dict(unresolved[k],evidence=evidence))
    assert set(old).isdisjoint(replay.rows) and len(old)+len(replay.rows)+len(unresolved)==len(index)
    assert all((k in locks or k in gtos or k in unresolved) for k in set(index)-set(old)) and len(covered)==97
    zero=Counter(row['version'] for row in replay.rows.values() if row['status']=='ZERO_JOINT_REACH')
    totals=dict(frozen_cert_models=97,named_boards=346,gto_decisions=346,lock_variant_decisions=398,
                all_source_decisions=len(index),previously_replayed=len(old),new_original_replays=len(replay.rows),
                new_gto_decisions=len(gtos),new_lock_variant_decisions=len(locks),new_zero_reach=dict(sorted(zero.items())),
                explicitly_unresolved=len(unresolved),sources_by_evidence=dict(sorted(counts.items())))
    report=dict(schema='NL2_HU_B490_ORIGINAL_LOCKED_MEDIUM_V1',frozen_commit=BASE,registry_sha256=regsha,
                poker_solver_pin=PIN,rust_engine_pin=RUST,pool_sha256=POOL,original_artifacts_sha256=sha(PINS.read_bytes()),
                totals=totals,references=locks,gto_references=gtos,unresolved=unresolved)
    inventory=dict(schema='NL2_HU_B490_CERT_SOURCE_INVENTORY_V1',frozen_commit=BASE,registry_sha256=regsha,
                   totals=totals,models=covered)
    for dest,obj in ((OUT,report),(INVENTORY,inventory)):
        payload=encode(obj)+b'\n'
        if args.verify:
            assert dest.read_bytes()==payload,f'{dest} differs from original replay'
        else:dest.write_bytes(payload)
    print(json.dumps(totals,sort_keys=True))


if __name__=='__main__':main()
