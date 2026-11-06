"""Single classifier adapter for historical scripts; never modifies source libraries."""
import sys
# common classifier is vendored alongside this module
from common import hcls,texture,ctype
from phevaluator import evaluate_cards
H={'S':'strong','TPG':'top_good','TPW':'top_weak','MID':'mid_low','DRAW':'draw','WDRAW':'weak_draw','AIR':'air'}
def hand_class(h,b): return H[hcls(h,b)]
def turn_type(f,t): return ctype(f+t,2)
def classes(h,b):
 c=hcls(h,b)
 if len(b)==10 and evaluate_cards(*[b[i:i+2]for i in range(0,10,2)])==evaluate_cards(*[x[i:i+2]for x in [h,b]for i in range(0,len(x),2)]):return ['AIR']
 if len(b)==10 and c in ('AIR','WDRAW'):
  old=hcls(h,b[:8])
  if old in ('DRAW','WDRAW'): return [old] # mutually exclusive missed-draw buckets
 return [c]
