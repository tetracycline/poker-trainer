import json, hashlib, zipfile
from pathlib import Path
import sys
P=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
PIN=[('gto',14793708366,'f2ed6bb2438d3b7c4fb84d6e3195a5798504e3e0e6f0228ba2518c918f75f1ae',15114867243,'a43e4a0900781a16706c2355501649c521aa4109b6c98db4026df4808e0073d6'),('exp_oop',14793159254,'400b10c2f45130e018fd93f0eb6e8341189525086ce981b88fcdfce22da3eb87',15115576330,'48193c80ea7af8744c38a773454d6d6db47490a20b34647713afd0b086b291ac')]
def sha(b):return hashlib.sha256(b).hexdigest()
def arc(i,d):
 p=P/f'github-actions-artifact-{i}.zip';assert sha(p.read_bytes())==d;return zipfile.ZipFile(p)
def cards(h):return frozenset(h[i:i+2] for i in range(0,len(h),2))
def key(h):return ''.join(sorted(cards(h)))
def node(g,l,b,seat,pot,bets):
 n,=[n for n in g['nodes'] if n['line']==l and n['board']==b];assert (n['player'],n['pot'],n['bets'])==(seat,pot,bets);return n
def accepted(g,n,a):
 seat=n['player'];hands=g['hands'][seat];N=len(hands);i=n['acts'].index(a);assert len(n['strat'])==N*len(n['acts']) and len(n['w'][seat])==N
 out=set()
 for j,h in enumerate(hands):
  if n['w'][seat][j]<=1e-4:continue
  v=[max(0,float(n['strat'][k*N+j])) for k in range(len(n['acts']))];s=sum(v)
  if not s:continue
  v=[x/s for x in v];best=max(range(len(v)),key=lambda k:v[k]);
  if i==best or (v[i]>=.4-1e-7 and v[i]>=.7*v[best]-1e-7):out.add(key(h))
 return out
def main():
 modes={};raws={};metadata={}
 for mode,old,od,new,nd in PIN:
  with arc(old,od) as z, arc(new,nd) as t:
   rn,=[n for n in z.namelist() if n.endswith('_multiboard.json')];rraw=z.read(rn);r=json.loads(rraw);jroot=json.loads(z.read(rn.replace('.json','.job.json')))
   d=t.read('b888-source/native/result.json');s=json.loads(d);jraw=t.read('b888-source/native/job.json');j=json.loads(jraw);pr=json.loads(t.read('b888-source/proof.json'))
   assert pr['mode']==mode and sha(rraw)==pr['original_root_sha256'] and sha(d)==pr['result_sha256'] and sha(jraw)==pr['job_sha256']
   assert sha(t.read('b888-source/plan.json'))==pr['plan_sha256']
   assert (r['flop'],r['pot'],r['stack'],s['flop'],s['pot'],s['stack'])==('Ac'+'8d'+'3h',650,9750,'Ac'+'8d'+'3h',1300,9425)
   assert (j['turn'],j['line0'],j['turn_oop'],j['rake_rate'],j['rake_cap'])==('Qc',['x','b50','c','/'],'33.333333%,50%,100%',.05,1000)
   for g in (r,s):assert 0<=g['info']['gto_expl_pct']<=.5
   if mode=='exp_oop':
    assert j['hero']==jroot['hero']==0 and j['locks'] and jroot['locks'] and 0<=r['info']['hero_gap_pct']<=.5 and 0<=s['info']['hero_gap_pct']<=.5
   else:assert not j.get('locks') and not jroot.get('locks') and not s['info'].get('lock_stats')
   flop='3h8dAc';turn=flop+'Qc';a=node(r,'',flop,0,650,[0,0]);b=node(r,'x',flop,1,650,[0,0]);c=node(r,'x b50',flop,0,975,[0,325]);p=node(r,'x b50 c/',turn,0,1300,[325,325]);u=node(s,'x b50 c/',turn,0,1300,[0,0]);v=node(s,'x b50 c/b33',turn,1,1733,[433,0]);
   for seat,k in enumerate(('oop_w','ip_w')):assert j[k]==[[h,w] for h,w in zip(r['hands'][seat],p['wr'][seat],strict=True) if w>1e-4]
   hero=accepted(r,a,'x')&accepted(r,c,'c')&accepted(s,u,'b33');villain=accepted(r,b,'b50')&accepted(s,v,'c');modes[mode]={};raws[mode]={}
   assert len(pr['rows'])==8
   for board,row in pr['rows'].items():
    assert board.startswith(turn) and len(cards(board))==5 and row['public_board']==board and row['acting_seat']==0 and row['line']=='x b50 c/b33 c/'
    n=node(s,'x b50 c/b33 c/',board,0,2166,[433,433]);assert 'b50' in n['acts']
    hs={h for h in hero&accepted(s,n,'x') if cards(h).isdisjoint(cards(board))};vs={key(h) for h,w in zip(s['hands'][1],n['w'][1],strict=True) if w>1e-4 and cards(h).isdisjoint(cards(board))}&villain
    allpairs={(h,v) for h in hs for v in vs if cards(h).isdisjoint(cards(v))};pairs=set()
    for h,opps in row['rendered_exact_deals'].items():
     h=key(h);claimed={key(v) for v in opps};assert h in hs and claimed=={v for v in vs if cards(h).isdisjoint(cards(v))};pairs|={(h,v) for v in claimed}
    assert pairs<=allpairs;modes[mode][board]=pairs;raws[mode][board]=allpairs
   metadata[mode]=dict(original_artifact=old,original_archive_sha256=od,continuation_artifact=new,continuation_archive_sha256=nd,root_sha256=sha(rraw),native_job_sha256=sha(jraw),native_result_sha256=sha(d),gto_gap_pct=s['info']['gto_expl_pct'],hero_gap_pct=s['info'].get('hero_gap_pct'))
 assert set(modes['gto'])==set(modes['exp_oop']);rows=[]
 for b in sorted(modes['gto']):
  g,e=modes['gto'][b],modes['exp_oop'][b];shared=g&e;rows.append(dict(board=b,gto_rendered_pairs=len(g),nl2_rendered_pairs=len(e),shared_rendered_pairs=len(shared),shared_hero_combos=len({h for h,v in shared}),shared_rendered_deals=sorted(shared),raw_shared_pairs_before_render_filter=len(raws['gto'][b]&raws['exp_oop'][b])))
 result=dict(schema='B892_INDEPENDENT_RAW_ACTION_WITNESS_V1',rank=158,model='ln-opfr-r_model-tl6ij8',sources=metadata,rows=rows,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope='Direct native per-card action and both-seat blocker validation of each reported rendered deal, independent of archived proof mask. Rendered cell completeness and original full replay still require B891. No certification.')
 print(json.dumps(result,sort_keys=True,indent=2))
if __name__=='__main__':main()
