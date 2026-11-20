import copy
import json
import unittest
from pathlib import Path
from validate import check_manifest, digest_bytes

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source.synthetic.txt'
FIX=json.loads((HERE/'manifest.synthetic.json').read_bytes())

class Intake(unittest.TestCase):
    def check(self, change=lambda x:None, allow=True, wrong_sha=False):
        x=copy.deepcopy(FIX)
        change(x)
        b=json.dumps(x).encode()
        return check_manifest(b,'0'*64 if wrong_sha else digest_bytes(b),SOURCE,allow)
    def reject(self, code, change=lambda x:None, **kwargs):
        with self.assertRaisesRegex(ValueError,code):
            self.check(change,**kwargs)
    def test_synthetic_pass_is_never_empirical(self):
        self.assertEqual(self.check()['status'],'SYNTHETIC_TEST_ONLY')
        self.reject('SYNTHETIC_NOT_EMPIRICAL',allow=False)
    def test_expected_manifest_sha(self):
        self.reject('MANIFEST_SHA_MISMATCH',wrong_sha=True)
    def test_corpus_sha(self):
        self.reject('SOURCE_SHA_MISMATCH',lambda x:x['source'].update(sha256='0'*64))
    def test_prior_streets_required(self):
        self.reject('EXACT_PRIOR_STREETS',lambda x:x['rows'][0].update(prior_streets=[]))
    def test_prior_amount_required(self):
        self.reject('EXACT_ACTION_FIELDS',lambda x:x['rows'][0]['prior_streets'][0][1].pop('to'))
        self.reject('ILLEGAL_CALL',lambda x:x['rows'][0]['prior_streets'][0][2].update(to=0))
    def test_board_and_positions(self):
        self.reject('PUBLIC_BOARD',lambda x:x['rows'][0]['board'].pop())
        self.reject('POSITIONS_OOP_IP',lambda x:x['rows'][0]['cohort'].update(positions=['BTN','BB']))
        self.reject('PREFLOP_FLOP_STATE_MISMATCH',lambda x:x['rows'][0]['cohort'].update(positions=['SB','BTN']))
    def test_spr_and_chip_state(self):
        self.reject('SPR_MISMATCH',lambda x:x['rows'][0]['node'].update(spr_num=178))
        self.reject('NODE_STATE',lambda x:x['rows'][0]['node'].pop('spr_den'))
        self.reject('NODE_CHIP_MISMATCH',lambda x:x['rows'][0]['node'].update(pot=36))
        self.reject('PREFLOP_FLOP_STATE_MISMATCH',lambda x:x['rows'][0]['flop_state'].update(remaining=[196,195]))
    def test_n_and_action_counts(self):
        self.reject('ACTION_COUNT_CONSERVATION',lambda x:x['rows'][0]['counts'].update(f=239))
        self.reject('N_GATE',lambda x:x['rows'][0].update(n=499,counts={'f':200,'c':299,'r:24':0}))
        self.reject('N_GATE',lambda x:x['rows'][0].update(n=601))
    def test_menu_legality(self):
        self.reject('ILLEGAL_CHECK',lambda x:x['rows'][0]['node'].update(menu=['x','f','c']))
        self.reject('ILLEGAL_RAISE',lambda x:x['rows'][0]['node'].update(menu=['f','c','r:13']))
        self.reject('INCOMPLETE_PASSIVE_MENU',lambda x:x['rows'][0]['node'].update(menu=['c','r:24']))
    def test_cohort(self):
        self.reject('UNSUPPORTED_COHORT',lambda x:x['rows'][0]['cohort'].update(stake='NL5'))
        self.reject('PREFLOP_FAMILY_MISMATCH',lambda x:x['rows'][0]['cohort'].update(family='3BP'))
    def test_showdown_combo_rejected(self):
        def combo(x,sampling,values):
            x['source']['sampling']=sampling
            x['rows'][0].update(mode='EXACT_PRIVATE_COMBO',combo=values)
        self.reject('COMBO_REQUIRES_NON_SHOWDOWN_SAMPLING',lambda x:combo(x,'SHOWDOWN_ONLY',['Ac','As']))
        self.reject('COMBO_REQUIRES_NON_SHOWDOWN_SAMPLING',lambda x:combo(x,'PUBLIC_ACTION_HISTORIES',['Ac','As']))
        self.reject('INVALID_COMBO',lambda x:combo(x,'PRIVATE_HOLECARDS_INDEPENDENT_OF_SHOWDOWN',['2c','Ac']))
        self.assertEqual(self.check(lambda x:combo(x,'PRIVATE_HOLECARDS_INDEPENDENT_OF_SHOWDOWN',['Ac','As']))['status'],'SYNTHETIC_TEST_ONLY')
    def test_duplicate_and_nonfinite_json(self):
        for b,code in [(b'{"a":0,"a":1}','DUPLICATE_JSON_KEY'),(b'{"a":NaN}','NONFINITE_JSON')]:
            with self.assertRaisesRegex(ValueError,code):
                check_manifest(b,digest_bytes(b),SOURCE,True)
        self.reject('DUPLICATE_NODE',lambda x:x['rows'].append(copy.deepcopy(x['rows'][0])))

if __name__=='__main__':unittest.main()
