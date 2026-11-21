#!/usr/bin/env python3
"""B257 independent exact original 100bb CO_BB pinned-preflop-GTO + real Rust
NL2 CO-IP partially locked TURN and river verifier, ranks 60/61 only.

Never substitute opposite-seat OOP, different original flop source or false
measured NL2 per-hole-card actions; strict 40/70 prior actor reach remains.
"""
import argparse,gzip,hashlib,json,pathlib,os,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_sequential_cfr_reach import game_reach
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data'
SPECS={
 (60,'KsQh4d'):dict(gto='B251',gto_run=44902084841,child='B255',model='ln-ipfr-t_model-hxdit',line='x b50 c',spr=8.614),
 (60,'8s8h3d'):dict(gto='B252',gto_run=44902088039,child='B255',model='ln-ipfr-t_model-hxdit',line='x b50 c',spr=8.614),
 (61,'KsQh4d'):dict(gto='B253',gto_run=44902146101,child='B256',model='ln-ipfr-t_model-qpx6tn',line='x b100 c',spr=5.576),
 (61,'8s8h3d'):dict(gto='B254',gto_run=44902150376,child='B256',model='ln-ipfr-t_model-qpx6tn',line='x b100 c',spr=5.576)
}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as fp:
  for z in iter(lambda:fp.read(1048576),b''):h.update(z)
 return h.hexdigest()
def load(path):return json.loads(path.read_text())

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--rank',type=int,choices=(60,61),required=True)
 p.add_argument('--flop',choices=('KsQh4d','8s8h3d'),required=True)
 p.add_argument('--parent',type=pathlib.Path,required=True)
 p.add_argument('--fresh',type=pathlib.Path,required=True)
 a=p.parse_args();spec=SPECS[(a.rank,a.flop)]
 gto=spec['gto'];child=spec['child'];flop=a.flop;line=spec['line']
 pre='CO_BB';turn=None
 original_pin=D/f'nl2_hu_{gto.lower()}_rank{a.rank}_cobb_{flop}_gto_parent_pin.json'
 original_idx=D/f'solver_evidence/NL2_MULTIBOARD_{gto}_R{a.rank}_{flop.upper()}_GTO.index.json'
 original_archive=D/f'solver_evidence/NL2_MULTIBOARD_{gto}_R{a.rank}_{flop.upper()}_GTO.json.gz'
 assert all(z.is_file() for z in (original_pin,original_idx,original_archive))
 pin=load(original_pin);ix=load(original_idx)
 assert (pin['source_run_id'],ix['run_id'])==(spec['gto_run'],spec['gto_run'])
 assert (pin['spot'],pin['flop'],pin['flop_line'],pin['turn_line'])==(pre,flop,line,'x')
 assert (pin['target_rank'],pin['model_id'])==(a.rank,spec['model'])
 assert pin['preflop_CFR_pinned_not_observed_NL2_private_card'] is True
 assert pin['original_full_100bb_cobb_gto_source_pinned'] is True
 assert pin['target_exact_actor_IP_turn_strict_combos']>0
 assert ix['exact_target_actor_IP_turn_strict_combos']==pin['target_exact_actor_IP_turn_strict_combos']
 assert ix['source_sha256']==hashlib.sha256(gzip.decompress(original_archive.read_bytes())).hexdigest()
 assert ix['gzip_sha256']==sha(original_archive)
 assert (ix['gto_cases'],ix['locked_cases'],ix['verified_cases'])==(1,0,1)
 turn=pin['turn']
 parent=a.parent.resolve()
 manifest=parent/f'evidence/{pre}-gto-{flop}.json'
 root=parent/f'solver/postflop/out/{pre}/gto/{flop}_multiboard.json'
 rootjob=root.with_suffix('.job.json')
 for path,expected in [(manifest,pin['original_gto_manifest_sha256']),
     (root,pin['original_gto_root_sha256']),(rootjob,pin['original_gto_job_sha256'])]:
  assert path.is_file() and sha(path)==expected, 'Original 100bb source SHA mismatch '+str(path)
 m=load(manifest);fr=load(root);gj=load(rootjob)
 assert (m['spot'],m['version'],m['flop'])==(pre,'gto',flop)
 assert m['selected_lines']==[line] and m['turns']==[turn]
 assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
 assert (m['root_pot_bb'],m['root_remaining_bb'])==(5.5,97.5)
 assert (fr['flop'],fr['pot'],fr['stack'])==(flop,550,9750)
 assert (gj['pot'],gj['stack'],gj['rake_rate'],gj['rake_cap'])==(550,9750,.05,1000)
 assert gj.get('hero') is None and not gj.get('locks')
 assert fr['info']['gto_expl_pct']<=.5
 fresh=a.fresh.resolve()
 reportfile=fresh/f'evidence/{pre}-exp_ip-{flop}.json'
 src=fresh/f'solver/postflop/out/{pre}/exp_ip/{flop}_{line.replace(" ","")}_{turn}.json'
 jobfile=src.with_suffix('.job.json')
 assert all(z.is_file() for z in (reportfile,src,jobfile))
 rep=load(reportfile);raw=load(src);j=load(jobfile)
 assert rep['schema']==f'NL2_HU_{child}_TRUE_PINNED_CO_BB_GTO_FLOP_PARTIAL_NL2_IP_V1'
 assert (rep['target_rank'],rep['model_id'],rep['spot'],rep['flop'],rep['turn'])==(
     a.rank,spec['model'],pre,flop,turn)
 assert (rep['flop_line'],rep['exact_target_line'],rep['version'])==(line,line+'/x','exp_ip')
 assert rep['original_GTO_source_run_id']==spec['gto_run']
 assert rep['original_GTO_flop_root_sha256']==sha(root)
 assert rep['original_GTO_job_sha256']==sha(rootjob)
 assert rep['original_GTO_manifest_sha256']==sha(manifest)
 assert rep['original_GTO_pin_sha256']==sha(original_pin)
 assert rep['source_preflop']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
 assert rep['no_observed_private_card_NL2_rates'] and rep['original_GTO_flop_unchanged']
 assert rep['original_GTO_flop_full_sizing_not_reoptimized'] and rep['partially_locked_turn_river_only']
 assert rep['no_generic_CERT_upgrade'] and rep['PR2_Draft_NEVER_MERGE'] and rep['locks']
 assert not rep['failures'] and len(rep['cases'])==1
 c=rep['cases'][0]
 assert (c['flop'],c['turn'],c['exact_action_line'])==(flop,turn,line+'/x')
 assert (c['source_sha256'],c['original_exp_job_sha256'])==(sha(src),sha(jobfile))
 assert j['hero']==1 and j.get('locks') and j['rake_rate']==.05 and j['rake_cap']==1000
 assert raw['line0']==line and raw['turn']==turn
 assert any(len(n['board'])==8 for n in raw['nodes'])
 assert any(len(n['board'])==10 for n in raw['nodes'])
 reach,stats=game_reach(fr,raw)
 selected=[]
 for n in raw['nodes']:
  if not(n['line']==line+'/x' and n['player']==1 and len(n['board'])==8):continue
  q=reach['|'.join((n['board'],n['line'],'1'))]
  if q['count']<=0:continue
  spr=(raw['stack']-max(n['bets']))/n['pot']
  selected.append(dict(board=n['board'],strict_combos=q['count'],
      actual_spr=round(spr,7),relative_spr_error_pct=round(100*abs(spr-spec['spr'])/spec['spr'],4),
      allowed_actions=n['acts']))
 strict=sum(z['strict_combos'] for z in selected)
 match=sum(z['strict_combos'] for z in selected if z['relative_spr_error_pct']<=5)
 assert strict==c['strictly_reachable_actor_turn_combos']
 assert match==c['model_SPR_eligible_actor_turn_combos']
 assert rep['genuine_GTO_parent_actor_turn_strict_combos']==pin['target_exact_actor_IP_turn_strict_combos']>0
 data=src.read_bytes();packed=gzip.compress(data,compresslevel=9,mtime=0)
 dest=D/f'solver_evidence/NL2_MULTIBOARD_{child}_R{a.rank}_{flop.upper()}_EXP_IP.json.gz'
 idxpath=dest.with_suffix('').with_suffix('.index.json')
 dest.write_bytes(packed)
 result=dict(schema='NL2_HU_B257_CO_BB_EXACT_ORIGINAL_GTO_PLUS_REAL_NL2_IP_PARTIAL_LOCK_V1',
    source_run_id=int(os.environ['GITHUB_RUN_ID']),source_batch=child,original_GTO_batch=gto,
    original_GTO_source_run=spec['gto_run'],gto_pin_sha256=sha(original_pin),
    gto_index_sha256=sha(original_idx),gto_archive_sha256=sha(original_archive),
    original_GTO_root_sha256=sha(root),original_GTO_job_sha256=sha(rootjob),
    original_GTO_exploitability_pct=fr['info']['gto_expl_pct'],
    authentic_NL2_Rust_source_sha256=sha(src),nl2_job_sha256=sha(jobfile),
    authentic_NL2_Rust_gzip_sha256=sha(dest),
    spot=pre,rank=a.rank,model_id=spec['model'],flop=flop,turn=turn,
    exact_line=line+'/x',actor='CO_IP',acting_seat=1,model_SPR=spec['spr'],
    original_GTO_actor_strict_combos=pin['target_exact_actor_IP_turn_strict_combos'],
    NL2_actor_strict_combos=strict,NL2_actor_model_SPR_eligible_combos=match,
    genuine_actor_matched_GTO_NL2_board=(strict>0 and match>0),
    genuine_actor_node_examples=selected,
    NL2_source_lock_patterns=rep['locks'],actual_hero_gap_pct=c['hero_gap_pct'],
    authentic_rust_40_70_reach_stats=dict(stats),
    original_preflop_CFR_not_observed_NL2_private_cards=True,
    partial_downstream_only_not_whole_flop_lock=True,
    no_observed_per_private_hand_NL2_conditionals=True,
    no_generalized_nonpolar50_bet_advice=True,no_generic_CERT_upgrade=True,
    current_V39_CERT=152,current_V39_APPROX=240,PR2_Draft_NEVER_MERGE=True)
 idxpath.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 doc=ROOT/f'docs/NL2_HU_B257_R{a.rank}_{flop.upper()}_REAL_COIP_NL2_LOCK.md'
 doc.write_text(f'# B257 rank{a.rank} {flop}/{turn} original GTO + authentic CO-IP NL2 partial lock\n\n'
   f'B{gto[1:]} original full 100bb CO_BB preflop-CFR GTO root kept SHA-identical. '
   f'Authentic Rust {child} re-solved only downstream turn/river with pooled NL2 '
   f'bet/street marginal locks and declared defaults; true CO-IP action line {line}/x. '
   f'GTO strict actor combos {pin["target_exact_actor_IP_turn_strict_combos"]}; '
   f'NL2 strict actor combos {strict} and same-SPR combos {match}. '
   f'No observed private-hand opponent conditionals. '
   f'This is one exact-board example, not a 3–5 flop CERT or generic 50%-pot recommendation. '
   f'All V39 584 source and HU2475 full audits must pass before commit. '
   f'PR#2 Draft, NEVER MERGE.\n')
 print('PASS B257 independently verified actual Rust GTO+EXP CO-IP',json.dumps(
     dict(rank=a.rank,flop=flop,gto_strict=pin['target_exact_actor_IP_turn_strict_combos'],
       nl2_strict=strict,nl2_spr=match,paired=result['genuine_actor_matched_GTO_NL2_board'])))
if __name__=='__main__':main()
