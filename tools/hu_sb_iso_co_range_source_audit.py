"""Compare the seat-specific SB isolation source, NL2 observations and trainer prices for ranks 122 and 123."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from hu_b467_river_source_gate import json_bytes

SOLVER='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
PINS={
    'inputs/pool_stats.json':'c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a',
    'exploit_v2/data/pool_ranges.json':'7d0eea0d8443c2cacb9ab0cfdbc9799918211f916773dd8dbb2ae4ad18486727',
    'exploit_v2/parse_pool.py':'c95b92a30af08e5b51fcdc207a0bb98537ff987a3a06aa34c016507400577eab',
    'exploit_v3/data/iso_ranges.json':'759035ccec130a8296152aa1fbfc4a8b35cc5eef9e067e2a6519d1b46a1434c8',
    'exploit_v3/iso.py':'30307c7838f5265c965c71f618bff3faa2b3eb69a4a18f68fe0cf149eba18033',
    'preflop/pfsolve.py':'d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100',
    'preflop/gto_rake.json':'e73f1eb9fef6aabdbf565804a0e1a68610656b30cf0e3d273a432acfee110969',
}
B716=Path('data/nl2_hu_b716_iso_role_prices.json')

def audit(solver):
    head=subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()
    assert head==SOLVER
    raw={p:(solver/p).read_bytes() for p in PINS}
    assert {p:sha256(b).hexdigest() for p,b in raw.items()}==PINS
    current=json.loads(subprocess.check_output(['node','tools/hu_b716_iso_role_prices.cjs']))
    assert current==json.loads(B716.read_bytes())
    groups=current['affected_approx_ranks']
    assert current['target_ranks']==[122,123] and len(groups)==11 and not current['affected_certified_ranks']
    assert current['existing_stage2_locked_iso_profiles']==['ISO_BTN_CO']
    chart=json.loads(raw['exploit_v3/data/iso_ranges.json'])['CO>SB']
    assert (chart['size'],chart['iso_pct'],chart['limper_call'])==(5.0,25.2,.705)
    iso_source=raw['exploit_v3/iso.py'].decode()
    assert all(token in iso_source for token in ('def resp_alloc(','idx = np.argsort(-STR)','if size is None: size = (5.0','n_iso >= 7'))
    pool=json.loads(raw['inputs/pool_stats.json'])['NL2']
    sb=pool['preflop']['SB'];co=pool['preflop']['CO']
    assert (sb['iso'],sb['iso_opp'])==(17.8,246125)
    assert co['limp_vs_raise']=={'n':42988,'fold':25.9,'call':70.5,'raise':3.6}
    assert pool['preflop_showdown_hands']['limp_call']['n']==45658
    assert not any('iso' in k.lower() for k in pool['preflop_showdown_hands'])
    class_pool=json.loads(raw['exploit_v2/data/pool_ranges.json'])
    opening=class_pool['rfi']['CO']
    assert (len(opening['f_limp']),opening['n_sd_limp'])==(169,2574)
    assert set(class_pool)=={'names','meta','rfi','vs_open','prop','prop_raw','player_types'}
    assert 'and not limpers' in raw['exploit_v2/parse_pool.py'].decode()
    gto_nodes=json.loads(raw['preflop/gto_rake.json'])['nodes']
    assert gto_nodes and not any('limp' in name.lower() for name in gto_nodes)
    assert 'no limp branch' in raw['preflop/pfsolve.py'].decode()
    in_scope=current['alternative_root_scenarios'];five=in_scope['preflop_chart_5bb_100bb_start']
    assert five['root_pot_bb']==11 and five['root_stack_bb']==95
    model_spr={'122':5.083,'123':6.2}
    projected={rank:node['integer_percent_turn_spr'] for rank,node in five['native_integer_percent_branch_projections'].items()}
    differences={rank:round(100*abs(projected[rank]/model_spr[rank]-1),6) for rank in model_spr}
    assert all(err>5 for err in differences.values())
    return dict(schema='NL2_HU_SB_ISOLATOR_CO_CALLER_PREFLOP_SOURCE_AUDIT_V1',ranks=[122,123],all_same_ingress_approx_ranks=groups,
      roles=dict(oop='SB isolator',ip='CO limp/caller'),solver_head=SOLVER,solver_source_sha256=PINS,
      trainer_source_sha256=sha256(B716.read_bytes()).hexdigest(),
      observed=dict(SB_iso_pct_all_limp_opportunities=sb['iso'],SB_iso_opportunities=sb['iso_opp'],
        CO_limp_vs_all_raises=co['limp_vs_raise'],all_position_limp_call_showdowns_grouped_by_hand_family=45658,
        CO_open_limp_showdowns=opening['n_sd_limp'],CO_open_limp_estimated_hand_classes=len(opening['f_limp'])),
      available_conditional_chart=dict(key='CO>SB',iso_to_bb=chart['size'],modeled_iso_pct=chart['iso_pct'],
        action_class_counts=dict(Counter(chart['act'].values())),CO_limp_call_hand_assignment='strength-ranked allocation of pooled CO responses',
        source='exploit_v3/iso.py',scenario_sweep=9,per_hand_frequencies_observed=False),
      prices=in_scope,registry_spr=model_spr,chart_5bb_spr_relative_error_pct=differences,
      supported_postflop_iso_profiles=current['existing_stage2_locked_iso_profiles'],
      missing_inputs=['SB isolation range conditional on one CO limp at the displayed four-blind size',
        'CO call range conditional on that SB isolation size','one agreed pot and effective stack for the matched source'],
      eligible_native_source_boards=0,new_native_solves=0,actor_locked_public_boards=0,half_pot_assessed=0,
      disposition='Retain APPROX. The verified five-blind conditional chart, pooled observations and BTN-isolator sources do not supply the two displayed-price ranges.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--solver',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_bytes(json_bytes(audit(a.solver)))
