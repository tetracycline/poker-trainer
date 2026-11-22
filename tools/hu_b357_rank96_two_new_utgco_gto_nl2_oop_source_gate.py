#!/usr/bin/env python3
"""B357 frozen next high-frequency rank96 UTG_CO OOP on RIVER:
original full100bb b33 c/b50 c/ GTO vs true Rust NL2 exp_oop 40/70 whole prior street,
exact named public flop/turn/river and model SPR4.15; source-only not generic CERT.
"""
import argparse,gzip,hashlib,json,pathlib
from hu_sequential_cfr_reach import accepted,game_reach
D=pathlib.Path(__file__).resolve().parents[1]/'data'
FLOPS=('8s8h3d','Js9h4d')
VERSIONS=('gto','exp_oop')
SPOT='UTG_CO';LINE='b33 c/b50 c/';SPR=4.15
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--downloads',type=pathlib.Path,required=True)
 p.add_argument('--run',type=int,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 idxfile=D/'solver_evidence/NL2_MULTIBOARD_B357_R96_UTGCO_TWO.index.json'
 gzfile=D/'solver_evidence/NL2_MULTIBOARD_B357_R96_UTGCO_TWO.json.gz'
 i=json.loads(idxfile.read_text());raw=gzip.decompress(gzfile.read_bytes());archive=json.loads(raw)
 assert (i['run_id'],i['actual_spot_flop_version_jobs'])==(a.run,4)
 assert i['source_sha256']==hashlib.sha256(raw).hexdigest() and i['gzip_sha256']==sha(gzfile)
 assert archive['source_run_id']==a.run and not archive['errors'] and len(archive['artifacts'])==4
 assert {(z['flop'],z['version']) for z in archive['artifacts']}=={(f,v) for f in FLOPS for v in VERSIONS}
 rows=[]
 for flop in FLOPS:
  pairs={}
  for ver in VERSIONS:
   base=a.downloads/f'nl2-multiboard-B357_R96_UTGCO_TWO-{SPOT}-{flop}-{ver}'
   mf=base/f'evidence/{SPOT}-{flop}-{ver}.json'
   root=base/f'solver/postflop/out/{SPOT}/{ver}/{flop}_multiboard.json'
   job=root.with_suffix('.job.json')
   assert all(x.is_file() for x in (mf,root,job))
   m=json.loads(mf.read_text());fr=json.loads(root.read_text())
   assert (m['spot'],m['flop'],m['version'])==(SPOT,flop,ver)
   assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
   assert m['flop_size_profile']=='full' and not m['restricted_tree_assumption']
   assert m['selected_lines']==['b33 c'] and m['solved_cases']==1 and not m['failures']
   assert (m['root_pot_bb'],m['root_remaining_bb'])==(6.5,97.5)
   assert (fr['pot'],fr['stack'],fr['flop'])==(650,9750,flop)
   assert m['file_flop_sha256']==sha(root) and fr['info']['gto_expl_pct']<=.5
   roots=[n for n in fr['nodes'] if n['line']=='' and n['player']==0 and len(n['board'])==6]
   assert len(roots)==1 and 'b33' in roots[0]['acts']
   root_eligible=len(accepted(roots[0],fr['hands'],'b33'))
   c=m['cases'][0]
   assert (c['line'],c['turn'])==('b33 c',m['turns'][0])
   sub=base/'solver/postflop'/c['source_path']
   assert sub.is_file() and sha(sub)==c['source_sha256']
   child=json.loads(sub.read_text())
   assert child['line0']=='b33 c' and child['turn']==c['turn']
   assert child['info']['gto_expl_pct']<=.5
   if ver=='exp_oop':assert child['info']['hero_gap_pct']<=.5
   overlay,stats=game_reach(fr,child)
   # OOP is hero on river after OOP flop33 bet/called and OOP turn50 bet/called.
   rawnodes=[n for n in child['nodes'] if n['player']==0 and
     n['line']==LINE and len(n['board'])==10]
   legal={}
   for n in rawnodes:
    q=overlay.get('|'.join((n['board'],n['line'],'0')))
    assert q is not None
    spr=(fr['stack']-max(n['bets']))/n['pot']
    if abs(spr-SPR)/SPR<=.05 and q['count']>0:
     legal[n['board']]=dict(count=q['count'],SPR=spr,actions=n['acts'])
   pairs[ver]=dict(original_gto_or_independent_nl2=ver,
     original_100bb_full_flop_root_sha256=sha(root),
     original_flop_job_sha256=sha(job),original_manifest_sha256=sha(mf),
     true_rust_turn_river_sha256=sha(sub),
     flop_b33_strict_40_70_root_combo_count=root_eligible,
     exact_target_actor_OOP_river_positive_source_nodes=legal,
     exact_target_actor_OOP_strict_source_combo_rows=sum(z['count'] for z in legal.values()),
     actual_matched_source_node_count=len(legal),
     no_conditional_private_card_NL2_observations=True,
     source_reach_stats=dict(stats),turn=c['turn'])
  assert pairs['gto']['turn']==pairs['exp_oop']['turn']
  common=set(pairs['gto']['exact_target_actor_OOP_river_positive_source_nodes'])&set(pairs['exp_oop']['exact_target_actor_OOP_river_positive_source_nodes'])
  rows.append(dict(flop=flop,turn=pairs['gto']['turn'],GTO=pairs['gto'],
     real_NL2_OOP_partial_lock=pairs['exp_oop'],
     authentic_actor_spr_and_exact_public_river_matched=bool(common),
     matching_positive_public_river_boards=sorted(common),
     no_premature_or_generic_texture_CERT=True))
 status=D/'nl2_hu_multiboard_status_v46_b354_rank79.json'
 v=json.loads(status.read_text())
 assert (v['CERT_MULTIBOARD'],v['APPROX'],v['EST'],v['TOTAL'])==(158,234,0,392)
 m=v['records']['ln-opfr-r_model-18g2rvt']
 assert (m['frequency_rank'],m['solver_profile'],m['street'],m['assumed_model_node_spr'])==(96,SPOT,2,SPR)
 assert m['label']=='APPROX'
 out=dict(schema='NL2_HU_B357_RANK96_TWO_NEW_GENUINE_ORIGINAL_UTGCO_GTO_NL2_OOP_RIVER_SOURCE_V1',
   original_run=a.run,authentic_cases=4,flops=rows,
   true_matching_new_original_GTO_plus_NL2_actor_OOP_flops=[r['flop'] for r in rows if r['authentic_actor_spr_and_exact_public_river_matched']],
   historic_successful_original_stage2_Ks7h2d_river_GTO_NL2_source_run=44654973894,
   full_flop_original100bb_preflop_CFR_not_assumed_LMP=True,
   frozen_rank96_model='ln-opfr-r_model-18g2rvt',target_line=LINE,actor='UTG_OOP',model_spr=SPR,
   no_GTO_only_cert_or_invented_private_card_NL2_rates=True,
   original_V46_CERT=158,original_V46_APPROX=234,original_V46_sha256=sha(status),
   PR2_Draft_NEVER_MERGE=True)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('PASS B357 rank96 exact new original100bb GTO/real NL2 OOP source',[
    (z['flop'],z['GTO']['exact_target_actor_OOP_strict_source_combo_rows'],
     z['real_NL2_OOP_partial_lock']['exact_target_actor_OOP_strict_source_combo_rows'],
     len(z['matching_positive_public_river_boards'])) for z in rows])
if __name__=='__main__':main()
