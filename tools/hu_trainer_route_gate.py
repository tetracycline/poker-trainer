"""Admit original CFR boards only on the trainer's rendered actor and exact priced action ancestry."""
import argparse
import json
from pathlib import Path
import re
import subprocess

SCHEMA = "NL2_HU_RENDERED_ACTION_ROUTES_V1"
REASON = "FEWER_THAN_THREE_FLOPS_AFTER_RENDERED_ACTION_ROUTE_CHECK"


def rendered_contract(records, inspect=()):
    out = subprocess.run(["node", "tools/hu_trainer_route_contract.cjs", *inspect], input=json.dumps(list(records)),
                         text=True, stdout=subprocess.PIPE, check=True)
    contract = json.loads(out.stdout)
    assert contract["schema"] == SCHEMA and set(contract["routes"]) == set(records)
    return contract


def three_suited_turn(public):
    suits = public[1:8:2]
    return len(suits) == 4 and any(suits.count(suit) >= 3 for suit in 'cdhs')


def street_texture(public):
    ranks = public[::2]
    if any(public[1::2].count(suit) >= 3 for suit in 'cdhs'):
        return 'mono'
    if len(set(ranks)) < len(ranks):
        return 'paired'
    if 'A' in ranks:
        return 'A_high'
    if any(r in ranks for r in 'KQ'):
        return 'KQ_high'
    return 'mid_high' if any(r in ranks for r in 'JT') else 'low'


def missing_visible_rows(route, board):
    failures = []
    for step in route.get('visible_street_rows', []):
        public = board['public_board'][:4 + step['street'] * 2]
        texture = street_texture(public)
        if texture not in step['visible']:
            failures.append(dict(street=step['street'], public=public, texture=texture,
                                 from_section=step['from'], target=step.get('to'), eligible_rows=sorted(step['visible'])))
    return failures


def reviewed_row_failures(route, board):
    identity = (board['public_board'], board['actual_exact_action_line'], board['acting_seat'],
                board.get('source_run_id'), board.get('source_sha256'))
    for pin in route.get('reviewed_partial_sources', []):
        if identity == (pin['public_board'], pin['line'], pin['seat'], pin['run'], pin['gto_sha256']):
            return missing_visible_rows(route, board)
    return []


def compatible(route, board):
    if reviewed_row_failures(route, board):
        return False
    if route.get('requires_three_suited_turn') and not three_suited_turn(board['public_board']):
        return False
    expected = [street.split() for street in route["streets"]]
    actual = [street.split() for street in board["actual_exact_action_line"].split("/")]
    if route["seat"] != board["acting_seat"] or len(expected) != len(actual):
        return False
    for required, played in zip(expected, actual, strict=True):
        if len(required) != len(played):
            return False
        for target, token in zip(required, played, strict=True):
            if target == "bet":
                ok = re.fullmatch(r"b[1-9][0-9]*", token) is not None or token == "a"
            elif target == "overbet":
                ok = token == "a" or (re.fullmatch(r"b[0-9]+", token) is not None and int(token[1:]) > 100)
            elif target == "raise":
                ok = re.fullmatch(r"r[0-9]*", token) is not None or token == "a"
            else:
                ok = target == token
            if not ok:
                return False
    return True


def active_boards(model):
    if model["label"] == "CERT-MULTIBOARD":
        return model["certified_3_to_5_exact_flop_boards"]
    return model.get("remaining_exact_board_evidence", [])


def apply_routes(records, contract, exclusions):
    changed = []
    for mid, model in records.items():
        route = contract["routes"][mid]
        valid = []
        before = active_boards(model)
        for b in before:
            if compatible(route, b):
                valid.append(b)
            else:
                key = (mid, b["public_board"], b["actual_exact_action_line"], b["acting_seat"], b["source_run_id"], b["source_sha256"])
                exclusions[key] = dict(model_id=mid, public_board=b["public_board"], actual_line=b["actual_exact_action_line"],
                    acting_seat=b["acting_seat"], run=b["source_run_id"], sha256=b["source_sha256"])
                failures = reviewed_row_failures(route, b)
                if failures:
                    exclusions[key].update(reason='NO_RENDERED_CELL_ON_ACTUAL_STREET', missing_rows=failures,
                                           retained_locked_sources=[lock['sha256'] for lock in b['nl2_locked_variants']])
        if len(valid) == len(before):
            continue
        changed.append(mid)
        assert len({b["flop"] for b in valid}) == len(valid)
        model["proven_exact_board_count"] = len(valid)
        if len(valid) >= 3:
            model["certified_3_to_5_exact_flop_boards"] = valid
        else:
            model.update(label="APPROX", blocked_reason=REASON, remaining_exact_board_evidence=valid,
                         certified_3_to_5_exact_flop_boards=[])
    return changed


def active_pins(model, pins):
    keys = {(b["flop"], b["public_board"], b["source_run_id"], b["source_sha256"]) for b in active_boards(model)}
    return [p for p in pins if (p["flop"], p["public_board"], p["source_run_id"], p["original_GTO_SHA256"]) in keys]


def audit_file(path):
    data = json.loads(path.read_bytes())
    if data["schema"] != "NL2_HU_392_MULTIBOARD_CERT_STATUS_VERIFIED_EXTENSIONS_V1":
        return
    manifest = json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())
    current = rendered_contract(data["records"])
    assert data["trainer_route_contract_schema"] == current["schema"]
    assert manifest["trainer_route_contract"] == current
    for mid, m in data["records"].items():
        assert all(compatible(current["routes"][mid], b) for b in active_boards(m)), mid


    historical = json.loads(Path('data/nl2_hu_multiboard_status_v53_b465_rank218.json').read_bytes())['records']
    for mid, route in current['routes'].items():
        for pin in route.get('reviewed_partial_sources', []):
            original, = (b for b in active_boards(historical[mid]) if b['source_sha256'] == pin['gto_sha256'])
            assert set(pin['locked_sha256']) == {v['sha256'] for v in original['nl2_locked_variants']}
            failures = reviewed_row_failures(route, original)
            if failures:
                assert original['source_sha256'] not in {b['source_sha256'] for b in active_boards(data['records'][mid])}
                recorded, = (row for row in manifest['trainer_route_exclusions']
                             if row['model_id'] == mid and row['sha256'] == pin['gto_sha256'])
                assert recorded['missing_rows'] == failures and set(recorded['retained_locked_sources']) == set(pin['locked_sha256'])


def inspect_partials(path):
    records = json.loads(path.read_bytes())['records']
    reviewed = {mid: m for mid, m in records.items() if m['label'] == 'APPROX' and
                len({b['flop'] for b in active_boards(m)}) == 2}
    routes = rendered_contract(records, reviewed)['routes']
    for mid, model in sorted(reviewed.items(), key=lambda kv:kv[1]['frequency_rank']):
        observations = []
        for board in active_boards(model):
            failures = missing_visible_rows(routes[mid], board)
            observations.append(dict(flop=board['flop'], public=board['public_board'], missing_rows=failures,
                status='INCOMPATIBLE_RENDERED_ROW' if failures else 'ROW_PRESENT_VERIFY_NATIVE_HANDS'))
        print(json.dumps(dict(rank=model['frequency_rank'],model_id=mid,boards=observations),ensure_ascii=False))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("registry", type=Path)
    cli.add_argument('--inspect-partials', action='store_true', help='Diagnose two-flop registry partials against live rows')
    args = cli.parse_args()
    if args.inspect_partials:
        inspect_partials(args.registry)
    else:
        audit_file(args.registry)
