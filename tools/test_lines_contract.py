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

    def test_mw_all_cells_required_even_with_empty_audit(self):
        missing = [m for m in diff({'rows': [], 'mw_grid': {'columns': [{}], 'cells': {}}}) if m['sp'] == 'mw']
        self.assertEqual(len(missing), 9 * 7 * 2)
        self.assertEqual({m['nd'] for m in missing}, set(NODES['mw']))

    def test_mw_missing_cell_is_not_waived_by_low_pool_n(self):
        row = dict(sp='mw', nd='t_vs_xr', hc=['AIR'], c={'hr':'CALL'})
        data = {'rows': [row], 'mw_grid': {'cells': {'t_vs_xr|AIR': {'n': 0}}}}
        missing = [m for m in diff(data) if m['sp'] == 'mw']
        self.assertEqual(len(missing), 125)
        self.assertFalse(any(m['nd'] == 't_vs_xr' and m['hc'] == 'AIR' and m['c']=={'hr':'CALL'} for m in missing))

    def test_mw_caller_cannot_cover_opener(self):
        row = dict(sp='mw', nd='f_bet', hc=['S'], c={'hr':'CALL'})
        missing = diff({'rows':[row]})
        self.assertTrue(any(m['sp']=='mw' and m['nd']=='f_bet' and m['hc']=='S' and m['c']=={'hr':'PFR'} for m in missing))

    def test_mw_sanity_rejects_inverted_strength_and_folds(self):
        from mw_sanity import check
        rows = [dict(sp='mw',nd='f_vs_bet',hc=[c],c={'hr':'PFR'},solver={'freq':f}) for c,f in {
            'S':{'r':.1,'c':.9},'MID':{'r':.2,'f':.8},
            'WDRAW':{'r':.3,'f':.7},'AIR':{'r':.4,'f':.6}}.items()]
        issues,_=check({'rows':rows})
        self.assertEqual(len(issues),2)

    def test_mw_ip_caller_strength_gate_is_required(self):
        from mw_sanity import check
        rows = [dict(sp='mw',nd='f_bet',hc=[c],c={'hr':'CALL'},solver={'freq':{'small':p,'x':1-p},'samples':[{'player':0}]})
                for c,p in [('S',.2),('MID',.1),('WDRAW',.4),('AIR',.1)]]
        self.assertEqual(check({'rows':rows})[0],[])
        for r in rows:r['solver']['samples'][0]['player']=1
        self.assertEqual(len(check({'rows':rows})[0]),1)

    def test_every_spot_has_turn_contract(self):
        for sp, nodes in NODES.items():
            self.assertTrue(any(street(nd) == 'turn' for nd in nodes), sp)


if __name__ == '__main__':
    unittest.main()
