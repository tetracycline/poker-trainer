#!/usr/bin/env python3
"""Conservative 392-model to genuine 100bb action-lineage/source screening.

This is a research aid, NOT a CERT/EST promotion. Model nodes have no frozen
board cards; even an identical family, abstract actions and near SPR cannot
establish per-board, per-combo GTO strategy.
"""
import argparse, collections, itertools, json, pathlib

BET_SIZES=('b33','b50','b75')
VERBS={'過':('x',),'跟':('c',),'加注':('r',),
       '全下':('a',),'加注全下':('a',),
       '下注':BET_SIZES,'超池下注':('b150',)}

def abstractions(text):
    tokens=[]
    for unit in text.split('、'):
        unit=unit.strip()
        if unit.startswith('對手'):unit=unit[2:]
        elif unit.startswith('你'):unit=unit[1:]
        if not unit:continue
        if unit not in VERBS:return ()
        tokens.append(VERBS[unit])
    if not tokens or len(tokens)>8:return ()
    return tuple(' '.join(row) for row in itertools.product(*tokens))

def normalized_example(case,node,model,street):
    node_spr=float(case['turn_spr']) if street==1 else float(node['node_spr'])
    denom=max(1.,abs(node_spr))
    discrepancy=abs(node_spr-float(model['approx_spr']))/denom
    return dict(source_run_id=case['source_run_id'],
       source_sha256=case['source_sha256'],spot=case['spot'],
       family=case['pot_family'],version='gto',
       flop=case['flop'],turn=case['turn'],
       actual_public_board=(case['flop']+case['turn']) if street==1 else node['board'],
       exact_flop_actions=case['flop_line'],
       exact_solver_node_line=case['flop_line']+'/' if street==1 else node['line'],
       actual_node_spr=round(node_spr,6),
       model_assumed_node_spr=model['approx_spr'],
       relative_spr_difference=round(discrepancy,6),
       reached_combos=(node['reachable_combos'] if node else None),
       board_exact_match_to_model=False, # model is texture-only, not cards.
       available_for='EXACT_SOURCE_EXAMPLE_ONLY_NOT_GENERIC_CERT')

def build(q,solver):
    index=collections.defaultdict(list)
    for x in solver['subgames']:
        if x['status']!='CERT_EXACT_BOARD_GTO' or x['version']!='gto':continue
        index[x['spot'],x['pot_family'],x['flop_line']].append(x)
    records={};tot=collections.Counter()
    for m in q['records']:
        seg=m['abstract_action_history'].split('|')
        flop_variants=abstractions(seg[0])
        sources=[x for line in flop_variants
                 for x in index.get((m['solver_profile'],m['family'],line),())]
        candidates=[]
        if m['street']==1:
            for c in sources:
                root=next((n for n in c['nodes'] if n['line']==c['flop_line']+'/' and n['reachable_combos']>0),None)
                if root:candidates.append(normalized_example(c,root,m,1))
        elif m['street']==2:
            turn_variants=abstractions(seg[1]) if len(seg)>1 else ()
            for c in sources:
                for turn in turn_variants:
                    line=c['flop_line']+'/'+turn+'/'
                    # Exact river roots only, after public river has actually been dealt.
                    for n in c['nodes']:
                        if n['line']==line and len(n['board'])==10 and n['reachable_combos']>0:
                            candidates.append(normalized_example(c,n,m,2))
        else:
            raise ValueError('Unknown model street')
        unique={}
        for x in candidates:unique[(x['source_sha256'],x['exact_solver_node_line'],x['actual_public_board'])]=x
        ordered=sorted(unique.values(),key=lambda x:(x['relative_spr_difference'],x['source_run_id']))
        matches=[x for x in ordered if x['relative_spr_difference']<=0.01]
        if matches:status='MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY'
        elif ordered:status='MATCHED_ABSTRACT_HISTORY_BUT_NOT_SPR'
        else:status='NO_MATCHING_EXACT_BOARD_SOURCE_LINE'
        # A MODEL with unknown actual turn and river cannot be CERT or EST.
        rec=dict(model_id=m['model_id'],family=m['family'],spot=m['spot'],
            source_profile=m['solver_profile'],street=m['street'],
            abstract_history=m['abstract_action_history'],
            generic_model_status='MODEL_UNCERTIFIED',
            source_line_match_count=len(ordered),
            same_history_within_1pct_spr_count=len(matches),
            candidate_status=status,
            best_exact_board_examples=ordered[:5],
            blockers=['MODEL_HAS_NO_FROZEN_PUBLIC_FLOP_TURN_RIVER',
                'GTO_COMBO_REACH_UNKNOWN_FOR_GENERIC_BOARD',
                'ABSTRACT_BET_SIZES_NOT_EXACT_ACTION_SIZES',
                'SOURCE_PROVES_ONLY_ITS_OWN_PUBLIC_BOARD'],
            upgraded_to_cert=False,upgraded_to_est=False)
        records[m['model_id']]=rec
        tot[status]+=1
        tot[m['family']+':'+status]+=1
    if len(records)!=392:raise ValueError('Expected 392 unique generic models')
    assert all(not x['upgraded_to_cert'] and not x['upgraded_to_est'] for x in records.values())
    return dict(schema='NL2_MODEL_TO_CFR_LINEAGE_SCREEN_V1',
        model_nodes=len(records),generic_CERT=0,generic_EST=0,
        exact_source_subgames=solver['exact_subgame_count'],
        strict_spot_family_and_street_required=True,
        relative_spr_tolerance_for_research_candidate=0.01,
        warning='History/SRP/SPR similarity alone is never a CERT or EST. Every source example is an EXACT BOARD ONLY.',
        summary=dict(tot),records=records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--queue',required=True,type=pathlib.Path)
    p.add_argument('--source',required=True,type=pathlib.Path)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    d=build(json.loads(a.queue.read_text()),json.loads(a.source.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'models':d['model_nodes'],'status':d['summary'],
                      'CERT':d['generic_CERT'],'EST':d['generic_EST']},ensure_ascii=False))
if __name__=='__main__':main()
