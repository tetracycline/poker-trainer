#!/usr/bin/env python3
"""B288: independently SHA-verify genuine original B286 100bb full-flop GTO
and separately solved real Rust NL2 CO-IP turn/river hero partial lock.
Only exact 7s7h2d/3s x b50 c/x, 40/70 previous-street per-combo reach,
SPR 19.55<=5%. No private-card NL2 measured rates, no generic CERT.
"""
import argparse,gzip,hashlib,json,os,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_sequential_cfr_reach import game_reach
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data';DOC=ROOT/'docs'
SPOT='LMP_CO_BB';FLOP='7s7h2d';TURN='3s';LINE='x b50 c/x'
PIN=D/'nl2_hu_b286_rank46_lmp_7s7h2d_gto_parent_pin.json'
IDX=D/'solver_evidence/NL2_MULTIBOARD_B286_R46_7S7H2D_GTO.index.json'
ARCH=D/'solver_evidence/NL2_MULTIBOARD_B286_R46_7S7H2D_GTO.json.gz'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(1048576),b''):h.update(z)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--parent',type=pathlib.Path,required=True)
 ap.add_argument('--fresh',type=pathlib.Path,required=True)
 a=ap.parse_args()
 p=load(PIN);i=load(IDX)
 assert p['schema']=='NL2_HU_B286_RANK46_LMP_7S7H2D_GTO_PARENT_PIN_V1'
 assert (p['source_run_id'],i['run_id'])==(44939456600,44939456600)
 assert (p['target_rank'],p['model_id'])==(46,'ln-iso-lmp_t_model-17z0wyl')
 assert (p['spot'],p['flop'],p['turn'],p['flop_line'],p['turn_line'])==(
  SPOT,FLOP,TURN,'x b50 c','x x')
 assert p['target_exact_actor_IP_turn_strict_combos']==i['exact_target_actor_IP_strict_combos']==12
 assert p['target_exact_actor_IP_turn_nodes']==1
 assert p['original_full_100bb_lmp_gto_not_recomputed'] and p['assumed_limped_169class']
 assert p['observed_preflop_ranges'] is False and p['direct_nl2_lock_source_present'] is False
 assert (i['verified_cases'],i['gto_cases'],i['locked_cases'])==(1,1,0)
 assert i['no_generic_model_certification'] and i['immediate_CERT_upgrades']==0
 assert i['source_sha256']==hashlib.sha256(gzip.decompress(ARCH.read_bytes())).hexdigest()
 assert i['gzip_sha256']==sha(ARCH)
 assert (i['original_parent_GTO_root_SHA256'],i['original_parent_GTO_job_SHA256'],
         i['original_parent_GTO_manifest_SHA256'])==(
         p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
 orig=a.parent.resolve()
 manifest=orig/f'evidence/{SPOT}-gto-{FLOP}.json'
 root=orig/f'solver/postflop/out/{SPOT}/gto/{FLOP}_multiboard.json'
 jobfile=root.with_suffix('.job.json')
 for file,digest in ((manifest,p['original_gto_manifest_sha256']),
                     (root,p['original_gto_root_sha256']),
                     (jobfile,p['original_gto_job_sha256'])):
  assert file.is_file() and sha(file)==digest, 'Original GTO SHA mismatch '+str(file)
 m=load(manifest);fr=load(root);origjob=load(jobfile)
 assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
 assert (m['spot'],m['flop'],m['version'])==(SPOT,FLOP,'gto')
 assert m['selected_lines']==['x b50 c'] and m['selected_turn_lines']==['x x']
 assert m['turns']==[TURN]
 assert m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
 assert (m['root_pot_bb'],m['root_remaining_bb'])==(2.5,99.)
 assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,250,9900)
 assert (origjob['pot'],origjob['stack'],origjob['rake_rate'],origjob['rake_cap'])==(250,9900,.05,1000)
 assert origjob.get('hero') is None and not origjob.get('locks')
 assert 0<=float(fr['info']['gto_expl_pct'])<=.5
 fresh=a.fresh.resolve()
 repfile=fresh/f'evidence/{SPOT}-exp_ip-{FLOP}.json'
 sub=fresh/f'solver/postflop/out/{SPOT}/exp_ip/{FLOP}_xb50c_{TURN}.json'
 subjob=sub.with_suffix('.job.json')
 assert all(x.is_file() for x in (repfile,sub,subjob)), 'Missing actual fresh Rust EXP evidence'
 report,raw,rustjob=load(repfile),load(sub),load(subjob)
 assert report['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
 assert (report['spot'],report['version'],report['flop'])==(SPOT,'exp_ip',FLOP)
 assert report['selected_lines']==['x b50 c'] and report['selected_turn_lines']==['x x']
 assert report['flop_line_policy']=='checked-b50only' and report['turn_line_policy']=='xxonly'
 assert report['flop_parent_mode']=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK'
 assert report['original_full_GTO_flop_byte_identical_not_recomputed'] is True
 assert report['gto_parent_source_run_id']==44939456600
 assert report['gto_parent_source_sha256']==sha(root)
 assert report['gto_parent_source_manifest_sha256']==sha(manifest)
 assert report['flop_root_jobfile_sha256']==sha(jobfile)
 assert report['original_B282_parent_pin_sha256']==sha(PIN)
 assert report['NL2_hero_lock_scope']=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO'
 assert report['restricted_tree_assumption'] is False
 assert report['no_generic_certification'] and report['not_observed_exact_NL2_hero_EV']
 assert not report['failures'] and report['solved_cases']==1 and len(report['cases'])==1
 assert report['locks'] and report['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
 case=report['cases'][0]
 assert (case['line'],case['turn'])==('x b50 c',TURN)
 assert case['source_sha256']==sha(sub)
 assert rustjob['hero']==1 and rustjob.get('locks')
 assert (rustjob['rake_rate'],rustjob['rake_cap'])==(.05,1000)
 assert (raw['line0'],raw['turn'])==('x b50 c',TURN)
 assert any(len(z['board'])==10 for z in raw['nodes'])
 assert any(len(z['board'])==8 for z in raw['nodes'])
 reach,stats=game_reach(fr,raw)
 matched=[]
 for n in raw['nodes']:
  if n['line']!=LINE or n['player']!=1 or len(n['board'])!=8:continue
  k='|'.join((n['board'],n['line'],'1'))
  q=reach[k]
  if q['count']<=0:continue
  spr=(raw['stack']-max(n['bets']))/n['pot']
  matched.append(dict(board=n['board'],strict_combos=q['count'],
     spr=round(spr,6),relative_spr_error_pct=round(100*abs(spr-19.55)/19.55,4),
     allowed_actions=n['acts']))
 strict=sum(n['strict_combos'] for n in matched)
 exact=sum(n['strict_combos'] for n in matched if n['relative_spr_error_pct']<=5)
 gzip_path=D/'solver_evidence/NL2_MULTIBOARD_B288_R46_7S7H2D_EXP_IP.json.gz'
 gzip_path.write_bytes(gzip.compress(sub.read_bytes(),compresslevel=9,mtime=0))
 source_sha=sha(sub);compressed_sha=sha(gzip_path)
 result=dict(schema='NL2_HU_B288_R46_AUTHENTIC_ORIGINAL_B286_GTO_PLUS_RUST_NL2_COIP_V1',
     original_GTO_source_run=44939456600,source_run_id=int(os.environ['GITHUB_RUN_ID']),
     original_GTO_batch='B286',source_batch='B288',
     original_GTO_parent_pin_sha256=sha(PIN),original_GTO_index_sha256=sha(IDX),
     original_GTO_archive_sha256=sha(ARCH),
     original_GTO_root_sha256=sha(root),original_GTO_job_sha256=sha(jobfile),
     original_GTO_manifest_sha256=sha(manifest),
     true_original_GTO_root_unchanged=True,
     original_GTO_exploitability_pct=fr['info']['gto_expl_pct'],
     NL2_actual_Rust_source_sha256=source_sha,NL2_actual_Rust_gzip_sha256=compressed_sha,
     NL2_actual_Rust_job_sha256=sha(subjob),
     original_100bb_GTO_strict_actor_IP_combos=12,
     NL2_strict_actor_IP_combos=strict,
     NL2_actor_IP_model_SPR_eligible_combos=exact,
     genuine_same_exact_board_actor_line_SPR_paired=(exact>0),
     exact_public_board=FLOP+TURN,flop=FLOP,turn=TURN,
     spot=SPOT,actor='CO_IP',acting_seat=1,model_id='ln-iso-lmp_t_model-17z0wyl',rank=46,
     exact_line=LINE,model_SPR=19.55,
     actual_strict_nodes=matched,actual_sequential_40_70_gate_stats=dict(stats),
     NL2_partial_hero_gap_pct=case['hero_gap_pct'],
     observed_NL2_per_private_card_frequencies=False,
     observed_pool_marginals_only_where_available=True,
     assumed_limped_preflop_169class=True,
     only_downstream_turn_river_locked=True,
     no_generic_texture_CERT=True,no_automatic_CERT_upgrade=True,
     V41_CERT=154,V41_APPROX=238,V41_EST=0,
     PR2_Draft_NEVER_MERGE=True)
 index=D/'solver_evidence/NL2_MULTIBOARD_B288_R46_7S7H2D_EXP_IP.index.json'
 index.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 doc=DOC/'NL2_HU_B288_R46_7S7H2D_ACTUAL_RUST_NL2_PARTIAL_LOCK.md'
 doc.write_text('# B288 rank46 original B286 GTO + authentic NL2 CO-IP partial Rust source\n\n'
  'Third exact flop 7s7h2d/3s, original complete 100bb B286 GTO strictly reachable '
  'actor CO-IP x b50 c/x combos 12 and GTO root SHA checked unchanged. '
  f'New Rust partially locked downstream NL2 has {strict} legal CO-IP turn combos, '
  f'{exact} passing model SPR19.55 ±5%, genuine actor paired={exact>0}. '
  f'True GTO original exploitability {fr["info"]["gto_expl_pct"]}%; '
  f'partial NL2 hero gap {case["hero_gap_pct"]}. '
  'Any private-hand NL2 conditional rate remains UNOBSERVED; pooled street/size '
  'marginals and assumed defaults must remain disclosed. '
  'No automatic generic rank46 or texture CERT; third-board certification '
  'requires a separately audited V42-only promotion. '
  'V41 154 CERT/238 APPROX, 590 existing boards, HU2475/2475 audit required. '
  'PR#2 Draft NEVER MERGE.\n')
 print('PASS B288 genuine original source',json.dumps(dict(gto=12,NL2=strict,eligible=exact,
   paired=exact>0,source_sha=source_sha),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
