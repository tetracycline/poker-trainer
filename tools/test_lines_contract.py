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


class SemanticTests(unittest.TestCase):
    def fixture(self):
        return dict(node_labels={'iso':{'lmp_t_delay':'轉牌：你有位置，對手先行動；延遲搶池 (stab)'}}, rows=[dict(id='test',sp='iso',nd='lmp_t_delay',eg=[dict(t='LMP',me='CO',pa=None,pc=['BB','CO'])])])

    def test_pot_type_and_first_actor_mutations(self):
        from lines_contract import semantic_errors
        d=self.fixture()
        self.assertEqual(semantic_errors(d),[])
        d['rows'][0]['eg'][0]['t']='ISO'
        self.assertTrue(any('pot type' in e for e in semantic_errors(d)))
        d=self.fixture();d['rows'][0]['eg'][0]['me']='BB'
        self.assertTrue(any('first actor' in e for e in semantic_errors(d)))

    def test_role_and_invalid_text_mutations(self):
        from lines_contract import semantic_errors
        d=self.fixture();r=d['rows'][0];r.update(sp='ipfr',nd='t_delay',why='NaN undefined')
        d['node_labels']={'ipfr':{'t_delay':'轉牌：你有位置，對手先行動'}}
        self.assertTrue(any('role' in e for e in semantic_errors(d)))
        self.assertTrue(any('rendered text' in e for e in semantic_errors(d)))

    def test_strategy_source_and_iso_namespace_mutations(self):
        from lines_contract import semantic_errors
        d=self.fixture();r=d['rows'][0]
        r['solver']={'samples':[{'path':'iso_source.json','player':1}]}
        self.assertTrue(any('strategy source' in e for e in semantic_errors(d)))
        r.update(nd='iso_t_delay');d['node_labels']={'iso':{'iso_t_delay':'轉牌：你有位置，對手先行動'}}
        self.assertTrue(any('ISO namespace' in e for e in semantic_errors(d)))

    def test_mixed_nodes_have_independently_aggregated_strategies(self):
        import json
        from pathlib import Path
        d=json.loads((Path(__file__).resolve().parents[1]/'lines_data.js').read_text().split('window.NLL=',1)[1].rstrip(';\n'))
        for base in ('t_delay','t_first','t_vs_3b'):
            groups={t:[r for r in d['rows'] if r['nd']==t+'_'+base] for t in ('iso','lmp')}
            self.assertTrue(all(groups.values()),base)
            common=set(r['hc'][0] for r in groups['iso']) & set(r['hc'][0] for r in groups['lmp'])
            self.assertTrue(any(next(r for r in groups['iso'] if r['hc'][0]==h)['solver']['freq'] != next(r for r in groups['lmp'] if r['hc'][0]==h)['solver']['freq'] for h in common),base)

    def test_multiway_oop_does_not_imply_first_actor(self):
        from lines_contract import semantic_errors
        d=dict(node_labels={'mw':{'t_vs_xr':'轉牌：你沒位置先行動'}},rows=[dict(sp='mw',nd='t_vs_xr',eg=[dict(t='SRP',me='CO',pa='CO',pc=['BB','BTN'],l='BB:x CO:b0.5 BTN:c/BB:x CO:b0.5 BTN:r3')])])
        self.assertTrue(any('first actor' in e for e in semantic_errors(d)))

    def test_generated_publication(self):
        import json
        from pathlib import Path
        from lines_contract import semantic_errors
        s=(Path(__file__).resolve().parents[1]/'lines_data.js').read_text()
        d=json.loads(s.split('window.NLL=',1)[1].rstrip(';\n'))
        self.assertEqual(semantic_errors(d),[])


if __name__ == '__main__':
    unittest.main()
