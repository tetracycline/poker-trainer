"""Rank the current APPROX queue using actual model amounts and archived CFR reach."""
import argparse
import collections
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from hu_multiboard_promote import FAM_ROOT, hero_seat, tokenize
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope

D = Path('data')
E = D / 'solver_evidence'
Q = D / 'nl2_hu_stage2_queue.json'
CURRENT = D / 'nl2_hu_multiboard_status_current.json'
OUT = D / 'nl2_hu_b471_remaining_approx_queue.json'


def load(p):
    return json.loads(gzip.decompress(p.read_bytes()) if p.name.endswith('.gz') else p.read_bytes())


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def matches_chips(line, row):
    """Native templates use thirds. Rust encodes 33% in chips. Replay each separately."""
    root_pot, root_stack = row['root_pot_bb'], row['root_remaining_bb']
    def replay(integer):
        pot, stack = Fraction(str(root_pot))*100, Fraction(str(root_stack))*100
        for street in line.split('/'):
            paid = [0, 0]
            for index, move in enumerate(street.split()):
                seat = index % 2
                if move == 'x':
                    continue
                if move == 'c':
                    paid[seat] = max(paid)
                elif move.startswith('b'):
                    pct = int(move[1:])
                    frac = Fraction(1,3) if not integer and pct == 33 else Fraction(2,3) if not integer and pct == 66 else Fraction(pct,100)
                    amount = pot * frac
                    paid[seat] = min(stack, int(amount + Fraction(1,2)) if integer else amount)
                else:
                    return None  # A bare 'r' carries no original raise-to amount.
            stack -= max(paid)
            pot += sum(paid)
        return float(pot/100), float(stack/100)
    ideal = replay(False)
    if ideal is None:
        return None
    if abs(ideal[0]-row['approx_pot_bb']) > .005 or abs(ideal[1]-row['approx_remaining_bb']) > .005:
        return False
    return replay(True)


def model_lines(row, models):
    parts = [s.split('、') if s else [] for s in row['abstract_action_history'].split('|')]
    alternatives = [[list(tokenize(tok)) for tok in tokens] for tokens in parts]
    node = row
    while node:
        if node['source_action'] == 'bet':
            street = node['street']-1
            pos = len(parts[street])-2
            if pos < 0 or parts[street][pos] != '你下注' or parts[street][pos+1] != '對手跟':
                return {}
            action = 'b' + str(round(node['source_action_assumed_size_pot']*100))
            alternatives[street][pos] = [action]
        node = models.get(node['source_id'])
    segments = [list(' '.join(actions) for actions in itertools.product(*choices)) for choices in alternatives]
    lines = {}
    for history in itertools.product(*segments):
        line = '/'.join(history)
        chips = matches_chips(line, row)
        if chips is not False:
            lines[line] = chips
    return lines


def profiles(registry):
    source = {r['model_id']:r for r in load(Q)['records']}
    rows, lookup = {}, collections.defaultdict(list)
    for r in registry['records'].values():
        if r['label'] != 'APPROX':
            continue
        m = source[r['model_id']]
        rank = r['frequency_rank']
        pot, stack = m['approx_pot_bb'], m['approx_remaining_bb']
        spot = r['solver_profile']
        root = m['root_pot_bb'], m['root_remaining_bb']
        assert (r['abstract_action_history'], r['assumed_model_node_spr']) == (m['abstract_action_history'], m['approx_spr'])
        # All 392 model decisions are first-to-act or checked-to; no outstanding wager.
        assert m['abstract_action_history'].split('|')[-1] in ('','對手過')
        balance = round(pot + 2*stack - root[0] - 2*root[1], 6)
        if root != FAM_ROOT[spot]:
            reason, lines = 'ROOT_POT_OR_STACK_MISMATCH', {}
        elif abs(balance) > .005:
            reason, lines = 'UNMATCHED_CHIPS_AT_MODEL_DECISION', {}
        else:
            lines = model_lines(m, source)
            reason = ('REQUIRES_ORIGINAL_RAISE_TO_AMOUNT' if lines and all(v is None for v in lines.values()) else
                      'COMPATIBLE_BET_SEQUENCE' if lines else 'NO_CHIP_MATCH_FOR_LISTED_SIZES')
        for line, amounts in lines.items():
            lookup[(spot,r['family'],m['street'],hero_seat(m['preflop_text']),line)].append((rank,amounts,pot,stack))
        rows[rank] = dict(rank=rank, model_id=m['model_id'], spot=spot, hero_seat=hero_seat(m['preflop_text']),
                          frequency_proxy=r['estimated_nl2_occurrence_opportunity_frac'], root_bb=root,
                          model_pot_bb=pot, model_effective_stack_bb=stack, balance_error_bb=balance,
                          geometry=reason, possible_exact_lines=sorted(lines))
    return rows, lookup


def inspect_sources(lookup):
    # Keying all candidates by *exact* board, line and spot prevents pairing unrelated runs.
    candidates = collections.defaultdict(dict)
    count = collections.Counter()
    def record(spot,family,flop,ver,run,sha,node,path,exact=False):
        if not run or len(sha or '') != 64:
            return
        board, line, seat, pot, stack, strict = node
        if strict <= 0 or ver not in ('gto','exp_oop' if seat==0 else 'exp_ip'):
            return
        for rank, amounts, expected_p, expected_s in lookup.get((spot,family,len(board)//2-3,seat,line),()):
            if amounts is None:
                # Exact size for an original raise requires an independent raise-to replay.
                continue
            if abs(pot-amounts[0])>.011 or abs(stack-amounts[1])>.011:
                continue
            key = (rank,flop,board,line)
            proof = dict(run=run, sha256=sha, archive=path.name, positive_combos=strict, two_seat_raw=exact)
            existing = candidates[key].get(ver)
            if existing is None or (exact and not existing['two_seat_raw']):
                candidates[key][ver] = proof

    overlays = {}
    for p in sorted(D.glob('nl2_hu_sequential_reach_official_b*.json.gz')):
        overlays.update(load(p)['subgames_by_source_sha256'])
    for p in [D/name for name in ('nl2_hu_exact_boards.json.gz','nl2_hu_exact_boards_b04.json.gz','nl2_hu_exact_boards_b05.json.gz')]:
        for c in load(p)['subgames']:
            count['official_cases'] += 1
            if c['gto_gap_pct'] > .5 or (c['version'] != 'gto' and (c['hero_gap_pct'] is None or c['hero_gap_pct'] > .5)):
                continue
            seq = overlays.get(c['source_sha256'],{}).get('nodes',{})
            for n in c['nodes']:
                board,line,seat = n['board'],n['line'],n['acting_seat']
                strict = seq.get('|'.join((board,line,str(seat))),{}).get('count',0)
                record(c['spot'],c['pot_family'],c['flop'],c['version'],c['source_run_id'],c['source_sha256'],
                       (board,line,seat,n['pot_units']/100,n['remaining_stack_units']/100,strict),p)
    for p in sorted(E.glob('NL2_MULTIBOARD_*.json.gz')):
        d = load(p)
        if d.get('schema') != 'NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1' or d.get('errors'):
            continue
        count['compact_archives'] += 1
        for art in d['artifacts']:
            for c in art['cases']:
                v = c['version']
                if c['gto_exploitability_pct']>.5 or (v!='gto' and (c['locked_hero_gap_pct'] is None or c['locked_hero_gap_pct']>.5)):
                    continue
                for n in c['nodes']:
                    record(c['spot'],c['pot_family'],c['flop'],v,d['source_run_id'],c['source_sha256'],
                           (n['public_board'],n['exact_node_line'],n['acting_seat'],n['pot_bb'],n['remaining_bb'],n['strictly_reachable_combos']),p)
    return candidates,count,record


def raw_cases():
    """Only durable paired source archives with independent proof/registry pins are admitted."""
    for filename, key in (('nl2_hu_multiboard_status_v51_b453_rank32.json','B453_rank32_three_true_original_GTO_NL2_OOP_flops'),
                          ('nl2_hu_multiboard_status_v52_b463_rank45.json','B463_rank45_three_true_original_GTO_NL2_OOP_flops')):
        path = D/filename
        if not path.exists():
            continue
        for pin in load(path)[key]['pins']:
            path = E/f"NL2_{pin['archive_code']}.json.gz"
            pack = load(path)
            for src in pack['source_arrays']:
                version = src['version']
                sha = pin['original_GTO_SHA256' if version=='gto' else 'actual_NL2_SHA256']
                assert src['source_sha256'] == sha and len(sha)==64
                yield path, src['manifest'], src['root'], src['subgame'], pack['run_id'], sha
    legacy = E/'NL2_B443_R27_R29_AS9H2D_EXP_OOP_TURN_ONLY.json.gz'
    pin = load(D/'nl2_hu_b443_as9h2d_exp_oop_partial_source_proof.json')
    archive = load(legacy)
    for v, sha, run in [('gto',pin['GTO_turn_sha256'],pin['gto_parent_run_id']),('exp',pin['EXP_OOP_turn_sha256'],pin['run_id'])]:
        yield legacy, archive[v+'_manifest'], archive[v+'_root'], archive[v+'_turn'], run, sha
    core = E/'NL2_B460_R48_BTN_BB_9S6H3D_B75.json.gz'
    idx = load(core.with_name(core.name.replace('.json.gz','.index.json')))
    pairs = [(core, idx['run_id'], idx['raw_archive_sha256'])]
    for path in sorted((E/'b466').glob('*.proof.json')):
        meta = load(path)
        archive = path.parent / meta['archive']
        if archive.is_file() and archive.name != core.name:
            pairs.append((archive, meta['run_id'], meta['archive_sha256']))
    for path, run, sha in pairs:
        assert sha == digest(path)
        obj = load(path)
        for v in ('gto','exp_oop'):
            src = obj[v]
            yield path, src['manifest'], src['flop_root'], src['turn_subgame'], run, src['subgame_sha256']


def inspect_raw(lookup, record, counts):
    for path, m, root, sub, run, sha in raw_cases():
        v = m['version']
        assert (m['root_pot_bb'],m['root_remaining_bb']) == FAM_ROOT[m['spot']]
        assert (m['flop'],sub['flop']) == (root['flop'],root['flop'])
        assert hashlib.sha256(json.dumps(sub,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() == sha
        assert m['cases'] and sha in {c['source_sha256'] for c in m['cases']}
        assert 0 <= sub['info']['gto_expl_pct'] <= .5
        if v!='gto':
            assert 0 <= sub['info']['hero_gap_pct'] <= .5 and m['locks']
            if not lock_scope(sub,m['locks'],v)['observed_marginal_source_nodes']:
                continue
        counts['paired_raw_version_cases'] += 1
        masks = game_reach(root,sub)[0]
        for n in sub['nodes']:
            board,line,seat = n['board'],n['line'],n['player']
            if (m['spot'],m['pot_family'],len(board)//2-3,seat,line) not in lookup:
                continue
            key='|'.join((board,line,str(seat)))
            actual=compatible_node_reach(root,sub,n,masks[key])
            record(m['spot'],m['pot_family'],m['flop'],v,run,sha,
                   (board,line,seat,n['pot']/100,(sub['stack']-max(n['bets']))/100,actual['count']),path,exact=True)


def build(source):
    registry=load(source)
    rows,lookup=profiles(registry)
    candidates,counts,record=inspect_sources(lookup)
    inspect_raw(lookup,record,counts)
    previous = D/'nl2_hu_b465_rank218_four_board_gate.json'
    if 218 in rows and previous.is_file():
        checkpoint = load(previous)
        for b,p in zip(checkpoint['boards'],checkpoint['pins']):
            assert p['flop']==b['flop'] and p['public_board']==b['public_board']
            for version,run,dig in [('gto','original_GTO_run','original_GTO_SHA256'),('exp_ip','actual_NL2_IP_run','actual_NL2_SHA256')]:
                joint=p['compatible_reach'][version]
                assert joint['compatible_hole_card_pairs']>0
                record('CO_BB','SRP',b['flop'],version,p[run],p[dig],(b['public_board'],checkpoint['line'],1,
                       b['actual_pot_bb'],b['actual_effective_stack_bb'],joint['count']),previous,exact=True)
    prior=load(D/'nl2_hu_b471_rank146_original_pairs.json')
    if 146 in rows:
        assert prior['model_id']==rows[146]['model_id']
        for b,p in zip(prior['boards'],prior['pins']):
            assert p['GTO_compatible_hole_card_pairs']>0 and p['NL2_compatible_hole_card_pairs']>0
            gto=E/f"NL2_MULTIBOARD_{p['viewer_archive_code']}.json.gz"
            exp=E/f"NL2_MULTIBOARD_{p['locked_viewer_archive_code']}.json.gz"
            assert digest(gto)==p['viewer_sha256'] and digest(exp)==p['locked_viewer_sha256']
            for ver,path,count,run,sha in [
                    ('gto',gto,p['GTO_strict_combos'],b['source_run_id'],p['original_GTO_SHA256']),
                    ('exp_oop',exp,p['NL2_strict_combos'],p['locked_source_run_id'],p['actual_NL2_SHA256'])]:
                record('UTG_CO','SRP',b['flop'],ver,run,sha,(b['public_board'],prior['line'],0,
                       b['actual_pot_bb'],b['actual_effective_stack_bb'],count),path,exact=True)
    pairs=collections.defaultdict(dict)
    for (rank,flop,board,line), versions in sorted(candidates.items()):
        expected = 'exp_ip' if rows[rank]['hero_seat'] else 'exp_oop'
        if 'gto' not in versions or expected not in versions:
            continue
        independent = all(versions[v]['two_seat_raw'] for v in ('gto',expected))
        sample = dict(public_board=board,line=line,raw_two_seat_replayed=independent,
                      gto=versions['gto'],nl2=versions[expected])
        previous=pairs[rank].get(flop)
        if previous is None or independent and not previous['raw_two_seat_replayed']:
            pairs[rank][flop]=sample
    for rank,r in rows.items():
        r['observed_distinct_flops']=pairs[rank]
        r['raw_joint_flops']=[k for k,v in pairs[rank].items() if v['raw_two_seat_replayed']]
        r['compact_only_flops']=[k for k,v in pairs[rank].items() if not v['raw_two_seat_replayed']]
        r['additional_distinct_raw_pairs_needed']=max(0,3-len(r['raw_joint_flops']))
    ordered=sorted(rows.values(),key=lambda r:(r['additional_distinct_raw_pairs_needed'],
                   -r['frequency_proxy'],r['rank']))
    assert len(ordered)==registry['APPROX']
    return dict(schema='NL2_HU_B471_APPROX_EXACT_GEOMETRY_QUEUE_V1', registry=source.name,
                registry_sha256=digest(source), model_queue_sha256=digest(Q), coverage=dict(counts),
                CERT_MULTIBOARD=registry['CERT_MULTIBOARD'],APPROX=len(ordered),
                one_distinct_raw_source_flop_short=[r['rank'] for r in ordered if len(r['raw_joint_flops'])==2],
                one_if_compact_sources_reauthenticate=[r['rank'] for r in ordered if len(r['observed_distinct_flops'])==2
                                                       and len(r['raw_joint_flops'])<2],
                provenance='Compact hits require replay of original private ranges for both seats and measured lock sources. Raw pairs are restricted to archived jointly reachable holdings.',
                model_geometry='Both seats have matched contributions at these model decisions. Replay preserves the actual starting pot and stack and each explicit modeled bet size. Bare raises require their original raise-to amount.',
                rows=ordered)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',type=Path,default=CURRENT)
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    data=build(args.registry)
    args.out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(data['APPROX'], 'APPROX;', 'one raw flop short:',data['one_distinct_raw_source_flop_short'],
          'one conditional on compact reauthentication:',data['one_if_compact_sources_reauthenticate'])
