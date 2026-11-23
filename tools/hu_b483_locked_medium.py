"""Replay exact GTO and locked decision masks from the first three original multiboard batches."""
import argparse
import base64
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from hu_b472_street_lock import PIN, POOL, RUST
from hu_multiboard_promote import FAM_ROOT
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, source_nodes

FROZEN=Path('data/nl2_hu_multiboard_status_v53_b465_rank218.json')
OUT=Path('data/nl2_hu_b483_locked_medium.json')
RUNS={
    44666285424:(1,'92c10f1d3ed037e04ca9b99feb702f2174ebd9af'),
    44666290556:(2,'91aaaf4661b62c114285a57f390fc6750e996471'),
    44666294821:(3,'e8f6e7dbce77676bf375a66b86db41742d896cd2'),
}
PIPELINE='f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253'
RANGES='f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba'
# ID and SHA-256 of each original GitHub Actions ZIP, keyed by its published artifact name.
ARCHIVES={
    'nl2-multiboard-B1-BTN_BB-exp_ip-8s8h3d': (14601267074,'59d9886566c8e55ca71335ee70f565529010552f1258ccfa0ef652e076db21d1'),
    'nl2-multiboard-B1-BTN_BB-exp_ip-As9h2d': (14599634225,'bb7e1b8e9a6f4e170916a612df5504a759a93f61ff88c2d68962f96de08d5c96'),
    'nl2-multiboard-B1-BTN_BB-exp_ip-KsQh4d': (14601061377,'af1d282f697824893e6becfc61679ba6123b1464e4d119ead029af5df66dba1e'),
    'nl2-multiboard-B1-BTN_BB-exp_oop-8s8h3d': (14601975812,'5287a8210790f40a9d45f3ae8f46a789b87762c2df93901f5206a5bc8440f652'),
    'nl2-multiboard-B1-BTN_BB-exp_oop-As9h2d': (14600766400,'018063baa0e11cd81748d9e0e2e5fd2dcf897feec61937f215a85fbb6371be6a'),
    'nl2-multiboard-B1-BTN_BB-exp_oop-KsQh4d': (14600579823,'767ff7aa8eb02a8f5196e234afbfc07dd0fad74b716b99518a072fce3239c0b9'),
    'nl2-multiboard-B1-BTN_BB-gto-8s8h3d': (14600293988,'a65a24cb50a3015dde4863cc16bc05f9358bab7dedb50cbc3004b2f1e324fd21'),
    'nl2-multiboard-B1-BTN_BB-gto-As9h2d': (14599607198,'8f19dbd115e4b6260aecf3b22fb9d43fc27d9a8327885735d050f2e37b0983b3'),
    'nl2-multiboard-B1-BTN_BB-gto-KsQh4d': (14600212926,'e22ef0510366501905aee957468b60bd3c5b586adcf3fe2406db3b08beeba7e1'),
    'nl2-multiboard-B1-SB_BB-exp_ip-8s8h3d': (14599910729,'b69ac48b82f7bdd21573373ca076038bb5460664ff1e82382bf55ebfc7a28d28'),
    'nl2-multiboard-B1-SB_BB-exp_ip-As9h2d': (14598327356,'bf25c09b395e9681f8cb67a081bf39fc0d5a3c3b4baa0a57dff2cfa991992a31'),
    'nl2-multiboard-B1-SB_BB-exp_ip-Js9h4d': (14598803503,'a470b65019dfc72a1490f5ef7ea73e9be21efc60f0352cc2cc569b425c64c407'),
    'nl2-multiboard-B1-SB_BB-exp_oop-8s8h3d': (14600596382,'5e51ed3c3ac1ad0ab1e1a5fb6aa3fe4b70ce5f66351a45567895ac7876ec497b'),
    'nl2-multiboard-B1-SB_BB-exp_oop-As9h2d': (14598079511,'268dc9d99252351bce051f8fb610a74bc167d4e36607aa2a6832bb2e9855d1c2'),
    'nl2-multiboard-B1-SB_BB-exp_oop-Js9h4d': (14599601220,'b542c062f5f720b54428616b5c17966befaaba36b7eb810105a4b1e5739b10c9'),
    'nl2-multiboard-B1-SB_BB-gto-8s8h3d': (14598504895,'17f1f9d0c1e6e5bb1301873e4eb76e44e619dd23b5fe4d32d911fdd258020722'),
    'nl2-multiboard-B1-SB_BB-gto-As9h2d': (14598935222,'b1a8e88fd871a2e0e9f8f43f068ed5187df9fc51511a09de93bd663bac2fca8d'),
    'nl2-multiboard-B1-SB_BB-gto-Js9h4d': (14599361276,'50f129112a18235d20dbc3938a7a2160c560b143216fb7e92270fa1d404fb6d7'),
    'nl2-multiboard-B2-CO_BB-exp_ip-8s8h3d': (14599113361,'d87347e5e0ee51de6740d13e33d13e5f7b14ff5d4c38a0550b2834d3428121cf'),
    'nl2-multiboard-B2-CO_BB-exp_ip-As9h2d': (14598482452,'96cef97def031971f0f4173fa1a35958ca80e5d2475f9128e5d63db0d05701c9'),
    'nl2-multiboard-B2-CO_BB-exp_ip-Js9h4d': (14598807546,'70edcf8cf6b0b1e7a5a2eb30a1fed6959bcd0462bf4199ac880f54b1e4b7a31a'),
    'nl2-multiboard-B2-CO_BB-exp_oop-8s8h3d': (14598534163,'85dd1ddf7ef016db4025c67faf5bdf094701bfd93ab04b6aa00f077960d84888'),
    'nl2-multiboard-B2-CO_BB-exp_oop-As9h2d': (14598057037,'3f752103bdd16757f2a8de94793fbcd79bbbe62203cd77a185a33d27e492ca84'),
    'nl2-multiboard-B2-CO_BB-exp_oop-Js9h4d': (14597984483,'908762465dfa24c8958c0dc7b02e9ab6fb15dc39b8a0eb18d8a3a9fe42e7da0f'),
    'nl2-multiboard-B2-CO_BB-gto-As9h2d': (14597269910,'0ca0cbf3cc9c51b9859e28e99fc4b383ab40508913a2fccfe19b98f6ac1b8443'),
    'nl2-multiboard-B2-CO_BB-gto-Js9h4d': (14597934573,'247c05663e8edd668a317d3104c33b0ab780ce26722923bc76dc3cff4fea04ec'),
    'nl2-multiboard-B2-SB3_BTN-exp_ip-8s8h3d': (14598914534,'a9772b74fc915ad5bf98015dc3beb6b2f68675163e54de4e2d0439cbe2defd38'),
    'nl2-multiboard-B2-SB3_BTN-exp_ip-9s6h3d': (14598528771,'3aa961828405c29f0ec9239c550c6b1de8fdc97cbb90e8e65dfc1284d3c6dd2f'),
    'nl2-multiboard-B2-SB3_BTN-exp_ip-KsQh4d': (14599049013,'7f87cd566b67841eff885809d9c82979c43ae2c8907d7cd2dde093424836ac75'),
    'nl2-multiboard-B2-SB3_BTN-exp_oop-KsQh4d': (14599228790,'7a71071e69f43cfce3e94a1af04c60ab973c6d6b7d955fba97235c96d98e903e'),
    'nl2-multiboard-B2-SB3_BTN-gto-9s6h3d': (14598643264,'48195d8ae9a564a375c96666ea257dda693259c59f2620322912ef2227b1c6e8'),
    'nl2-multiboard-B2-SB3_BTN-gto-KsQh4d': (14599605695,'0b6b5ddff20e0394c250171188d6f08cdb0e3d9194e5bb60ab4986cd9b41ffc9'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_ip-8s8h3d': (14599769541,'c891339f9dfeb072f96562827956f59c6659623252f813ef2ebae4e190806cef'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_ip-9s6h3d': (14599454837,'a9097cf51633aede964f0a9a83c591dc63a8a3e794aa0d430aa677dfee27cbce'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_ip-KsQh4d': (14602013161,'d47283bedc85746aea26f7c30028ffc4e6c20578919ccbb913174e05c605242c'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_oop-8s8h3d': (14600533671,'fb8b1eec4dff7a43cba522d1e1ddf61ad39cba2e293f69b5f5a3ae0db0eda8b9'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_oop-9s6h3d': (14598668846,'16c8ce88112b3c9b03b7dfcab247ec84a980eaca4113d5110f86b0f9b0bbaa54'),
    'nl2-multiboard-B3-LMP_CO_BB-exp_oop-KsQh4d': (14602740855,'e50c3ada48ed27d4092a6e1333d411abf924e230541a68c8bd7a20d153b952b8'),
    'nl2-multiboard-B3-LMP_CO_BB-gto-8s8h3d': (14600026283,'7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e'),
    'nl2-multiboard-B3-LMP_CO_BB-gto-9s6h3d': (14599037935,'f6d4d734bcb9d35f9c779e5b0d9853b23217bb1b44ef17b73ef35f4ef2fb0c11'),
    'nl2-multiboard-B3-LMP_CO_BB-gto-KsQh4d': (14601426559,'144919b63c7609d4256109db43d81f60004bad04a1bb7398759d238edc70f454'),
}


def encode(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path,expected=None):
    data=path.read_bytes()
    if expected is not None:
        assert digest(data)==expected,path
    return json.loads(data)


def collect_references(registry):
    """Use immutable V53 only for selecting and pinning references. Cumulative audit uses live state."""
    refs={}
    groups=defaultdict(lambda:defaultdict(list))
    def group(run,spot,flop,version,sha,key):
        num,_=RUNS[run]
        name=f'nl2-multiboard-B{num}-{spot}-{version}-{flop}'
        groups[name][sha].append((key,version))
    for mid,model in registry['records'].items():
        if model['label']!='CERT-MULTIBOARD':
            continue
        for b in model['certified_3_to_5_exact_flop_boards']:
            spot=model['solver_profile']
            for lock in b['nl2_locked_variants']:
                run,sha=lock['run_id'],lock['sha256']
                if run not in RUNS:
                    continue
                seat=b['acting_seat']
                assert lock['version']==('exp_ip' if seat else 'exp_oop')
                key=encode([mid,b['public_board'],b['actual_exact_action_line'],seat,run,sha]).decode()
                assert key not in refs
                refs[key]=(model,b,lock)
                group(run,spot,b['flop'],lock['version'],sha,key)
                if b['source_run_id'] in RUNS:
                    group(b['source_run_id'],spot,b['flop'],'gto',b['source_sha256'],key)
    assert set(groups)==set(ARCHIVES)
    return refs,groups


def jobs_checked(game,path,version,rules):
    job=read(path.with_suffix('.job.json'))
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(game['pot'],game['stack'],.05,1000)
    assert (job.get('hero'),bool(job.get('locks')))==({'gto':None,'exp_ip':1,'exp_oop':0}[version],version!='gto')
    assert [r['pat'] for r in job.get('locks',[])]==[r['pat'] for r in rules]
    assert 0<=game['info']['gto_expl_pct']<=.5
    if version!='gto':
        assert 0<=game['info']['hero_gap_pct']<=.5
    return job


def proof(root,sub,n,masks):
    board,line,actor=n['board'],n['line'],n['player']
    key=f'{board}|{line}|{actor}'
    exact=compatible_node_reach(root,sub,n,masks[key])
    action_mask=base64.b64decode(exact['mask'],validate=True)
    hands=sub['hands'][actor]
    legal=exact['count']
    assert len(hands)==len(action_mask) and sum(map(bool,action_mask))==legal
    assert all(bits<(1<<len(n['acts'])) for bits in action_mask)
    assert bool(exact['compatible_hole_card_pairs'])==bool(legal)
    nodes=source_nodes(dict(sub,nodes=[n]),{'nodes':{key:exact}})
    assert len(nodes)==int(legal>0)
    medium=None
    if legal:
        measured=nodes[0]
        medium=measured['medium_50pct_strict_evidence']
        assert measured['strictly_reachable_combos']==legal and measured['strictly_reachable_masks_b64']==exact['mask']
        b50=1<<n['acts'].index('b50') if 'b50' in n['acts'] else 0
        assert medium['eligible']==sum(bool(bits&b50) for bits in action_mask)
        assert medium['candidate'] is measured['b50_nonpolarized_relative_equity_research_candidate']
    return dict(status='POSITIVE_JOINT_REACH' if legal else 'ZERO_JOINT_REACH',
                public_board=board,line=line,acting_seat=actor,source_actions=n['acts'],
                source_hand_order_sha256=digest(encode(hands)),source_hand_count=len(hands),
                compatible_action_mask_b64=exact['mask'],strict_legal_combos=legal,
                compatible_opponent_combos=exact['compatible_opponent_combos'],
                compatible_hole_card_pairs=exact['compatible_hole_card_pairs'],b50=medium)


def replay_archive(directory,run,name,expected,api_info,refs):
    num,trainer_sha=RUNS[run]
    artifact_id,zip_sha=ARCHIVES[name]
    meta=api_info[artifact_id]
    info=meta['workflow_run']
    assert (meta['name'],meta['digest'],info['id'],info['head_sha'])==(name,'sha256:'+zip_sha,run,trainer_sha)
    assert info['head_branch']=='fix/nl2-hu-lines-audit-20261118' and info['repository_id']==1438346845
    folder=directory/str(artifact_id)
    assert digest(folder.with_suffix('.zip').read_bytes())==zip_sha
    evidence=folder/'evidence'
    assert (evidence/'poker-solver-pinned-SHA.txt').read_text().strip()==PIN
    assert (evidence/'rust-engine-pin-SHA.txt').read_text().strip()==RUST
    mf,=evidence.glob('*.json')
    m=read(mf)
    spot,version,flop=m['spot'],m['version'],m['flop']
    assert name==f'nl2-multiboard-B{num}-{spot}-{version}-{flop}'
    assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1' and not m['failures']
    assert (m['solver_pin'],m['solver_ranges_sha256'],m['pool_source_sha256'],m['n_NL2_hands'])==(PIPELINE,RANGES,POOL,2334487)
    assert m['flop_action_sizes']==['33%','50%','75%','100%']
    assert m['preflop_ranges']['source']==('ASSUMED_EXPLICIT_169CLASS' if m['pot_family']=='LMP' else 'PINNED_POKER_SOLVER_PREFLOP_CFR')
    base=folder/'solver/postflop'
    root_path=base/m['file_flop']
    root=read(root_path,m['file_flop_sha256'])
    assert (root['pot']/100,root['stack']/100)==(m['root_pot_bb'],m['root_remaining_bb'])==FAM_ROOT[spot]
    assert root['flop']==flop
    jobs_checked(root,root_path,version,m['locks'])
    cases={c['source_sha256']:c for c in m['cases']}
    assert len(cases)==m['solved_cases'] and set(expected)<=cases.keys()
    gathered=[]
    for sub_sha,entries in expected.items():
        c=cases[sub_sha]
        path=base/c['source_path']
        sub=read(path,sub_sha)
        job=jobs_checked(sub,path,version,m['locks'])
        assert job['line0']==[*c['line'].split(),'/'] and job['turn']==sub['turn']==c['turn']
        assert (sub['flop'],sub['line0'])==(flop,c['line'])
        assert c['gto_gap_pct']==sub['info']['gto_expl_pct'] and c['hero_gap_pct']==sub['info'].get('hero_gap_pct')
        masks=game_reach(root,sub)[0]
        index={(n['board'],n['line'],n['player']):n for n in sub['nodes']}
        assert len(index)==len(sub['nodes'])
        scope=lock_scope(sub,m['locks'],version)
        scope.pop('matching_examples',None)
        scope.pop('caveat',None)
        source=dict(source_sha256=sub_sha,source_run_id=run,archive_id=artifact_id,archive_sha256=zip_sha,
                    spot=spot,family=m['pot_family'],version=version,flop=flop,turn=c['turn'],
                    gto_gap_pct=c['gto_gap_pct'],locked_hero_gap_pct=c['hero_gap_pct'],lock_scope=scope)
        computed={}
        for ref,ver in entries:
            model,b,lock=refs[ref]
            assert ver==version
            assert (model['solver_profile'],model['family'],b['flop'],b['turn'],b['exact_flop_action'])==(spot,m['pot_family'],flop,c['turn'],c['line'])
            if ver=='gto':
                assert (b['source_run_id'],b['source_sha256'])==(run,sub_sha)
            else:
                assert (lock['run_id'],lock['sha256'],lock['version'])==(run,sub_sha,ver)
            k=b['public_board'],b['actual_exact_action_line'],b['acting_seat']
            n=index[k]
            assert (n['pot']/100,(sub['stack']-max(n['bets']))/100)==(b['actual_pot_bb'],b['actual_effective_stack_bb'])
            if ver=='gto':
                assert n['acts']==b['exact_node_actions']
            else:
                assert n['player']==int(ver=='exp_ip')
            if k not in computed:
                computed[k]=dict(source,**proof(root,sub,n,masks))
            gathered.append((ref,version,computed[k]))
    return gathered


def build(directory,run):
    refs,groups=collect_references(read(FROZEN))
    api={a['id']:a for a in read(directory/f'{run}.json')['artifacts']}
    partial={}
    for name,expected in sorted(groups.items()):
        if name.startswith(f'nl2-multiboard-B{RUNS[run][0]}-'):
            for ref,ver,row in replay_archive(directory,run,name,expected,api,refs):
                partial.setdefault(ref,{})['gto' if ver=='gto' else 'lock']=row
    return partial


def assemble(shards):
    rows={}
    for shard in shards:
        for key,parts in shard.items():
            by_version=rows.setdefault(key,{})
            assert not set(parts).intersection(by_version)
            by_version.update(parts)
    refs,_=collect_references(read(FROZEN))
    assert rows.keys()==refs.keys()
    complete={}
    for key,parts in sorted(rows.items()):
        model,b,lock=refs[key]
        assert set(parts)==({'lock','gto'} if b['source_run_id'] in RUNS else {'lock'})
        complete[key]=dict(parts['lock'],gto=parts.get('gto'))
    counts=Counter()
    for row in complete.values():
        counts['lock_positive' if row['strict_legal_combos'] else 'lock_zero']+=1
        counts['gto_outside_replay' if row['gto'] is None else ('gto_positive' if row['gto']['strict_legal_combos'] else 'gto_zero')]+=1
    return dict(schema='NL2_HU_B483_ORIGINAL_LOCKED_MEDIUM_V1', registry=FROZEN.name,registry_sha256=digest(FROZEN.read_bytes()),
                poker_solver_pin=PIN,rust_engine_pin=RUST,pool_sha256=POOL,trainer_commits={run:sha for run,(_,sha) in RUNS.items()},
                totals=dict(sorted(counts.items())),references=complete)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--downloads',type=Path)
    p.add_argument('--run',type=int,choices=RUNS)
    p.add_argument('--list-artifacts',action='store_true')
    p.add_argument('--assemble',type=Path,nargs='+')
    p.add_argument('--out',type=Path,default=OUT)
    args=p.parse_args()
    if args.list_artifacts:
        if not args.run: p.error('--list-artifacts needs --run')
        print(' '.join(str(item[0]) for name,item in ARCHIVES.items() if name.startswith(f'nl2-multiboard-B{RUNS[args.run][0]}-')))
        return
    if args.assemble:
        result=assemble([read(s) for s in args.assemble])
    elif args.run:
        result=build(args.downloads,args.run)
    else:
        result=assemble([build(args.downloads,r) for r in RUNS])
    args.out.write_bytes(encode(result)+b'\n')
    print(result.get('totals',{'keys_in_run':len(result)}))


if __name__=='__main__':
    main()
