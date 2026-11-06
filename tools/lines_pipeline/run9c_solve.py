"""Serial persistent batches, atomic validated checkpoints and input-aware resume."""
import json,os,subprocess,time,hashlib
from pathlib import Path
B=Path('/workspace/outputs/poker_lines_v2');O=B/'results/run9c';DRV='/workspace/postflop/pfdriver/target/release/pfdriver'
def digest(j):return hashlib.sha256(json.dumps(j,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 os.environ['RAYON_NUM_THREADS']='2'
 for item in sorted(json.load(open(O/'manifest.json')),key=lambda m:('rtf'.index(m['key'][0]),m['key'])):
  key=item['key'];p=O/(key+'.json');jp=O/(key+'.job.json');j=json.load(open(jp));sha=digest(j)
  try:d=json.load(open(p))
  except (FileNotFoundError,json.JSONDecodeError):d={}
  if d.get('job_sha256')==sha and d['info']['gto_expl_pct']<=j['target_pct']:
   print('skip',key,flush=True);continue
  # Solver writes a temporary result; only validated convergence becomes a checkpoint.
  temp=p.with_suffix('.pending.json');runjob=dict(j,out=str(temp));rjp=O/(key+'.running.json')
  json.dump(runjob,open(rjp,'w'))
  with (O/(key+'.log')).open('w') as f:
   print('start',key,time.ctime(),flush=True);proc=subprocess.run([DRV,str(rjp)],stdout=f,stderr=subprocess.STDOUT)
  if proc.returncode:raise RuntimeError((key,proc.returncode))
  d=json.load(open(temp));print('done',key,d['info'],flush=True)
  if d['info']['gto_expl_pct']>j['target_pct']:raise RuntimeError(('not converged',key))
  d['job_sha256']=sha;json.dump(d,open(temp,'w'));temp.replace(p);rjp.unlink()
 print('All jobs converged.',flush=True)
if __name__=='__main__':main()
