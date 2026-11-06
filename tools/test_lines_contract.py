"""Regression tests for missing-data detection, independent of solver actions."""
import unittest
from lines_contract import diff, street, NODES


class ContractTests(unittest.TestCase):
    def test_nodes_do_not_depend_on_surviving_rows(self):
        missing = diff({'rows': []})
        self.assertTrue(any(m['sp'] == 'opfr' and m['nd'] == 't_barrel' for m in missing))
        self.assertTrue(any(m['sp'] == 'iso' and m['nd'] == 'lmp_t_probe' for m in missing))

    def test_condition_is_not_satisfied_by_another_column(self):
        row = dict(sp='ipc', nd='r_vs_bet', hc=['AIR'], c={'sz': 'p75', 'ln': 'tb'})
        missing = diff({'rows': [row]})
        self.assertFalse(any(m['sp'] == 'ipc' and m['nd'] == 'r_vs_bet' and m['hc'] == 'AIR' and m['c'] == row['c'] for m in missing))
        self.assertTrue(any(m['sp'] == 'ipc' and m['nd'] == 'r_vs_bet' and m['hc'] == 'AIR' and m['c'] == {'sz': 'p75', 'ln': 'oth'} for m in missing))

    def test_existing_ui_columns_are_included(self):
        row = dict(sp='bb', nd='r_vs_bet', hc=['S'], c={'sz': 'le50', 'ct': 'pair'})
        self.assertTrue(any(m['sp'] == 'bb' and m['nd'] == 'r_vs_bet' and m['hc'] == 'AIR' and m['c'] == row['c'] for m in diff({'rows': [row]})))

    def test_mw_coarsening_excludes_insufficient_class(self):
        data = {'rows': [], 'mw_grid': {'columns': [{}], 'cells': {
            'f_bet|MID': {'actions': {'x': {'n': 61}, 'small': {'n': 15}}}}}}
        self.assertFalse(any(m['sp'] == 'mw' for m in diff(data)))

    def test_mw_eligible_cell_cannot_disappear(self):
        data = {'rows': [], 'mw_grid': {'columns': [{}], 'cells': {
            'f_bet|MID': {'actions': {'x': {'n': 61}, 'small': {'n': 40}}}}}}
        missing = [m for m in diff(data) if m['sp'] == 'mw']
        self.assertEqual(missing, [dict(sp='mw', nd='f_bet', hc='MID', c={})])

    def test_river_pool_eligible_cell_cannot_disappear(self):
        data = {'rows': [], 'mw_grid': {'method': 'river_closing_call', 'columns': [{}],
                'cells': {'r_vs_bet|MID': {'n': 40}, 'r_vs_xr|MID': {'n': 39}}}}
        missing = [m for m in diff(data) if m['sp'] == 'mw']
        self.assertEqual(missing, [dict(sp='mw', nd='r_vs_bet', hc='MID', c={})])

    def test_every_spot_has_turn_contract(self):
        for sp, nodes in NODES.items():
            self.assertTrue(any(street(nd) == 'turn' for nd in nodes), sp)


if __name__ == '__main__':
    unittest.main()
