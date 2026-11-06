"""Exact own-action reach and compatible joint weights from initial ranges.
Never infer reach percentages from the driver's unnormalised joint marginals.
"""
from collections import defaultdict
from run10_common import hcls,classes
R='23456789TJQKA'
def canon(h):return tuple(sorted([h[:2],h[2:]]))
def label(h):
 a,b=sorted([h[:2],h[2:]],key=lambda c:-R.index(c[0]));return a[0]+b[0]+(''if a[0]==b[0]else's'if a[1]==b[1]else'o')
def initial(d,j):
 out=[]
 for p,k in enumerate(['oop','ip']):
  if j.get(k+'_w'):
   w={canon(h):v for h,v in j[k+'_w']};out.append([w.get(canon(h),0)for h in d['hands'][p]])
  else:
   w={h:float(v)for h,v in (x.split(':')for x in j[k].split(','))};out.append([w.get(label(h),0)for h in d['hands'][p]])
 return out
def joint(d,rr,p):
 q=1-p;total=sum(rr[q]);cs=defaultdict(float);pairs={}
 for h,w in zip(d['hands'][q],rr[q]):cs[h[:2]]+=w;cs[h[2:]]+=w;pairs[canon(h)]=w
 return [w*max(0,total-cs[h[:2]]-cs[h[2:]]+pairs.get(canon(h),0))for h,w in zip(d['hands'][p],rr[p])]
def reaches(d,j,targets=None):
 init=initial(d,j);root=' '.join(j.get('line0',[])).replace(' /','/').replace('/ ','/')
 nodes={(n['board'],n['line']):n for n in d['nodes']};result={}
 root_street=2 if j.get('river') else 1 if j.get('turn') else 0
 for target in (targets if targets is not None else d['nodes']):
  board=target['board'];line=target['line'];rr=[list(v)for v in init]
  blocked={board[i:i+2]for i in range(0,len(board),2)}
  rr=[[0 if set(canon(h))&blocked else w for h,w in zip(d['hands'][p],rr[p])]for p in [0,1]]
  prefix=root;st=root_street;tail=line[len(root):] if line.startswith(root) else None
  if tail is None:continue
  ok=True
  for a in tail.replace('/',' / ').split():
   if a=='/':prefix=prefix.rstrip()+'/';st+=1;continue
   n=nodes.get((board[:6+2*st],prefix))
   if n is None:ok=False;break
   p=n['player'];N=len(d['hands'][p]);k=n['acts'].index(a)
   rr[p]=[w*n['strat'][k*N+i]/max(1e-12,sum(n['strat'][l*N+i]for l in range(len(n['acts']))))for i,w in enumerate(rr[p])]
   prefix=(prefix+(''if prefix.endswith('/')else' ')+a).strip()
  if ok:result[(board,line)]=rr
 return result

def metrics(d,j,n,rr,cl):
 p=n['player'];board=n['board'];inds=[i for i,h in enumerate(d['hands'][p])if cl in classes(h,board)]
 base=initial(d,j);blocked={board[i:i+2]for i in range(0,len(board),2)}
 base=[[0 if set(canon(h))&blocked else w for h,w in zip(d['hands'][q],base[q])]for q in [0,1]]
 den=sum(base[p][i]for i in inds);own=sum(rr[p][i]for i in inds);jw=joint(d,rr,p);bj=joint(d,base,p)
 return dict(own_share=own/den if den else 0,joint_share=sum(jw[i]for i in inds)/sum(bj[i]for i in inds)if sum(bj[i]for i in inds)else 0,base_mass=den,own_mass=own,joint_mass=sum(jw[i]for i in inds),conditional_on_job_root=True),inds,jw
