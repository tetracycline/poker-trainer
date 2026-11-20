#!/usr/bin/env python3
"""Authentic 100bb NL2 HU multiboard CFR on exact public cards.

For SRP/3BP use pinned preflop action-conditioned CFR ranges. For ISO/LMP use
frozen explicit 169-class assumptions. Both flop donk and check-stab branches
are allowed. All derived CERTs apply only to exact boards/SPR and solver lines.

For exp_ip/exp_oop, locks use the real NL2 2.33m-hand pool aggregates where
available, otherwise the disclosed marginal-by-size or assumed defaults.
No imaginary villain hole-card observations. Every pattern/sample is tagged.
"""
import argparse, hashlib, importlib, json, os, pathlib, re, sys, time, traceback

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from solve_hu_assumed_pots import RULES,w_iso_oop,w_iso_ip,w_lmp_ip
from solve_hu_missing_branches import EXTRA_SPOTS
SPOTS=('BTN_BB','CO_BB','SB_BB','UTG_CO','BB3_BTN','SB3_BTN','CO3_BTN','ISO_BTN_CO','LMP_CO_BB')
FLOP_ACTIONS=('x x','x b33 c','x b50 c','x b75 c','x b100 c',
              'b33 c','b50 c','b75 c','b100 c',
              'x b33 r c','x b50 r c','x b75 r c',
              'b33 r c','b50 r c','b75 r c')
SIZES=('33%','50%','75%','100%')
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def make_fallbacks(spot,ver,p,orig,loc):
    if ver=='gto':return [],[]
    configs=[]
    is_assumed=spot in RULES
    if is_assumed:
        base=[];meta=[]
    else:
        base,meta=orig(spot,ver,loc)
        meta=list(meta)
    # Observed NL2 bet-size / street pools supply explicit fallback weights.
    # Regex matches villain nodes only; no private combo observations exist.
    for street in (1,2,3):
        ps=p['HU_facing_bet'][str(street)]
        for size,bucket in [('33','≤33%'),('50','34-55%'),('75','56-80%'),('100','81-110%')]:
            v=ps['by_size'][bucket];n=int(v['n'])
            if n>=500:
                config={'pat':r'(?:^|[ /])b'+size+r'$',
                        'fold':v['fold']/100,'raise':v['raise']/100}
                configs.append(config)
                meta.append({'pat':config['pat'],'n':n,'street':street,
                     'src':f'NL2.HU_facing_bet[{street}].by_size[{bucket}]',
                     'scope':'IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL',
                     'frozen_flop':loc,'size':int(size)})
        # Fallback raise response based observed marginal on betting facing raise.
        v=ps['bettor_vs_raise'];n=int(v['n'])
        if n>=500:
            config={'pat':r'(?:^|[ /])r$', 'fold':v['fold']/100,'raise':v['raise']/100}
            configs.append(config)
            meta.append({'pat':config['pat'],'n':n,'street':street,
                 'src':f'NL2.HU_facing_bet[{street}].bettor_vs_raise',
                 'scope':'IMPUTED_HISTORY_FROM_TRUE_STREET_RAISE_MARGINAL'})
    # When faced with a check: actual PFR c-bet rate when measured; otherwise
    # fixed 45% bet with a 33/50/75/100 sizing mix. Explicitly ASSUMED.
    family='3BP' if '3' in spot else 'SRP'
    position=('IP' if spot in ('BTN_BB','CO_BB','CO3_BTN') else 'OOP')
    if is_assumed:family='SRP';position='IP'
    ph=p['postflop_HU'][family+'_PFR_'+position]
    check_rate=ph['cbet']['pct']/100
    for pat,rate,scope in [
      (r'^$',check_rate,'NL2_PFR_CB_AGGREGATE_PROXY_NOT_EXACT_SPOT'),
      (r'^x$',check_rate,'NL2_PFR_CB_AGGREGATE_PROXY_NOT_EXACT_SPOT'),
      (r'.*/x$',0.45,'ASSUMED_CHECKED_TO_BET_45PCT'),
      (r'.*/$',0.45,'ASSUMED_STREET_ROOT_BET_45PCT')]:
        config={'pat':pat,'bet':rate,'sizes':[[33,.35],[50,.35],[75,.20],[100,.10]]}
        configs.append(config)
        meta.append({'pat':pat,'n':ph['cbet']['n'] if scope.startswith('NL2') else 0,
                     'src':scope,'scope':scope})
    return base+configs,meta

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--solver-root',required=True,type=pathlib.Path)
    a.add_argument('--spot',choices=SPOTS,required=True)
    a.add_argument('--version',choices=('gto','exp_ip','exp_oop'),default='gto')
    a.add_argument('--flop',required=True)
    a.add_argument('--turn-count',type=int,default=1)
    a.add_argument('--manifest',required=True,type=pathlib.Path)
    args=a.parse_args()
    if not 1<=args.turn_count<=3:a.error('turn-count 1..3')
    flop=args.flop;cards=[flop[i:i+2] for i in (0,2,4)]
    if len(flop)!=6 or len(set(cards))!=3 or not all(re.fullmatch('[23456789TJQKA][cdhs]',t) for t in cards):
        a.error('Invalid explicit flop')
    src=args.solver_root.resolve()
    pf=src/'postflop'
    if not (pf/'pfdriver/target/release/pfdriver').exists():
        raise SystemExit('Authentic Rust CFR driver unavailable')
    sys.path.insert(0,str(pf/'py'))
    ranges=importlib.import_module('ranges')
    pipeline=importlib.import_module('pipeline')
    job=importlib.import_module('job')
    LK=importlib.import_module('locks')
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    if args.spot in RULES:
        prof=RULES[args.spot]
        config={k:prof[k] for k in ('pot','stack','oop','ip','pfr')}
        config['kind']='SRP' # solver tree geometry only, NOT source pot family.
        ranges.SPOTS[args.spot]=config
        pipeline.SPOTS[args.spot]=config
        fn_pair=(w_iso_oop,w_iso_ip) if args.spot=='ISO_BTN_CO' else (lambda n:1.0,w_lmp_ip)
        weighted=tuple([[float(fn(n)) for n in ranges.NAMES] for fn in fn_pair])
        assert len(weighted[0])==len(weighted[1])==169
        original_range=job.ranges
        job.ranges=lambda sp,v:weighted if sp==args.spot else original_range(sp,v)
        # pipeline uses imported "make_job" and shares job.ranges global.
        extra_range=dict(source='ASSUMED_EXPLICIT_169CLASS',
            profile=prof,oop_169=dict(zip(ranges.NAMES,weighted[0])),
            ip_169=dict(zip(ranges.NAMES,weighted[1])))
    else:
        if args.spot in EXTRA_SPOTS:
            pp=EXTRA_SPOTS[args.spot]
            for place,act in pp['oopc']+pp['ipc']:
                if place not in ranges.ACTS or act not in ranges.ACTS[place]:
                    raise ValueError('Preflop range source action missing: '+place+'/'+act)
            ranges.SPOTS[args.spot]=pp
            pipeline.SPOTS[args.spot]=pp
        extra_range=dict(source='PINNED_POKER_SOLVER_PREFLOP_CFR',
                         spot=args.spot,
                         full_sha256=sha(src/'v8_build/build/pf_data.json'))
    spot=pipeline.SPOTS[args.spot]
    original_locks=pipeline.lock_list
    def lock_list(spot,ver,board):
        return make_fallbacks(spot,ver,pool,original_locks,board)
    pipeline.lock_list=lock_list
    orig_make=pipeline.make_job
    def sized_make(*pos,**kwargs):
        kwargs['target']=0.5
        kwargs['rank']=0.5 if args.version!='gto' else 1.5
        kwargs['iters']=1700
        j=orig_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES) # include donk or OOP-PFR cbet
        j['flop_ip']=','.join(SIZES)  # include IP stab / IP-PFR cbet
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=sized_make
    turns=pipeline.turns_for(flop)[:args.turn_count]
    lines=list(FLOP_ACTIONS)
    out=pf/'out'/args.spot/args.version
    out.mkdir(parents=True,exist_ok=True)
    path=out/(flop+'_multiboard.json')
    jpath=out/(flop+'_multiboard.job.json')
    extracted=[{'prefix':[], 'street':True}]+[
        dict(prefix=line.split()+[turn],street=False,raw=True)
        for line in lines for turn in turns]
    locks,lock_src=pipeline.lock_list(args.spot,args.version,flop)
    job_input=sized_make(args.spot,args.version,flop,str(path)+'.tmp',
        extract=extracted,locks=locks,compress=True)
    info=dict(schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
      spot=args.spot,version=args.version,flop=flop,
      pot_family='ISO' if args.spot=='ISO_BTN_CO' else 'LMP' if args.spot=='LMP_CO_BB' else '3BP' if '3' in args.spot else 'SRP',
      root_pot_bb=spot['pot'],root_remaining_bb=spot['stack'],
      root_spr=round(spot['stack']/spot['pot'],6),
      preflop_ranges=extra_range,
      n_NL2_hands=pool['hands'],
      pool_source_sha256=sha(src/'inputs/pool_stats.json'),
      solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
      flop_action_sizes=SIZES,allow_OOP_flop_leads=True,
      selected_lines=lines,turns=turns,
      locks=[{'pat':m['pat'],'scope':m.get('scope','PINNED_MEASURED_NL2_SOURCE'),'source':m.get('src'),
         'n':m.get('n')} for m in lock_src],
      unknown_action_frequency_policy='Use observed NL2 street/size marginals where available; fallback checked-to bet 45% with 33:35%,50:35%,75:20%,100:10%. No observed private-card behavior.',
      no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
      file_flop=str(path.relative_to(pf)),file_flop_sha256=None,
      cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        job.run(job_input,str(jpath))
        pathlib.Path(str(path)+'.tmp').rename(path)
        fr=json.loads(path.read_text())
        fr['turns']=turns
        path.write_text(json.dumps(fr,separators=(',',':')))
        info['file_flop_sha256']=sha(path)
        for line in lines:
            for turn in turns:
                parent=next((n for n in fr['nodes'] if n['line']==line+'/' and n['board'][-2:]==turn),None)
                if not parent or not parent.get('wr') or any(
                    sum(max(0,float(y)) for y in arr)<1e-4 for arr in parent['wr']):
                    info['skipped'].append(dict(line=line,turn=turn,reason='NO_BOTH_PLAYER_REACH'))
                    continue
                pipeline.solve_sub(args.spot,args.version,flop,fr,line,turn)
                sub=out/(flop+'_'+line.replace(' ','')+'_'+turn+'.json')
                if not sub.exists():raise FileNotFoundError('Missing true Rust subgame '+str(sub))
                d=json.loads(sub.read_text())
                source_nodes=[n for n in d['nodes'] if len(n['board'])>=8]
                if not any(len(n['board'])==10 for n in source_nodes):
                    raise ValueError('No authentic river node '+str(sub))
                info['cases'].append(dict(line=line,turn=turn,
                    source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
                    real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
                    flop_parent_pot_bb=parent['pot']/100,
                    flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
                    true_river_nodes=sum(len(n['board'])==10 for n in d['nodes']),
                    source_node_count=len(d['nodes']),
                    gto_gap_pct=d['info'].get('gto_expl_pct'),
                    hero_gap_pct=d['info'].get('hero_gap_pct'),
                    lock_stats=d['info'].get('lock_stats',{}),
                    status='GTO_EXACT_ONLY' if args.version=='gto' else 'NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT'))
    except Exception as e:
        info['failures'].append({'reason':str(e),'traceback':traceback.format_exc()[-2400:]})
    info['elapsed_seconds']=round(time.monotonic()-t0,2)
    info['solved_cases']=len(info['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:info[k] for k in ('spot','version','flop','solved_cases','elapsed_seconds','failures')},ensure_ascii=False))
    if info['failures'] or info['solved_cases']==0:raise SystemExit(1)
if __name__=='__main__':main()
