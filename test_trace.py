import json
import threading
import unittest
from urllib.request import urlopen, Request
from http.server import ThreadingHTTPServer
from engine import simulate
from app import Handler

class TraceTests(unittest.TestCase):
    def test_unchecked_evidence_is_not_used(self):
        self.assertEqual(simulate({'merchant':'harbour'})['action'],'verify')
    def test_business_explanation(self):
        self.assertEqual(simulate({'merchant':'petal','checks':['payments','orders']})['action'],'monitor')
    def test_direct_evidence(self):
        self.assertEqual(simulate({'merchant':'harbour','checks':['route']})['action'],'escalate')
    def test_name_does_not_determine_result(self):
        self.assertEqual(simulate({'merchant':'petal','inputs':{'route':True},'checks':['route']})['action'],'escalate')
        self.assertEqual(simulate({'merchant':'harbour','inputs':{'orders':95,'route':False,'complaint':False},'checks':['payments','orders']})['action'],'monitor')
    def test_mixed_activity(self):
        r=simulate({'merchant':'petal','inputs':{'route':True},'checks':['orders','route']})
        self.assertEqual(r['action'],'escalate')
        self.assertTrue(any('mixed activity' in s for s in r['reasons']))
    def test_response_ladder_uses_distinct_evidence(self):
        result=simulate({'merchant':'harbour','checks':['links','settlement']})
        self.assertEqual(len(result['responses']),5)
        self.assertEqual(result['recommendation']['id'],'limit')
        self.assertTrue(result['responses'][3]['enabled'])
        self.assertFalse(result['responses'][4]['enabled'])
    def test_investigation_output_explains_patterns_and_sources(self):
        result=simulate({'merchant':'harbour','checks':['payments','orders','route','settlement']})
        patterns=result['transaction_patterns']
        self.assertEqual(sum(row['count'] for row in patterns['time_bands']),1000)
        self.assertEqual(sum(row['count'] for row in patterns['amount_mix']),1000)
        self.assertEqual(sum(row['count'] for row in patterns['payer_mix']),1000)
        self.assertTrue(result['records'][0]['payer_ref'])
        self.assertTrue(result['records'][0]['pattern_flags'])
        payment_finding=next(item for item in result['evidence'] if item['check']=='payments')
        self.assertIn('payment processor ledger',payment_finding['name'].lower())
        self.assertTrue(payment_finding['limit'])
        complaint_source=next(source for source in result['sources'] if source['check']=='complaint')
        self.assertFalse(complaint_source['checked'])
        self.assertTrue(result['triage_plan']['actions'])
    def test_api_hides_facts_until_their_source_is_checked(self):
        payment_only=simulate({'merchant':'harbour','checks':['payments']})
        for field in ('orders','complaint','route','shared_links','online','settlement','reply'):
            self.assertNotIn(field,payment_only['values'])
        for field in ('order_ref','fulfilled_order','settlement_destination','declared_account'):
            self.assertNotIn(field,payment_only['records'][0])
        cross_checked=simulate({'merchant':'harbour','checks':['payments','orders','settlement']})
        self.assertIn('orders',cross_checked['values'])
        self.assertIn('order_ref',cross_checked['records'][0])
        self.assertIn('settlement_destination',cross_checked['records'][0])
        self.assertIsNone(payment_only['settlement_destinations'])
        self.assertEqual(len(payment_only['money_map']['sample_transactions']),12)
        self.assertFalse(payment_only['money_map']['settlement_checked'])
        self.assertTrue(all(
            row['settlement_destination'].startswith('ACCT-')
            for row in payment_only['money_map']['sample_transactions']
        ))
        self.assertEqual(len({
            row['settlement_destination']
            for row in payment_only['money_map']['sample_transactions']
        }),4)
        self.assertEqual(len(cross_checked['settlement_destinations']),4)
        self.assertEqual(sum(row['count'] for row in cross_checked['settlement_destinations']),1000)
        self.assertAlmostEqual(sum(row['share'] for row in cross_checked['settlement_destinations']),100,places=1)
        self.assertEqual(cross_checked['settlement_destinations'][0]['account_ref'],'ACCT-OWN-01')
    def test_scenario_values_and_map_status_follow_matching_checks(self):
        result=simulate({
            'merchant':'petal',
            'inputs':{'night':64,'repeat':22,'settlement':34},
            'checks':['payments','settlement'],
        })
        self.assertEqual(result['metrics']['night'],64)
        self.assertEqual(result['money_map']['payer_mix']['repeat'],22)
        self.assertTrue(result['money_map']['payments_checked'])
        self.assertTrue(result['money_map']['settlement_checked'])
        self.assertEqual(result['money_map']['settlement_destinations'][0]['share'],34)
    def test_verified_low_fulfilment_is_a_concern_but_unchecked_is_unknown(self):
        unchecked=simulate({'merchant':'petal'})
        self.assertNotIn('fulfillment',unchecked['risk_sources'])
        low=simulate({'merchant':'petal','inputs':{'orders':15},'checks':['orders']})
        self.assertIn('fulfillment',low['risk_sources'])
        self.assertEqual(low['recommendation']['level'],2)
        self.assertIn('Reconcile them against point-of-sale orders',low['triage_plan']['actions'][1])
    def test_follow_up_action_matches_the_source_checked(self):
        settlement=simulate({'merchant':'petal','inputs':{'settlement':12},'checks':['settlement']})
        self.assertEqual(settlement['recommendation']['id'],'verify')
        self.assertIn('account ownership',settlement['triage_plan']['actions'][1])
        no_reply=simulate({'merchant':'petal','inputs':{'reply':'no_reply'},'checks':['merchant']})
        self.assertEqual(no_reply['recommendation']['id'],'verify')
        self.assertIn('Do not interpret silence',no_reply['triage_plan']['actions'][0])
        self.assertFalse(any('send one focused request' in action.lower() for action in no_reply['triage_plan']['actions']))
        vague=simulate({'merchant':'petal','inputs':{'reply':'vague'},'checks':['merchant']})
        self.assertIn('one focused follow-up',vague['triage_plan']['actions'][0])
        clean=simulate({'merchant':'petal'})
        self.assertEqual(clean['recommendation']['id'],'ask')
    def test_payment_and_fulfilment_concerns_are_counted_separately(self):
        result=simulate({'merchant':'petal','inputs':{'night':50,'orders':15},'checks':['payments','orders']})
        self.assertEqual(set(result['risk_sources']),{'payments','fulfillment'})
        self.assertEqual(result['recommendation']['level'],3)
    def test_direct_evidence_unlocks_analyst_review(self):
        result=simulate({'merchant':'harbour','checks':['route']})
        self.assertEqual(result['recommendation']['id'],'analyst')
        self.assertTrue(result['responses'][4]['enabled'])
        self.assertIn('checkout',result['risk_sources'])
    def test_scenario_changes_recommendation_not_merchant_name(self):
        result=simulate({'merchant':'harbour','inputs':{'orders':95,'route':False,'complaint':False},'checks':['payments','orders']})
        self.assertEqual(result['recommendation']['id'],'monitor')
    def test_strong_links_are_not_overridden_by_fulfilled_orders(self):
        result=simulate({'merchant':'petal','inputs':{'night':50,'orders':95,'shared_links':True,'settlement':10},'checks':['payments','orders','links','settlement']})
        self.assertEqual(result['recommendation']['id'],'limit')
    def test_complaint_needs_verification(self):
        self.assertEqual(simulate({'merchant':'petal','inputs':{'complaint':True},'checks':['payments','orders','complaint']})['action'],'verify')
    def test_budget_and_duplicate_checks(self):
        with self.assertRaises(ValueError):
            simulate({'checks':['payments','orders','complaint','route','links','digital','settlement','merchant']})
        self.assertEqual(simulate({'checks':['route','route']})['spent'],15)
    def test_metric_changes(self):
        self.assertEqual(simulate({'inputs':{'night':43},'checks':['payments']})['metrics']['night'],43)
    def test_invalid_inputs(self):
        for request in [{'inputs':{'night':101}},{'checks':['unknown']},{'merchant':'missing'}]:
            with self.assertRaises(ValueError): simulate(request)
    def test_local_server(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        origin=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(origin) as response:
                page=response.read()
                self.assertIn(b'Petal &amp; Crumb',page)
                self.assertIn(b'Five response levels',page)
                self.assertIn(b'Who paid, and where did the money go?',page)
                self.assertIn(b'Thicker line = larger share',page)
                self.assertIn(b'Sender \xc2\xb7 payer ref',page)
                self.assertIn(b'Receiver \xc2\xb7 merchant',page)
                self.assertIn(b'Next payout destination',page)
                self.assertIn(b'generated account ID',page)
                self.assertIn(b'synthetic sample transactions',page)
                self.assertIn(b'scenario preview',page)
            with urlopen(origin+'/logo.svg') as response:
                self.assertIn(b'<svg',response.read())
            with urlopen(origin+'/logo.png') as response:
                self.assertEqual(response.read()[:8],b'\x89PNG\r\n\x1a\n')
            with urlopen(Request(origin+'/api/review',data=json.dumps({'merchant':'harbour','checks':['route']}).encode(),headers={'Content-Type':'application/json'})) as response:
                self.assertEqual(json.load(response)['action'],'escalate')
        finally:
            server.shutdown();server.server_close();worker.join()

if __name__=='__main__': unittest.main()
