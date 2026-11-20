#!/usr/bin/env python3
"""Fail-closed NL2 exact-node intake; no solver integration."""
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

POS = ('SB','BB','UTG','HJ','CO','BTN')
SHA = re.compile(r'[0-9a-f]{64}')
CARD = re.compile(r'[2-9TJQKA][cdhs]')
FAMILIES = {'SRP': (False,1), '3BP': (False,2), 'ISO': (True,1), 'LMP': (True,0)}
MIN_N = 500

def require(condition, code):
    if not condition:
        raise ValueError(code)

def integer(x, lo=0):
    return type(x) is int and x >= lo

def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def digest_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def exact_dict(x, fields, code):
    require(isinstance(x,dict) and set(x)==set(fields.split()), code)

def unique_keys(pairs):
    out={}
    for k,v in pairs:
        require(k not in out,'DUPLICATE_JSON_KEY')
        out[k]=v
    return out

def no_constant(_):
    raise ValueError('NONFINITE_JSON')

def check_manifest(manifest_bytes, expected_sha, source_path, allow_synthetic=False):
    require(isinstance(expected_sha,str) and SHA.fullmatch(expected_sha)
            and digest_bytes(manifest_bytes)==expected_sha, 'MANIFEST_SHA_MISMATCH')
    x=json.loads(manifest_bytes,object_pairs_hook=unique_keys,parse_constant=no_constant)
    exact_dict(x,'schema synthetic source rows','MANIFEST_FIELDS')
    require(x['schema']=='NL2_EXACT_NODE_LOCK_INTAKE_V1' and type(x['synthetic']) is bool,'BAD_SCHEMA')
    require(not x['synthetic'] or allow_synthetic,'SYNTHETIC_NOT_EMPIRICAL')
    src=x['source']
    exact_dict(src,'sha256 start end provenance dedup attested_hand_count parsed_hand_count rejected_hand_count reject_counts sampling','SOURCE_FIELDS')
    require(isinstance(src['sha256'],str) and SHA.fullmatch(src['sha256']) and digest_file(source_path)==src['sha256'],'SOURCE_SHA_MISMATCH')
    for k in ('start','end'):
        require(isinstance(src[k],str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',src[k]),'SOURCE_DATES')
    require(date.fromisoformat(src['start'])<=date.fromisoformat(src['end']),'SOURCE_DATES')
    require(type(src['provenance']) is str and len(src['provenance'].strip())>=10,'SOURCE_PROVENANCE')
    require(src['dedup']=='UNIQUE_SITE_HAND_ID','SOURCE_DEDUP')
    require(src['sampling'] in ('PUBLIC_ACTION_HISTORIES','PRIVATE_HOLECARDS_INDEPENDENT_OF_SHOWDOWN','SHOWDOWN_ONLY'),'SOURCE_SAMPLING')
    require(all(integer(src[k]) for k in ('attested_hand_count','parsed_hand_count','rejected_hand_count')),'SOURCE_COUNTS')
    rej=src['reject_counts']
    require(isinstance(rej,dict) and all(k and integer(v) for k,v in rej.items()) and sum(rej.values())==src['rejected_hand_count'],'SOURCE_REJECT_COUNTS')
    require(src['attested_hand_count']==src['parsed_hand_count']+src['rejected_hand_count'],'SOURCE_COUNTS')
    require(isinstance(x['rows'],list) and x['rows'],'NO_ROWS')
    keys=set()
    for row in x['rows']:
        key=check_row(row,src)
        require(key not in keys,'DUPLICATE_NODE')
        keys.add(key)
    return {'status':'SYNTHETIC_TEST_ONLY' if x['synthetic'] else 'VALIDATED_INPUT_CONTRACT_ONLY',
            'rows':len(keys),'corpus_sha256':src['sha256'],
            'not_verified':'Corpus aggregation and sampling design are source attestations, not independently authenticated by this structural validator. No solver/lock authorization.'}

def check_row(row,src):
    exact_dict(row,'cohort preflop flop_state board street prior_streets current_actions node counts n mode combo','ROW_FIELDS')
    c=row['cohort']
    exact_dict(c,'stake table seats family positions rake ante','COHORT_FIELDS')
    require(c['stake']=='NL2' and c['table']=='NLHE_CASH' and type(c['seats']) is int
            and c['seats']==6 and c['family'] in FAMILIES and type(c['ante']) is int and c['ante']==0,'UNSUPPORTED_COHORT')
    require(isinstance(c['positions'],list) and len(c['positions'])==2
            and all(p in POS for p in c['positions']) and POS.index(c['positions'][0])<POS.index(c['positions'][1]),'POSITIONS_OOP_IP')
    require(isinstance(c['rake'],str) and c['rake'].strip(),'RAKE_PROFILE')
    mode=row['mode']
    require(mode in ('AGGREGATE_FREQUENCY','EXACT_PRIVATE_COMBO'),'UNSUPPORTED_MODE')
    board=row['board']; street=row['street']
    require(type(street) is int and street in (1,2,3) and isinstance(board,list)
            and len(board)==street+2 and all(isinstance(k,str) and CARD.fullmatch(k) for k in board)
            and len(set(board))==len(board),'PUBLIC_BOARD')
    require(board[:3]==sorted(board[:3]),'CANONICAL_FLOP_ORDER')
    if mode=='EXACT_PRIVATE_COMBO':
        require(src['sampling']=='PRIVATE_HOLECARDS_INDEPENDENT_OF_SHOWDOWN','COMBO_REQUIRES_NON_SHOWDOWN_SAMPLING')
        cards=row['combo']
        require(isinstance(cards,list) and len(cards)==2
                and all(isinstance(k,str) and CARD.fullmatch(k) and k not in board for k in cards)
                and cards[0]<cards[1],'INVALID_COMBO')
    else:
        require(row['combo'] is None,'UNEXPECTED_COMBO')
        require(src['sampling']!='SHOWDOWN_ONLY','BIASED_AGGREGATE_SAMPLING')
    flop=row['flop_state']
    exact_dict(flop,'pot remaining','FLOP_STATE')
    require(integer(flop['pot'],3) and isinstance(flop['remaining'],list)
            and len(flop['remaining'])==2 and all(integer(s,1) for s in flop['remaining']),'FLOP_CHIPS')
    check_preflop(row['preflop'],c,flop)
    prior=row['prior_streets']; current=row['current_actions']
    require(isinstance(prior,list) and len(prior)==street-1 and isinstance(current,list),'EXACT_PRIOR_STREETS')
    pot=flop['pot']; remaining=flop['remaining'][:]
    for actions in prior:
        require(isinstance(actions,list),'STREET_ACTIONS')
        st=replay(actions,pot,remaining)
        require(st['closed_by'] in ('XX','CALL') and all(st['remaining']),'PRIOR_STREET_NOT_PLAYABLE')
        pot=st['pot'];remaining=st['remaining']
    st=replay(current,pot,remaining)
    require(st['closed_by'] is None and all(st['remaining']),'TERMINAL_CURRENT_NODE')
    node=row['node']
    exact_dict(node,'actor pot remaining committed spr_num spr_den menu','NODE_STATE')
    require(all(node[k]==st[k] for k in ('actor','pot','remaining','committed'))
            and type(node['actor']) is int and type(node['pot']) is int
            and all(integer(v) for k in ('remaining','committed') for v in node[k]),'NODE_CHIP_MISMATCH')
    require(integer(node['spr_num']) and integer(node['spr_den'],1)
            and node['spr_num']*st['pot']==node['spr_den']*min(st['remaining']),'SPR_MISMATCH')
    menu=node['menu']
    require(isinstance(menu,list) and len(menu)==len(set(menu)) and len(menu)>=2,'ILLEGAL_MENU')
    kinds=set()
    for a in menu:
        require(type(a) is str and re.fullmatch(r'(x|f|c|b:[1-9]\d*|r:[1-9]\d*)',a),'ILLEGAL_MENU')
        k,_,amt=a.partition(':')
        apply(k,int(amt) if amt else (st['committed'][1-st['actor']] if k=='c' else 0),st.copy()|{'remaining':st['remaining'][:],'committed':st['committed'][:]})
        kinds.add(k)
    facing=st['committed'][1-st['actor']]>st['committed'][st['actor']]
    require({'f','c'}<=kinds if facing else ('x' in kinds),'INCOMPLETE_PASSIVE_MENU')
    counts=row['counts']; n=row['n']
    require(integer(n,MIN_N) and n<=src['parsed_hand_count'],'N_GATE')
    require(isinstance(counts,dict) and set(counts)==set(menu)
            and all(integer(v) for v in counts.values()) and sum(counts.values())==n,'ACTION_COUNT_CONSERVATION')
    return json.dumps([c,row['preflop'],flop,board,prior,current,node['actor'],row['combo']],sort_keys=True)

def check_preflop(v,c,flop):
    # Full six-seat chronology, exact posted blinds and starting stacks; no ante.
    exact_dict(v,'starting_stacks actions','PREFLOP_FIELDS')
    z=v['starting_stacks']
    require(isinstance(z,list) and len(z)==6 and all(integer(k,3) for k in z),'PREFLOP_STACKS')
    require(isinstance(v['actions'],list) and v['actions'],'PREFLOP_ACTIONS')
    living=set(range(6)); due=set(living); commits=[1,2,0,0,0,0]; actor=2; raises=limps=0; last_raise=2
    for a in v['actions']:
        exact_dict(a,'actor action to','PREFLOP_ACTION_FIELDS')
        require(due and type(a['actor']) is int and a['actor']==actor and integer(a['to']),'PREFLOP_TURN_OR_CHIPS')
        code=a['action']; amount=a['to']; high=max(commits)
        if code=='f':
            require(amount==commits[actor],'PREFLOP_FOLD_CHIPS')
            living.remove(actor);due.remove(actor)
        elif code=='x':
            require(amount==high==commits[actor],'PREFLOP_CHECK_CHIPS')
            due.remove(actor)
        elif code=='c':
            require(amount==high and commits[actor]<amount<z[actor],'PREFLOP_CALL_CHIPS')
            commits[actor]=amount;due.remove(actor)
            if not raises:limps+=1
        elif code=='r':
            require(high+last_raise<=amount<z[actor],'PREFLOP_RAISE_CHIPS')
            last_raise=amount-high;commits[actor]=amount;raises+=1;due=living-{actor}
        else:
            require(False,'PREFLOP_UNSUPPORTED_ACTION')
        if due: actor=min(due,key=lambda j:(j-actor-1)%6)
    require(not due and len(living)==2,'PREFLOP_UNCLOSED_OR_NOT_HU')
    require((limps>0,raises)==FAMILIES[c['family']],'PREFLOP_FAMILY_MISMATCH')
    p=sorted(living)
    require(c['positions']==[POS[j] for j in p] and flop['pot']==sum(commits)
            and flop['remaining']==[z[j]-commits[j] for j in p],'PREFLOP_FLOP_STATE_MISMATCH')

def replay(actions,pot,remaining):
    st={'actor':0,'pot':pot,'remaining':remaining[:],'committed':[0,0],'closed_by':None,'last_raise':2,'checks':0}
    for a in actions:
        exact_dict(a,'actor action to','EXACT_ACTION_FIELDS')
        require(type(a['actor']) is int and a['actor']==st['actor'] and integer(a['to']),'ACTION_TURN_OR_CHIPS')
        apply(a['action'],a['to'],st)
    return st

def apply(k,to,st):
    require(st['closed_by'] is None,'ACTION_AFTER_TERMINAL')
    u=st['actor'];v=1-u
    ours,theirs=st['committed'][u],st['committed'][v]
    due=theirs-ours
    cap=min(ours+st['remaining'][u],theirs+st['remaining'][v])
    require(due>=0,'INTERNAL_TURN')
    if k=='x': require(not due and not to,'ILLEGAL_CHECK');st['checks']+=1
    elif k=='f': require(due>0 and not to,'ILLEGAL_FOLD');st['closed_by']='FOLD'
    elif k=='c': require(due>0 and to==theirs and due<=st['remaining'][u],'ILLEGAL_CALL');to=theirs;st['closed_by']='CALL'
    elif k=='b':
        require(not due and ours==theirs==0 and 0<to<=cap and (to>=2 or to==cap),'ILLEGAL_BET')
        st['last_raise']=to
    elif k=='r':
        require(due>0 and theirs<to<=cap and (to-theirs>=st['last_raise'] or to==cap),'ILLEGAL_RAISE')
        st['last_raise']=to-theirs
    else:require(False,'ILLEGAL_ACTION')
    if k in ('b','r','c'):
        if k=='c' and st['remaining'][u]==due:st['closed_by']='CALL'
        st['remaining'][u]-=to-ours;st['pot']+=to-ours;st['committed'][u]=to
    if st['checks']==2:st['closed_by']='XX'
    st['actor']=v

def main():
    p=argparse.ArgumentParser()
    p.add_argument('manifest',type=Path);p.add_argument('--expected-manifest-sha256',required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--allow-synthetic',action='store_true')
    a=p.parse_args()
    try:
        ans=check_manifest(a.manifest.read_bytes(),a.expected_manifest_sha256,a.source,a.allow_synthetic)
    except (ValueError,TypeError,KeyError,AttributeError,OSError) as e:
        print(json.dumps({'status':'REJECTED','reason':str(e)}));return 1
    print(json.dumps(ans));return 0
if __name__=='__main__':sys.exit(main())
